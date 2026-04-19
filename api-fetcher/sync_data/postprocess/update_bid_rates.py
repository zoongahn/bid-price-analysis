"""
bid 테이블의 bid_rate, bid_rate_diff 컬럼 후처리 UPDATE

bid_rate: 사정률 기준 투찰률
bid_rate_diff: 사정률 기준 투찰률 차이 (bid_rate - 100)

계산 공식:
    bid_rate = trunc((((bidprcamt - a_value) / (sucsflwstlmtrt / 100) + a_value) / bssamt) * 100, 5)
    bid_rate_diff = bid_rate - 100

참조:
    - notice.a_value: A값 (GENERATED 컬럼)
    - notice.bssamt: 기초금액
    - bid.sucsflwstlmtrt: 낙찰하한율
    - bid.bidprcamt: 입찰금액
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


def update_bid_rates(schema: str = None):
    """
    bid 테이블의 bid_rate, bid_rate_diff 컬럼 UPDATE

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
                COUNT(bid_rate) as has_bid_rate,
                COUNT(*) FILTER (WHERE bid_rate IS NULL) as null_bid_rate
            FROM {schema}.bid
        """)
        stats = cursor.fetchone()
        logger.info(f"bid 테이블 현황: 총 {stats[0]:,}건, bid_rate 있음: {stats[1]:,}건, NULL: {stats[2]:,}건")

        # Step 2: bid_rate 계산 UPDATE
        logger.info("bid_rate 계산 중...")
        update_bid_rate_sql = f"""
            UPDATE {schema}.bid b
            SET bid_rate = CASE
                WHEN (n.bssamt IS NULL OR n.bssamt = 0
                      OR b.sucsflwstlmtrt IS NULL OR b.sucsflwstlmtrt = 0)
                THEN NULL
                ELSE trunc(
                    (((b.bidprcamt - COALESCE(n.a_value, 0)) / (b.sucsflwstlmtrt / 100)
                      + COALESCE(n.a_value, 0)) / n.bssamt) * 100,
                    5
                )
            END
            FROM {schema}.notice n
            WHERE b.bidntceno = n.bidntceno
              AND b.bidntceord = n.bidntceord
              AND b.bid_rate IS NULL
        """
        cursor.execute(update_bid_rate_sql)
        updated_bid_rate = cursor.rowcount
        logger.info(f"bid_rate 업데이트: {updated_bid_rate:,}건")

        # Step 3: bid_rate_diff 계산 UPDATE
        logger.info("bid_rate_diff 계산 중...")
        update_bid_rate_diff_sql = f"""
            UPDATE {schema}.bid
            SET bid_rate_diff = bid_rate - 100
            WHERE bid_rate IS NOT NULL
              AND bid_rate_diff IS NULL
        """
        cursor.execute(update_bid_rate_diff_sql)
        updated_bid_rate_diff = cursor.rowcount
        logger.info(f"bid_rate_diff 업데이트: {updated_bid_rate_diff:,}건")

        conn.commit()

        # Step 4: 결과 확인
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(bid_rate) as has_bid_rate,
                COUNT(bid_rate_diff) as has_bid_rate_diff,
                AVG(bid_rate) as avg_bid_rate,
                MIN(bid_rate) as min_bid_rate,
                MAX(bid_rate) as max_bid_rate
            FROM {schema}.bid
        """)
        result = cursor.fetchone()
        logger.info(f"업데이트 완료:")
        logger.info(f"  - 총 레코드: {result[0]:,}건")
        logger.info(f"  - bid_rate 계산됨: {result[1]:,}건")
        logger.info(f"  - bid_rate_diff 계산됨: {result[2]:,}건")
        if result[3]:
            logger.info(f"  - bid_rate 평균: {result[3]:.5f}")
            logger.info(f"  - bid_rate 범위: {result[4]:.5f} ~ {result[5]:.5f}")

        # Step 5: 샘플 데이터 출력
        cursor.execute(f"""
            SELECT b.bidntceno, b.bidntceord, b.bidprcamt, n.bssamt, b.sucsflwstlmtrt, b.bid_rate, b.bid_rate_diff
            FROM {schema}.bid b
            JOIN {schema}.notice n ON b.bidntceno = n.bidntceno AND b.bidntceord = n.bidntceord
            WHERE b.bid_rate IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 5
        """)
        samples = cursor.fetchall()
        logger.info("샘플 데이터 (랜덤 5건):")
        for row in samples:
            logger.info(f"  공고: {row[0]}-{row[1]}, 입찰금액: {row[2]:,}, "
                       f"기초금액: {row[3]:,}, 하한율: {row[4]}, "
                       f"bid_rate: {row[5]:.5f}, diff: {row[6]:.5f}")

        return updated_bid_rate, updated_bid_rate_diff

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
    logger.info("bid 테이블 bid_rate, bid_rate_diff 후처리 시작")
    logger.info("=" * 80)

    update_bid_rates()

    logger.info("=" * 80)
    logger.info("스크립트 실행 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
