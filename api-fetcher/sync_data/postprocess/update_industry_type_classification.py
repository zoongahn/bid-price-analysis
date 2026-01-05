"""
notice_industry_type 테이블에 classification 정보를 추가하고 업데이트하는 스크립트
notice_industry_type_info 테이블과 JOIN하여 분류 정보를 가져옵니다.
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from common.init_psql import init_psql
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# 스키마 설정
DATA_SCHEMA = "data"
META_SCHEMA = "meta"
NOTICE_INDUSTRY_TYPE_TABLE = f"{DATA_SCHEMA}.notice_industry_type"
INDUSTRY_TYPE_INFO_TABLE = f"{META_SCHEMA}.industry_type_info"


def update_classification_info():
    """
    notice_industry_type 테이블에 classification 컬럼을 추가하고
    notice_industry_type_info와 JOIN하여 데이터를 업데이트
    """
    server = None
    conn = None

    try:
        # PostgreSQL 연결
        logger.info("PostgreSQL 연결 중...")
        server, conn = init_psql()
        cursor = conn.cursor()

        # Step 1: 컬럼이 이미 존재하는지 확인
        logger.info("기존 컬럼 확인 중...")
        cursor.execute(f"""
            SELECT column_name
            FROM information_schema.columns
            WHERE table_schema = '{DATA_SCHEMA}'
            AND table_name = 'notice_industry_type'
            AND column_name IN ('classification_code', 'classification_name')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        logger.info(f"기존 컬럼: {existing_columns}")

        # Step 2: 컬럼 추가 (존재하지 않는 경우)
        if 'classification_code' not in existing_columns:
            logger.info("classification_code 컬럼 추가 중...")
            cursor.execute(f"""
                ALTER TABLE {NOTICE_INDUSTRY_TYPE_TABLE}
                ADD COLUMN classification_code TEXT
            """)
            cursor.execute(f"""
                COMMENT ON COLUMN {NOTICE_INDUSTRY_TYPE_TABLE}.classification_code
                IS '분류코드 (예: 49-건설업, 61-정보통신)'
            """)
            logger.info("classification_code 컬럼 추가 완료")
        else:
            logger.info("classification_code 컬럼이 이미 존재합니다")

        if 'classification_name' not in existing_columns:
            logger.info("classification_name 컬럼 추가 중...")
            cursor.execute(f"""
                ALTER TABLE {NOTICE_INDUSTRY_TYPE_TABLE}
                ADD COLUMN classification_name TEXT
            """)
            cursor.execute(f"""
                COMMENT ON COLUMN {NOTICE_INDUSTRY_TYPE_TABLE}.classification_name
                IS '업종분류명 (예: 건설업, 정보통신)'
            """)
            logger.info("classification_name 컬럼 추가 완료")
        else:
            logger.info("classification_name 컬럼이 이미 존재합니다")

        conn.commit()

        # Step 3: notice_industry_type 테이블의 총 레코드 수 확인
        cursor.execute(f"SELECT COUNT(*) FROM {NOTICE_INDUSTRY_TYPE_TABLE}")
        total_records = cursor.fetchone()[0]
        logger.info(f"notice_industry_type 테이블 총 레코드 수: {total_records:,}")

        # Step 4: lcnslmtnm_code가 NULL이 아닌 레코드 수 확인
        cursor.execute(f"SELECT COUNT(*) FROM {NOTICE_INDUSTRY_TYPE_TABLE} WHERE lcnslmtnm_code IS NOT NULL")
        valid_code_records = cursor.fetchone()[0]
        logger.info(f"lcnslmtnm_code가 NULL이 아닌 레코드 수: {valid_code_records:,}")

        # Step 5: JOIN하여 업데이트
        logger.info("JOIN을 통해 classification 정보 업데이트 중...")
        update_sql = f"""
            UPDATE {NOTICE_INDUSTRY_TYPE_TABLE} nit
            SET
                classification_code = NULLIF(niti.classification_code, 'None'),
                classification_name = NULLIF(niti.classification_name, 'None')
            FROM {INDUSTRY_TYPE_INFO_TABLE} niti
            WHERE nit.lcnslmtnm_code = niti.industry_code
        """

        cursor.execute(update_sql)
        updated_count = cursor.rowcount
        conn.commit()

        logger.info(f"업데이트 완료: {updated_count:,}개 레코드")

        # Step 5-2: 문자열 'None'을 NULL로 변환 (매칭되지 않은 경우 정리)
        logger.info("문자열 'None'을 NULL로 변환 중...")
        cleanup_sql = f"""
            UPDATE {NOTICE_INDUSTRY_TYPE_TABLE}
            SET
                classification_code = NULL,
                classification_name = NULL
            WHERE classification_code = 'None' OR classification_name = 'None'
        """
        cursor.execute(cleanup_sql)
        cleanup_count = cursor.rowcount
        conn.commit()

        if cleanup_count > 0:
            logger.info(f"'None' 문자열 정리 완료: {cleanup_count:,}개 레코드")

        # Step 6: 업데이트 결과 확인
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {NOTICE_INDUSTRY_TYPE_TABLE}
            WHERE classification_code IS NOT NULL
        """)
        updated_records = cursor.fetchone()[0]
        logger.info(f"classification_code가 업데이트된 레코드 수: {updated_records:,}")

        # Step 7: 매칭되지 않은 레코드 확인
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {NOTICE_INDUSTRY_TYPE_TABLE}
            WHERE lcnslmtnm_code IS NOT NULL
            AND classification_code IS NULL
        """)
        unmatched_records = cursor.fetchone()[0]

        if unmatched_records > 0:
            logger.warning(f"매칭되지 않은 레코드 수: {unmatched_records:,}")

            # 매칭되지 않은 코드 전체 확인
            cursor.execute(f"""
                SELECT DISTINCT lcnslmtnm_code, lcnslmtnm_name, COUNT(*) as cnt
                FROM {NOTICE_INDUSTRY_TYPE_TABLE}
                WHERE lcnslmtnm_code IS NOT NULL
                AND classification_code IS NULL
                GROUP BY lcnslmtnm_code, lcnslmtnm_name
                ORDER BY cnt DESC
            """)
            unmatched_samples = cursor.fetchall()
            logger.warning(f"매칭되지 않은 코드 전체 ({len(unmatched_samples)}개):")
            for code, name, cnt in unmatched_samples:
                logger.warning(f"  코드: {code}, 이름: {name}, 건수: {cnt:,}")
        else:
            logger.info("모든 레코드가 성공적으로 매칭되었습니다!")

        # Step 8: 샘플 데이터 확인
        cursor.execute(f"""
            SELECT
                bidntceno,
                lcnslmtnm_code,
                lcnslmtnm_name,
                classification_code,
                classification_name
            FROM {NOTICE_INDUSTRY_TYPE_TABLE}
            WHERE classification_code IS NOT NULL
            LIMIT 5
        """)
        sample_data = cursor.fetchall()

        logger.info("업데이트된 샘플 데이터 (처음 5개):")
        for row in sample_data:
            logger.info(f"  공고번호: {row[0]}, 업종코드: {row[1]}, 업종명: {row[2]}")
            logger.info(f"    → 분류코드: {row[3]}, 분류명: {row[4]}")

        # Step 9: 분류별 통계
        cursor.execute(f"""
            SELECT
                classification_code,
                classification_name,
                COUNT(*) as count
            FROM {NOTICE_INDUSTRY_TYPE_TABLE}
            WHERE classification_code IS NOT NULL
            GROUP BY classification_code, classification_name
            ORDER BY count DESC
            LIMIT 10
        """)
        classification_stats = cursor.fetchall()

        logger.info("분류별 통계 (상위 10개):")
        for code, name, count in classification_stats:
            logger.info(f"  [{code}] {name}: {count:,}건")

        # Step 10: 인덱스 추가 (성능 향상)
        logger.info("인덱스 추가 중...")
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_notice_industry_type_classification
            ON {NOTICE_INDUSTRY_TYPE_TABLE} (classification_code, classification_name)
        """)
        cursor.execute(f"""
            CREATE INDEX IF NOT EXISTS idx_notice_industry_type_lcnslmtnm_code
            ON {NOTICE_INDUSTRY_TYPE_TABLE} (lcnslmtnm_code)
        """)
        conn.commit()
        logger.info("인덱스 추가 완료")

    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise

    finally:
        # 연결 종료
        if conn:
            conn.close()
            logger.info("PostgreSQL 연결 종료")
        if server:
            server.stop()
            logger.info("SSH 터널 종료")


def main():
    """메인 함수"""
    logger.info("=" * 80)
    logger.info("notice_industry_type 테이블에 classification 정보 추가 및 업데이트 시작")
    logger.info("=" * 80)

    update_classification_info()

    logger.info("=" * 80)
    logger.info("스크립트 실행 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
