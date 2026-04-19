"""
notice 테이블의 plnprc(예정가격) 후처리 UPDATE

plnprc가 NULL인 건에 대해 reserve_price_range 테이블에서 가져와 채움.
plnprc가 채워지면 answer_rate, min_winning_price는 GENERATED COLUMN으로 자동 계산됨.

계산 공식 (DB generated column):
    answer_rate = floor_5dp((plnprc / bssamt) * 100)
    min_winning_price = ceil((plnprc - A값) * sucsfbidlwltrate / 100 + A값)
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


def update_notice_stats(schema: str = None):
    """
    notice 테이블의 plnprc(예정가격) UPDATE

    reserve_price_range 테이블에서 plnprc를 가져와 notice.plnprc가 NULL인 건을 채움.
    plnprc가 채워지면 answer_rate, min_winning_price는 generated column으로 자동 계산.

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
                COUNT(plnprc) as has_plnprc,
                COUNT(answer_rate) as has_answer_rate,
                COUNT(min_winning_price) as has_min_winning_price
            FROM {schema}.notice
        """)
        stats = cursor.fetchone()
        logger.info(f"notice 테이블 현황: 총 {stats[0]:,}건")
        logger.info(f"  - plnprc 있음: {stats[1]:,}건 ({stats[1]/stats[0]*100:.1f}%)")
        logger.info(f"  - answer_rate 있음 (자동계산): {stats[2]:,}건")
        logger.info(f"  - min_winning_price 있음 (자동계산): {stats[3]:,}건")

        # Step 2: plnprc가 NULL인 건에 대해 reserve_price_range에서 채우기
        logger.info("plnprc 업데이트 중 (reserve_price_range에서)...")

        update_plnprc_sql = f"""
            UPDATE {schema}.notice n
            SET plnprc = (
                SELECT r.plnprc
                FROM {schema}.reserve_price_range r
                WHERE r.bidntceno = n.bidntceno
                  AND r.bidntceord = n.bidntceord
                  AND r.plnprc IS NOT NULL
                LIMIT 1
            )
            WHERE n.plnprc IS NULL
              AND EXISTS (
                SELECT 1
                FROM {schema}.reserve_price_range r
                WHERE r.bidntceno = n.bidntceno
                  AND r.bidntceord = n.bidntceord
                  AND r.plnprc IS NOT NULL
              )
        """
        cursor.execute(update_plnprc_sql)
        updated_plnprc = cursor.rowcount
        logger.info(f"plnprc 업데이트: {updated_plnprc:,}건")

        conn.commit()

        # Step 3: 결과 확인
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(plnprc) as has_plnprc,
                COUNT(answer_rate) as has_answer_rate,
                COUNT(min_winning_price) as has_min_winning_price
            FROM {schema}.notice
        """)
        result = cursor.fetchone()
        logger.info(f"업데이트 완료:")
        logger.info(f"  - 총 공고: {result[0]:,}건")
        logger.info(f"  - plnprc: {result[1]:,}건 ({result[1]/result[0]*100:.1f}%)")
        logger.info(f"  - answer_rate (자동계산): {result[2]:,}건")
        logger.info(f"  - min_winning_price (자동계산): {result[3]:,}건")

        return updated_plnprc

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
    logger.info("notice 테이블 plnprc 후처리 시작")
    logger.info("=" * 80)

    update_notice_stats()

    logger.info("=" * 80)
    logger.info("스크립트 실행 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
