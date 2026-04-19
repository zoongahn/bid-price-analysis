"""
notice 테이블의 winner_bid_rate 컬럼 후처리 UPDATE

winner_bid_rate: 1등 낙찰업체의 사정률 (bid 테이블의 bid_rate)

계산 공식:
    winner_bid_rate = (SELECT bid_rate FROM bid WHERE opengRank = 1)

참조:
    - bid.opengRank: 개찰순위 (1등 = 1)
    - bid.bid_rate: 사정률 기준 투찰률 (후처리 계산됨)

※ 주의: bid 테이블의 bid_rate가 먼저 계산되어 있어야 함 (update_bid_rates.py 실행 후)
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


def update_winner_bid_rate(schema: str = None):
    """
    notice 테이블의 winner_bid_rate 컬럼 UPDATE

    Args:
        schema: PostgreSQL 스키마명 (기본값: 환경변수 또는 'data')

    Returns:
        int: 업데이트된 레코드 수
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
                COUNT(winner_bid_rate) as has_winner_bid_rate,
                COUNT(*) FILTER (WHERE winner_bid_rate IS NULL) as null_winner_bid_rate
            FROM {schema}.notice
        """)
        stats = cursor.fetchone()
        logger.info(f"notice 테이블 현황: 총 {stats[0]:,}건, winner_bid_rate 있음: {stats[1]:,}건, NULL: {stats[2]:,}건")

        # Step 2: bid 테이블에서 1등 낙찰업체 bid_rate 확인
        cursor.execute(f"""
            SELECT COUNT(*)
            FROM {schema}.bid
            WHERE opengRank = 1 AND bid_rate IS NOT NULL
        """)
        available_winners = cursor.fetchone()[0]
        logger.info(f"bid 테이블에서 1등 낙찰업체 (bid_rate 있음): {available_winners:,}건")

        # Step 3: winner_bid_rate UPDATE
        logger.info("winner_bid_rate 계산 중...")
        update_winner_bid_rate_sql = f"""
            UPDATE {schema}.notice n
            SET winner_bid_rate = (
                SELECT b.bid_rate
                FROM {schema}.bid b
                WHERE b.bidntceno = n.bidntceno
                  AND b.bidntceord = n.bidntceord
                  AND b.opengRank = 1
                LIMIT 1
            )
            WHERE n.winner_bid_rate IS NULL
        """
        cursor.execute(update_winner_bid_rate_sql)
        updated_count = cursor.rowcount
        logger.info(f"winner_bid_rate 업데이트: {updated_count:,}건")

        conn.commit()

        # Step 4: 결과 확인
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(winner_bid_rate) as has_winner_bid_rate,
                AVG(winner_bid_rate) as avg_winner_bid_rate,
                MIN(winner_bid_rate) as min_winner_bid_rate,
                MAX(winner_bid_rate) as max_winner_bid_rate
            FROM {schema}.notice
        """)
        result = cursor.fetchone()
        logger.info(f"업데이트 완료:")
        logger.info(f"  - 총 공고: {result[0]:,}건")
        logger.info(f"  - winner_bid_rate 계산됨: {result[1]:,}건")
        if result[2]:
            logger.info(f"  - 평균 1등 사정률: {result[2]:.5f}")
            logger.info(f"  - 1등 사정률 범위: {result[3]:.5f} ~ {result[4]:.5f}")

        # Step 5: 샘플 데이터 출력
        cursor.execute(f"""
            SELECT
                n.bidntceno,
                n.bidntceord,
                n.winner_bid_rate,
                n.winner_corpnm,
                b.bidprcamt
            FROM {schema}.notice n
            LEFT JOIN {schema}.bid b ON b.bidntceno = n.bidntceno
                AND b.bidntceord = n.bidntceord
                AND b.opengRank = 1
            WHERE n.winner_bid_rate IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 5
        """)
        samples = cursor.fetchall()
        logger.info("샘플 데이터 (랜덤 5건):")
        for row in samples:
            corp_name = row[3][:20] if row[3] else "N/A"
            bid_amt = f"{row[4]:,}" if row[4] else "N/A"
            logger.info(f"  공고: {row[0]}-{row[1]}, 1등 사정률: {row[2]:.5f}, "
                       f"낙찰업체: {corp_name}, 입찰금액: {bid_amt}")

        return updated_count

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
    logger.info("notice 테이블 winner_bid_rate 후처리 시작")
    logger.info("=" * 80)

    update_winner_bid_rate()

    logger.info("=" * 80)
    logger.info("스크립트 실행 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
