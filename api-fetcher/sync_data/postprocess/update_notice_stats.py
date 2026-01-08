"""
notice 테이블의 bid_count, answer_rate, min_winning_price 컬럼 후처리 UPDATE

bid_count: 공고번호 기준 참여업체수
answer_rate: 사정률 (예정가격 / 기초금액 * 100)
min_winning_price: 낙찰하한가

계산 공식:
    bid_count = (SELECT COUNT(*) FROM bid WHERE bidntceno, bidntceord 일치)
    answer_rate = floor_5dp((plnprc / bssamt) * 100)  -- reserve_price_range 테이블 참조
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
    notice 테이블의 bid_count, answer_rate, min_winning_price 컬럼 UPDATE

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
                COUNT(bid_count) as has_bid_count,
                COUNT(answer_rate) as has_answer_rate
            FROM {schema}.notice
        """)
        stats = cursor.fetchone()
        logger.info(f"notice 테이블 현황: 총 {stats[0]:,}건")
        logger.info(f"  - bid_count 있음: {stats[1]:,}건, answer_rate 있음: {stats[2]:,}건")

        # Step 2: bid_count 계산 UPDATE
        logger.info("bid_count 계산 중...")
        update_bid_count_sql = f"""
            UPDATE {schema}.notice n
            SET bid_count = (
                SELECT COUNT(*)
                FROM {schema}.bid b
                WHERE b.bidntceno = n.bidntceno
                  AND b.bidntceord = n.bidntceord
            )
        """
        cursor.execute(update_bid_count_sql)
        updated_bid_count = cursor.rowcount
        logger.info(f"bid_count 업데이트: {updated_bid_count:,}건")

        # Step 3: answer_rate 계산 UPDATE (floor_5dp 함수 사용)
        logger.info("answer_rate 계산 중...")

        # floor_5dp 함수 존재 여부 확인
        cursor.execute("""
            SELECT EXISTS (
                SELECT 1 FROM pg_proc
                WHERE proname = 'floor_5dp'
            )
        """)
        has_floor_5dp = cursor.fetchone()[0]

        if has_floor_5dp:
            update_answer_rate_sql = f"""
                UPDATE {schema}.notice n
                SET answer_rate = (
                    SELECT floor_5dp((r.plnprc / NULLIF(r.bssamt, 0)) * 100)
                    FROM {schema}.reserve_price_range r
                    WHERE r.bidntceno = n.bidntceno
                      AND r.bidntceord = n.bidntceord
                    LIMIT 1
                )
            """
        else:
            # floor_5dp 함수가 없으면 일반 FLOOR 사용
            logger.warning("floor_5dp 함수가 없습니다. 일반 FLOOR 사용")
            update_answer_rate_sql = f"""
                UPDATE {schema}.notice n
                SET answer_rate = (
                    SELECT FLOOR((r.plnprc / NULLIF(r.bssamt, 0)) * 100 * 100000) / 100000
                    FROM {schema}.reserve_price_range r
                    WHERE r.bidntceno = n.bidntceno
                      AND r.bidntceord = n.bidntceord
                    LIMIT 1
                )
            """

        cursor.execute(update_answer_rate_sql)
        updated_answer_rate = cursor.rowcount
        logger.info(f"answer_rate 업데이트: {updated_answer_rate:,}건")

        # Step 4: min_winning_price 계산 UPDATE
        # 낙찰하한가 = (예정가격 - A값) * (낙찰하한율 / 100) + A값
        # bssamtpurcnstcst가 있는 경우 GREATEST(위 값, bssamtpurcnstcst * answer_rate / 100 * 0.98)
        logger.info("min_winning_price 계산 중...")

        update_min_winning_price_sql = f"""
            UPDATE {schema}.notice n
            SET min_winning_price = (
                SELECT
                    CASE
                        WHEN n.bssamtpurcnstcst IS NULL THEN
                            -- bssamtpurcnstcst가 NULL인 경우
                            (r.plnprc - COALESCE(n.a_value, 0)) * (COALESCE(n.sucsfbidlwltrate, 87.745) / 100) + COALESCE(n.a_value, 0)
                        ELSE
                            -- bssamtpurcnstcst가 존재하는 경우: 두 값 중 큰 값
                            GREATEST(
                                (r.plnprc - COALESCE(n.a_value, 0)) * (COALESCE(n.sucsfbidlwltrate, 87.745) / 100) + COALESCE(n.a_value, 0),
                                n.bssamtpurcnstcst * (COALESCE(n.answer_rate, 100) / 100) * 0.98
                            )
                    END
                FROM {schema}.reserve_price_range r
                WHERE r.bidntceno = n.bidntceno
                  AND r.bidntceord = n.bidntceord
                LIMIT 1
            )
            WHERE n.sucsfbidlwltrate IS NOT NULL
        """
        cursor.execute(update_min_winning_price_sql)
        updated_min_winning_price = cursor.rowcount
        logger.info(f"min_winning_price 업데이트: {updated_min_winning_price:,}건")

        conn.commit()

        # Step 5: 결과 확인
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(bid_count) as has_bid_count,
                COUNT(answer_rate) as has_answer_rate,
                COUNT(min_winning_price) as has_min_winning_price,
                AVG(bid_count) FILTER (WHERE bid_count > 0) as avg_bid_count,
                MAX(bid_count) as max_bid_count,
                AVG(answer_rate) as avg_answer_rate,
                MIN(answer_rate) as min_answer_rate,
                MAX(answer_rate) as max_answer_rate,
                AVG(min_winning_price) as avg_min_winning_price,
                MIN(min_winning_price) as min_min_winning_price,
                MAX(min_winning_price) as max_min_winning_price
            FROM {schema}.notice
        """)
        result = cursor.fetchone()
        logger.info(f"업데이트 완료:")
        logger.info(f"  - 총 공고: {result[0]:,}건")
        logger.info(f"  - bid_count 계산됨: {result[1]:,}건")
        logger.info(f"  - answer_rate 계산됨: {result[2]:,}건")
        logger.info(f"  - min_winning_price 계산됨: {result[3]:,}건")
        if result[4]:
            logger.info(f"  - 평균 참여업체수: {result[4]:.2f}개")
        if result[5]:
            logger.info(f"  - 최대 참여업체수: {result[5]:,}개")
        if result[6]:
            logger.info(f"  - 평균 사정률: {result[6]:.5f}")
            logger.info(f"  - 사정률 범위: {result[7]:.5f} ~ {result[8]:.5f}")
        if result[9]:
            logger.info(f"  - 평균 낙찰하한가: {result[9]:,.0f}원")
            logger.info(f"  - 낙찰하한가 범위: {result[10]:,.0f} ~ {result[11]:,.0f}원")

        # Step 6: 참여업체수 분포 확인
        cursor.execute(f"""
            SELECT
                CASE
                    WHEN bid_count = 0 THEN '0'
                    WHEN bid_count BETWEEN 1 AND 5 THEN '1-5'
                    WHEN bid_count BETWEEN 6 AND 10 THEN '6-10'
                    WHEN bid_count BETWEEN 11 AND 20 THEN '11-20'
                    WHEN bid_count BETWEEN 21 AND 50 THEN '21-50'
                    ELSE '50+'
                END as range,
                COUNT(*) as count
            FROM {schema}.notice
            WHERE bid_count IS NOT NULL
            GROUP BY 1
            ORDER BY MIN(bid_count)
        """)
        distribution = cursor.fetchall()
        logger.info("참여업체수 분포:")
        for range_name, count in distribution:
            logger.info(f"  - {range_name}개: {count:,}건")

        return updated_bid_count, updated_answer_rate, updated_min_winning_price

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
    logger.info("notice 테이블 bid_count, answer_rate, min_winning_price 후처리 시작")
    logger.info("=" * 80)

    update_notice_stats()

    logger.info("=" * 80)
    logger.info("스크립트 실행 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
