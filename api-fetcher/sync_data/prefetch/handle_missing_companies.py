"""
Phase 1: 기존 데이터의 누락된 company 처리

1. bid 테이블의 company FK 해제
2. bid 동기화 실행
3. PostgreSQL에서 누락 bizno 조회 (bid에 있지만 company에 없는)
4. 누락 bizno API 수집 → MongoDB
5. company 동기화 (MongoDB → PostgreSQL)
6. 여전히 없는 bizno → __UNKNOWN__으로 UPDATE
7. company 테이블에 __UNKNOWN__ row 추가
8. FK 제약 다시 활성화
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from common.init_psql import init_psql
from common.init_mongodb import init_mongodb
from fetch_data.src.data_collector import DataCollector
import logging
from typing import List, Set, Tuple, Optional

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 상수
UNKNOWN_BIZNO = "__UNKNOWN__"
UNKNOWN_CORPNM = "조회불가업체"
DEFAULT_BIZNO = "__DEFAULT__"


class MissingCompanyHandler:
    """누락된 company 처리 핸들러"""

    def __init__(self, schema: str = None):
        """
        Args:
            schema: PostgreSQL 스키마명 (기본값: 환경변수 또는 'data')
        """
        self.schema = schema or os.getenv("POSTGRES_SCHEMA", "data")
        self.psql_server = None
        self.psql_conn = None
        self.mongo_server = None
        self.mongo_client = None

    def connect_psql(self):
        """PostgreSQL 연결"""
        if not self.psql_conn:
            logger.info("PostgreSQL 연결 중...")
            self.psql_server, self.psql_conn = init_psql()
        return self.psql_conn

    def connect_mongodb(self):
        """MongoDB 연결"""
        if not self.mongo_client:
            logger.info("MongoDB 연결 중...")
            self.mongo_server, self.mongo_client = init_mongodb()
        return self.mongo_client

    def close_connections(self):
        """모든 연결 종료"""
        if self.psql_conn:
            self.psql_conn.close()
            logger.info("PostgreSQL 연결 종료")
        if self.psql_server:
            self.psql_server.stop()
        if self.mongo_server:
            self.mongo_server.stop()
            logger.info("MongoDB SSH 터널 종료")

    def disable_company_fk(self) -> bool:
        """
        Step 1: bid 테이블의 company FK 제약 해제

        Returns:
            성공 여부
        """
        logger.info(f"[Step 1] bid 테이블의 company FK 제약 해제 ({self.schema} 스키마)")

        conn = self.connect_psql()
        cursor = conn.cursor()

        try:
            # FK 제약 조건 이름 조회
            cursor.execute(f"""
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = '{self.schema}.bid'::regclass
                AND confrelid = '{self.schema}.company'::regclass
                AND contype = 'f'
            """)
            result = cursor.fetchone()

            if not result:
                logger.warning("company FK 제약 조건을 찾을 수 없습니다. 이미 해제되었을 수 있습니다.")
                return True

            fk_name = result[0]
            logger.info(f"  → FK 제약 조건명: {fk_name}")

            # FK 제약 해제
            cursor.execute(f"ALTER TABLE {self.schema}.bid DROP CONSTRAINT {fk_name}")
            conn.commit()

            logger.info(f"  → FK 제약 해제 완료")
            return True

        except Exception as e:
            logger.error(f"FK 해제 실패: {e}")
            conn.rollback()
            return False

    def enable_company_fk(self) -> bool:
        """
        Step 8: bid 테이블의 company FK 제약 활성화

        Returns:
            성공 여부
        """
        logger.info(f"[Step 8] bid 테이블의 company FK 제약 활성화 ({self.schema} 스키마)")

        conn = self.connect_psql()
        cursor = conn.cursor()

        try:
            # 기존 FK 존재 여부 확인
            cursor.execute(f"""
                SELECT conname
                FROM pg_constraint
                WHERE conrelid = '{self.schema}.bid'::regclass
                AND confrelid = '{self.schema}.company'::regclass
                AND contype = 'f'
            """)

            if cursor.fetchone():
                logger.info("  → FK 제약 조건이 이미 존재합니다")
                return True

            # FK 제약 추가
            cursor.execute(f"""
                ALTER TABLE {self.schema}.bid
                ADD CONSTRAINT bid_prcbdrbizno_fkey
                FOREIGN KEY (prcbdrbizno) REFERENCES {self.schema}.company(bizno)
            """)
            conn.commit()

            logger.info(f"  → FK 제약 활성화 완료")
            return True

        except Exception as e:
            logger.error(f"FK 활성화 실패: {e}")
            conn.rollback()
            return False

    def get_missing_bizno_from_psql(self) -> Set[str]:
        """
        Step 3: PostgreSQL에서 누락된 bizno 조회
        bid 테이블에 있지만 company 테이블에 없는 사업자등록번호

        Returns:
            누락된 bizno 집합
        """
        logger.info(f"[Step 3] PostgreSQL에서 누락된 bizno 조회 ({self.schema} 스키마)")

        conn = self.connect_psql()
        cursor = conn.cursor()

        # bid에 있지만 company에 없는 bizno 조회
        # __DEFAULT__와 __UNKNOWN__은 제외
        cursor.execute(f"""
            SELECT DISTINCT b.prcbdrbizno
            FROM {self.schema}.bid b
            LEFT JOIN {self.schema}.company c ON b.prcbdrbizno = c.bizno
            WHERE c.bizno IS NULL
            AND b.prcbdrbizno NOT IN ('{DEFAULT_BIZNO}', '{UNKNOWN_BIZNO}')
            AND b.prcbdrbizno IS NOT NULL
            AND b.prcbdrbizno != ''
            AND b.prcbdrbizno IS NOT NULL
            AND b.prcbdrbizno != ''
        """)

        missing_bizno = {row[0] for row in cursor.fetchall()}
        logger.info(f"  → 누락된 bizno: {len(missing_bizno):,}개")

        if missing_bizno:
            sample = list(missing_bizno)[:10]
            logger.info(f"  → 샘플 (최대 10개): {sample}")

        return missing_bizno

    def collect_companies_by_bizno(self, bizno_list: List[str]) -> int:
        """
        Step 4: 누락된 bizno로 API 수집 → MongoDB

        Args:
            bizno_list: 수집할 사업자등록번호 리스트

        Returns:
            수집된 건수
        """
        if not bizno_list:
            logger.info("[Step 4] 수집할 bizno가 없습니다")
            return 0

        logger.info(f"[Step 4] 누락된 업체 정보 API 수집 ({len(bizno_list):,}개)")

        try:
            # DataCollector 생성 (조달업체기본정보 API)
            collector = DataCollector(
                service_name="사용자정보서비스",
                operation_number=2,  # 조달업체 기본정보
            )

            # 수집 실행
            collector.collect_company_by_bizno(bizno_list)

            logger.info(f"  → API 수집 완료")
            return len(bizno_list)

        except Exception as e:
            logger.error(f"API 수집 실패: {e}", exc_info=True)
            return 0

    def ensure_unknown_company_row(self) -> bool:
        """
        Step 7: company 테이블에 __UNKNOWN__ row 추가

        Returns:
            성공 여부
        """
        logger.info(f"[Step 7] company 테이블에 {UNKNOWN_BIZNO} row 추가")

        conn = self.connect_psql()
        cursor = conn.cursor()

        try:
            # __UNKNOWN__ row 존재 확인
            cursor.execute(f"""
                SELECT bizno FROM {self.schema}.company WHERE bizno = %s
            """, (UNKNOWN_BIZNO,))

            if cursor.fetchone():
                logger.info(f"  → {UNKNOWN_BIZNO} row가 이미 존재합니다")
                return True

            # __UNKNOWN__ row 추가
            cursor.execute(f"""
                INSERT INTO {self.schema}.company (bizno, corpnm)
                VALUES (%s, %s)
            """, (UNKNOWN_BIZNO, UNKNOWN_CORPNM))
            conn.commit()

            logger.info(f"  → {UNKNOWN_BIZNO} row 추가 완료")
            return True

        except Exception as e:
            logger.error(f"__UNKNOWN__ row 추가 실패: {e}")
            conn.rollback()
            return False

    def insert_missing_as_unknown_companies(self) -> int:
        """
        Step 6: 여전히 company에 없는 bizno를 __UNKNOWN__ 업체로 company 테이블에 추가

        API 수집 후에도 없는 bizno (더미/테스트 값)를 company 테이블에
        corpnm='__UNKNOWN__'으로 INSERT합니다.

        Returns:
            추가된 행 수
        """
        logger.info(f"[Step 6] 여전히 누락된 bizno를 company 테이블에 __UNKNOWN__ 업체로 추가")

        conn = self.connect_psql()
        cursor = conn.cursor()

        try:
            # 여전히 company에 없는 bizno 조회
            cursor.execute(f"""
                SELECT DISTINCT b.prcbdrbizno
                FROM {self.schema}.bid b
                LEFT JOIN {self.schema}.company c ON b.prcbdrbizno = c.bizno
                WHERE c.bizno IS NULL
                AND b.prcbdrbizno NOT IN ('{DEFAULT_BIZNO}', '{UNKNOWN_BIZNO}')
            AND b.prcbdrbizno IS NOT NULL
            AND b.prcbdrbizno != ''
                AND b.prcbdrbizno IS NOT NULL
                AND b.prcbdrbizno != ''
            """)
            missing_bizno = [row[0] for row in cursor.fetchall()]

            if not missing_bizno:
                logger.info("  → 누락된 bizno가 없습니다 (모두 수집됨)")
                return 0

            logger.info(f"  → 여전히 누락된 bizno: {len(missing_bizno)}개")
            logger.info(f"  → 누락된 bizno 목록: {missing_bizno}")

            # company 테이블에 __UNKNOWN__ 업체로 INSERT
            inserted_count = 0
            for bizno in missing_bizno:
                cursor.execute(f"""
                    INSERT INTO {self.schema}.company (bizno, corpnm)
                    VALUES (%s, '__UNKNOWN__')
                    ON CONFLICT (bizno) DO NOTHING
                """, (bizno,))
                if cursor.rowcount > 0:
                    inserted_count += 1
                    logger.info(f"  + {bizno} → __UNKNOWN__")

            conn.commit()

            logger.info(f"  → {inserted_count}개 업체를 __UNKNOWN__으로 추가 완료")
            return inserted_count

        except Exception as e:
            logger.error(f"__UNKNOWN__ 업체 추가 실패: {e}")
            conn.rollback()
            return 0

    def update_missing_to_unknown(self) -> int:
        """
        (Legacy) 여전히 company에 없는 bizno를 bid 테이블에서 __UNKNOWN__으로 UPDATE

        Note: 이 방식 대신 insert_missing_as_unknown_companies() 사용 권장

        Returns:
            업데이트된 행 수
        """
        logger.info(f"[Legacy] 여전히 누락된 bizno를 {UNKNOWN_BIZNO}로 UPDATE")

        conn = self.connect_psql()
        cursor = conn.cursor()

        try:
            # 먼저 __UNKNOWN__ row가 존재하는지 확인
            self.ensure_unknown_company_row()

            # 여전히 company에 없는 bizno 개수 확인
            cursor.execute(f"""
                SELECT COUNT(DISTINCT b.prcbdrbizno)
                FROM {self.schema}.bid b
                LEFT JOIN {self.schema}.company c ON b.prcbdrbizno = c.bizno
                WHERE c.bizno IS NULL
                AND b.prcbdrbizno NOT IN ('{DEFAULT_BIZNO}', '{UNKNOWN_BIZNO}')
            AND b.prcbdrbizno IS NOT NULL
            AND b.prcbdrbizno != ''
                AND b.prcbdrbizno IS NOT NULL
                AND b.prcbdrbizno != ''
            """)
            still_missing_count = cursor.fetchone()[0]

            if still_missing_count == 0:
                logger.info("  → 누락된 bizno가 없습니다 (모두 수집됨)")
                return 0

            logger.info(f"  → 여전히 누락된 bizno: {still_missing_count:,}개")

            # __UNKNOWN__으로 UPDATE
            cursor.execute(f"""
                UPDATE {self.schema}.bid b
                SET prcbdrbizno = '{UNKNOWN_BIZNO}'
                FROM (
                    SELECT DISTINCT prcbdrbizno
                    FROM {self.schema}.bid b2
                    LEFT JOIN {self.schema}.company c ON b2.prcbdrbizno = c.bizno
                    WHERE c.bizno IS NULL
                    AND b2.prcbdrbizno NOT IN ('{DEFAULT_BIZNO}', '{UNKNOWN_BIZNO}')
                    AND b2.prcbdrbizno IS NOT NULL
                    AND b2.prcbdrbizno != ''
                ) missing
                WHERE b.prcbdrbizno = missing.prcbdrbizno
            """)
            updated_count = cursor.rowcount
            conn.commit()

            logger.info(f"  → {updated_count:,}개 행을 {UNKNOWN_BIZNO}로 UPDATE 완료")
            return updated_count

        except Exception as e:
            logger.error(f"__UNKNOWN__ UPDATE 실패: {e}")
            conn.rollback()
            return 0

    def get_summary(self) -> dict:
        """현재 상태 요약 조회"""
        conn = self.connect_psql()
        cursor = conn.cursor()

        # bid 테이블 통계
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(DISTINCT prcbdrbizno) as unique_bizno,
                COUNT(*) FILTER (WHERE prcbdrbizno = '{DEFAULT_BIZNO}') as default_count,
                COUNT(*) FILTER (WHERE prcbdrbizno = '{UNKNOWN_BIZNO}') as unknown_count
            FROM {self.schema}.bid
        """)
        bid_stats = cursor.fetchone()

        # company 테이블 통계
        cursor.execute(f"""
            SELECT COUNT(*) FROM {self.schema}.company
        """)
        company_count = cursor.fetchone()[0]

        # 누락된 bizno 개수
        cursor.execute(f"""
            SELECT COUNT(DISTINCT b.prcbdrbizno)
            FROM {self.schema}.bid b
            LEFT JOIN {self.schema}.company c ON b.prcbdrbizno = c.bizno
            WHERE c.bizno IS NULL
            AND b.prcbdrbizno NOT IN ('{DEFAULT_BIZNO}', '{UNKNOWN_BIZNO}')
            AND b.prcbdrbizno IS NOT NULL
            AND b.prcbdrbizno != ''
        """)
        missing_count = cursor.fetchone()[0]

        return {
            "bid_total": bid_stats[0],
            "bid_unique_bizno": bid_stats[1],
            "bid_default_count": bid_stats[2],
            "bid_unknown_count": bid_stats[3],
            "company_count": company_count,
            "missing_bizno_count": missing_count
        }


def run_phase1_after_bid_sync(schema: str = None, dry_run: bool = False) -> dict:
    """
    Phase 1 실행 (bid 동기화 이후 단계)

    Steps:
        3. PostgreSQL에서 누락 bizno 조회
        4. 누락 bizno API 수집 → MongoDB
        5. (별도 실행) company 동기화
        6. 여전히 없는 bizno → __UNKNOWN__으로 UPDATE
        7. company 테이블에 __UNKNOWN__ row 추가
        8. FK 제약 다시 활성화

    Args:
        schema: PostgreSQL 스키마명
        dry_run: True면 조회만 하고 실제 수집/UPDATE 안 함

    Returns:
        실행 결과 딕셔너리
    """
    handler = MissingCompanyHandler(schema=schema)
    result = {
        "missing_bizno_count": 0,
        "collected_count": 0,
        "updated_to_unknown_count": 0,
        "fk_enabled": False,
        "success": False
    }

    try:
        logger.info("=" * 80)
        logger.info("Phase 1: 누락된 company 처리 (bid 동기화 이후)")
        logger.info("=" * 80)

        # Step 3: 누락 bizno 조회
        missing_bizno = handler.get_missing_bizno_from_psql()
        result["missing_bizno_count"] = len(missing_bizno)

        if not missing_bizno:
            logger.info("\n누락된 bizno가 없습니다.")
            result["success"] = True

            # FK 활성화
            handler.enable_company_fk()
            result["fk_enabled"] = True
            return result

        if dry_run:
            logger.info(f"\n[Dry Run] 수집하지 않고 종료합니다.")
            return result

        # Step 4: API 수집
        missing_list = list(missing_bizno)
        collected = handler.collect_companies_by_bizno(missing_list)
        result["collected_count"] = collected

        # Step 5: company 동기화는 별도로 실행해야 함
        logger.info("\n[Step 5] company 동기화는 별도로 실행해야 합니다:")
        logger.info("  → python sync_data/sync/run_sync.py company")

        # Step 6: __UNKNOWN__으로 UPDATE (company 동기화 후 실행)
        # 이 단계는 company 동기화 후에 실행해야 함

        # Step 7: __UNKNOWN__ row 추가
        handler.ensure_unknown_company_row()

        result["success"] = True

        # 요약 출력
        summary = handler.get_summary()
        logger.info("\n" + "=" * 80)
        logger.info("실행 결과 요약")
        logger.info("=" * 80)
        logger.info(f"  - 누락된 bizno: {result['missing_bizno_count']:,}개")
        logger.info(f"  - API 수집 요청: {result['collected_count']:,}개")
        logger.info(f"  - bid 테이블 총 행: {summary['bid_total']:,}개")
        logger.info(f"  - company 테이블 총 행: {summary['company_count']:,}개")

        return result

    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        result["error"] = str(e)
        return result

    finally:
        handler.close_connections()


def finalize_after_company_sync(schema: str = None) -> dict:
    """
    company 동기화 후 마무리 작업

    Steps:
        6. 여전히 없는 bizno → company 테이블에 __UNKNOWN__ 업체로 추가
        8. FK 제약 다시 활성화

    Args:
        schema: PostgreSQL 스키마명

    Returns:
        실행 결과 딕셔너리
    """
    handler = MissingCompanyHandler(schema=schema)
    result = {
        "inserted_unknown_count": 0,
        "fk_enabled": False,
        "success": False
    }

    try:
        logger.info("=" * 80)
        logger.info("Phase 1 마무리: company 동기화 후 처리")
        logger.info("=" * 80)

        # Step 6: 누락된 bizno를 company 테이블에 __UNKNOWN__ 업체로 추가
        inserted = handler.insert_missing_as_unknown_companies()
        result["inserted_unknown_count"] = inserted

        # Step 8: FK 활성화
        handler.enable_company_fk()
        result["fk_enabled"] = True

        result["success"] = True

        # 요약 출력
        summary = handler.get_summary()
        logger.info("\n" + "=" * 80)
        logger.info("최종 결과 요약")
        logger.info("=" * 80)
        logger.info(f"  - __UNKNOWN__ 업체로 추가된 bizno: {result['inserted_unknown_count']}개")
        logger.info(f"  - FK 제약 활성화: {result['fk_enabled']}")
        logger.info(f"  - company 테이블 총 행: {summary['company_count']:,}개")
        logger.info(f"  - 여전히 누락된 bizno: {summary['missing_bizno_count']}개")

        return result

    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        result["error"] = str(e)
        return result

    finally:
        handler.close_connections()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="Phase 1: 누락된 company 처리")
    parser.add_argument(
        "--schema",
        type=str,
        default=None,
        help="PostgreSQL 스키마명 (기본값: 환경변수 POSTGRES_SCHEMA 또는 'data')"
    )
    parser.add_argument(
        "--step",
        type=str,
        choices=["disable-fk", "after-bid-sync", "after-company-sync", "enable-fk", "status"],
        required=True,
        help="실행할 단계"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="조회만 하고 실제 수집/UPDATE 안 함"
    )
    args = parser.parse_args()

    handler = MissingCompanyHandler(schema=args.schema)

    try:
        if args.step == "disable-fk":
            handler.disable_company_fk()

        elif args.step == "after-bid-sync":
            run_phase1_after_bid_sync(schema=args.schema, dry_run=args.dry_run)

        elif args.step == "after-company-sync":
            finalize_after_company_sync(schema=args.schema)

        elif args.step == "enable-fk":
            handler.enable_company_fk()

        elif args.step == "status":
            summary = handler.get_summary()
            logger.info("현재 상태:")
            for key, value in summary.items():
                logger.info(f"  - {key}: {value:,}" if isinstance(value, int) else f"  - {key}: {value}")

    finally:
        handler.close_connections()


if __name__ == "__main__":
    main()
