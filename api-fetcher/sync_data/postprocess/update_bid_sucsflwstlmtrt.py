"""
bid 테이블의 sucsflwstlmtrt(낙찰하한율) 컬럼 후처리 UPDATE

bid.sucsflwstlmtrt가 NULL인 경우, notice.sucsfbidlwltrate 값으로 채움

참조:
    - notice.sucsfbidlwltrate: 낙찰하한율 (공고 단위)
    - bid.sucsflwstlmtrt: 낙찰하한율 (투찰 단위, API에서 수집)

※ 주의: bid_rate 계산 전에 실행해야 함 (bid_rate는 sucsflwstlmtrt 필요)
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


def update_bid_sucsflwstlmtrt(schema: str = None):
    """
    bid 테이블의 sucsflwstlmtrt 컬럼 UPDATE (notice.sucsfbidlwltrate로 채움)

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
                COUNT(sucsflwstlmtrt) as has_value,
                COUNT(*) FILTER (WHERE sucsflwstlmtrt IS NULL) as null_count
            FROM {schema}.bid
        """)
        stats = cursor.fetchone()
        logger.info(f"bid 테이블 현황: 총 {stats[0]:,}건, sucsflwstlmtrt 있음: {stats[1]:,}건, NULL: {stats[2]:,}건")

        if stats[2] == 0:
            logger.info("업데이트할 레코드 없음 (모든 sucsflwstlmtrt가 이미 채워져 있음)")
            return 0

        # Step 2: notice.sucsfbidlwltrate로 채우기
        logger.info("sucsflwstlmtrt 업데이트 중 (notice.sucsfbidlwltrate에서 복사)...")
        update_sql = f"""
            UPDATE {schema}.bid b
            SET sucsflwstlmtrt = n.sucsfbidlwltrate
            FROM {schema}.notice n
            WHERE b.bidntceno = n.bidntceno
              AND b.bidntceord = n.bidntceord
              AND b.sucsflwstlmtrt IS NULL
              AND n.sucsfbidlwltrate IS NOT NULL
              AND n.sucsfbidlwltrate != 0
        """
        cursor.execute(update_sql)
        updated_count = cursor.rowcount
        logger.info(f"sucsflwstlmtrt 업데이트: {updated_count:,}건")

        conn.commit()

        # Step 3: 결과 확인
        cursor.execute(f"""
            SELECT
                COUNT(*) as total,
                COUNT(sucsflwstlmtrt) as has_value,
                COUNT(*) FILTER (WHERE sucsflwstlmtrt IS NULL) as null_count
            FROM {schema}.bid
        """)
        result = cursor.fetchone()
        logger.info(f"업데이트 완료:")
        logger.info(f"  - 총 레코드: {result[0]:,}건")
        logger.info(f"  - sucsflwstlmtrt 있음: {result[1]:,}건")
        logger.info(f"  - sucsflwstlmtrt NULL: {result[2]:,}건")

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
    logger.info("bid 테이블 sucsflwstlmtrt 후처리 시작")
    logger.info("=" * 80)

    update_bid_sucsflwstlmtrt()

    logger.info("=" * 80)
    logger.info("스크립트 실행 완료!")
    logger.info("=" * 80)


if __name__ == "__main__":
    main()
