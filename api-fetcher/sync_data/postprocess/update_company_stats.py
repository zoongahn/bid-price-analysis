"""
company 테이블의 has_bid, bid_count 컬럼 후처리 UPDATE

has_bid: 해당 회사가 입찰에 참여한 이력이 있는지 여부
bid_count: 사업자등록번호 기준 투찰 횟수

계산 공식:
    has_bid = EXISTS (SELECT 1 FROM bid WHERE bidprccorpbizrno = bizno)
    bid_count = (SELECT COUNT(*) FROM bid WHERE bidprccorpbizrno = bizno)
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
DATA_SCHEMA = os.getenv("POSTGRES_SCHEMA", "data")


def update_company_stats(schema: str = None):
    """
    company 테이블의 has_bid, bid_count 컬럼 UPDATE

    Args:
        schema: PostgreSQL 스키마명 (기본값: 환경변수 또는 'data')
    """
    schema = schema or DATA_SCHEMA
    server = None
    conn = None

    try:
        logger.info("PostgreSQL 연결 중...")
        server, conn = init_psql()
        cursor = conn.cursor()

        # Step 1: 현재 상태 확인
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE has_bid = TRUE) as has_bid_true,
                COUNT(*) FILTER (WHERE has_bid = FALSE) as has_bid_false,
                COUNT(*) FILTER (WHERE has_bid IS NULL) as has_bid_null
            FROM {schema}.company
        """)
        stats = cursor.fetchone()
        logger.info(f"company 테이블 현황: 총 {stats[0]:,}건")
        logger.info(f"  - has_bid=TRUE: {stats[1]:,}건, FALSE: {stats[2]:,}건, NULL: {stats[3]:,}건")

        # Step 2: has_bid 계산 UPDATE
        logger.info("has_bid 계산 중...")
        update_has_bid_sql = f"""
            UPDATE {schema}.company c
            SET has_bid = EXISTS (
                SELECT 1 FROM {schema}.bid b
                WHERE b.bidprccorpbizrno = c.bizno
            )
        """
        cursor.execute(update_has_bid_sql)
        updated_has_bid = cursor.rowcount
        logger.info(f"has_bid 업데이트: {updated_has_bid:,}건")

        # Step 3: bid_count 계산 UPDATE
        logger.info("bid_count 계산 중...")
        update_bid_count_sql = f"""
            UPDATE {schema}.company c
            SET bid_count = (
                SELECT COUNT(*)
                FROM {schema}.bid b
                WHERE b.bidprccorpbizrno = c.bizno
            )
        """
        cursor.execute(update_bid_count_sql)
        updated_bid_count = cursor.rowcount
        logger.info(f"bid_count 업데이트: {updated_bid_count:,}건")

        conn.commit()

        # Step 4: 결과 확인
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(*) FILTER (WHERE has_bid = TRUE) as has_bid_true,
                COUNT(*) FILTER (WHERE has_bid = FALSE) as has_bid_false,
                SUM(bid_count) as total_bids,
                AVG(bid_count) FILTER (WHERE bid_count > 0) as avg_bids,
                MAX(bid_count) as max_bids
            FROM {schema}.company
        """)
        result = cursor.fetchone()
        logger.info(f"업데이트 완료:")
        logger.info(f"  - 총 회사: {result[0]:,}개")
        logger.info(f"  - 투찰 이력 있음 (has_bid=TRUE): {result[1]:,}개")
        logger.info(f"  - 투찰 이력 없음 (has_bid=FALSE): {result[2]:,}개")
        logger.info(f"  - 총 투찰 횟수 합계: {result[3]:,}건")
        if result[4]:
            logger.info(f"  - 투찰 회사당 평균 투찰 횟수: {result[4]:.2f}건")
        logger.info(f"  - 최대 투찰 횟수: {result[5]:,}건")

        # Step 5: 상위 투찰 회사 출력
        cursor.execute(f"""
            SELECT bizno, corpnm, bid_count
            FROM {schema}.company
            WHERE bid_count > 0
            ORDER BY bid_count DESC
            LIMIT 10
        """)
        top_companies = cursor.fetchall()
        logger.info("상위 투찰 회사 (TOP 10):")
        for bizno, corpnm, count in top_companies:
            logger.info(f"  - {corpnm} ({bizno}): {count:,}건")

        return updated_has_bid, updated_bid_count

    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()
            logger.info("PostgreSQL 연결 종료")
        if server:
            server.stop()


def main():
    """메인 함수"""
    logger.info("=" * 80)
    logger.info("company 테이블 has_bid, bid_count 후처리 시작")
    logger.info("=" * 80)

    update_company_stats()

    logger.info("=" * 80)
    logger.info("스크립트 실행 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
