"""
notice_industry_type 데이터를 재동기화하는 스크립트

1. MongoDB의 is_synced 플래그 제거
2. PostgreSQL 테이블 데이터 삭제
3. 수정된 전처리 로직으로 재동기화
"""
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


def reset_mongodb_flags():
    """MongoDB의 notice_industry_type 관련 is_synced 플래그 제거"""
    logger.info("=" * 80)
    logger.info("Step 1: MongoDB is_synced 플래그 제거")
    logger.info("=" * 80)

    server = None
    client = None

    try:
        server, client = init_mongodb()
        db = client.get_database("gfcon_raw")

        collection_name = "입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회"
        coll = db[collection_name]

        # 현재 is_synced가 있는 문서 수 확인
        synced_count = coll.count_documents({"is_synced": {"$exists": True}})
        logger.info(f"is_synced 플래그가 있는 문서 수: {synced_count:,}건")

        if synced_count == 0:
            logger.info("이미 is_synced 플래그가 없습니다.")
            return

        # is_synced 플래그 제거
        result = coll.update_many(
            {"is_synced": {"$exists": True}},
            {"$unset": {"is_synced": ""}}
        )

        logger.info(f"✅ is_synced 제거 완료: {result.modified_count:,}건")

        # 검증
        remaining = coll.count_documents({"is_synced": {"$exists": True}})
        if remaining == 0:
            logger.info("✅ 모든 is_synced 플래그가 제거되었습니다.")
        else:
            logger.warning(f"⚠️  {remaining:,}건의 is_synced 플래그가 남아있습니다.")

    except Exception as e:
        logger.error(f"MongoDB 플래그 제거 실패: {e}", exc_info=True)
        raise

    finally:
        if client:
            client.close()
            logger.info("MongoDB 연결 종료")
        if server:
            server.stop()
            logger.info("SSH 터널 종료")


def clear_postgresql_data():
    """PostgreSQL notice_industry_type 테이블 데이터 삭제"""
    logger.info("\n" + "=" * 80)
    logger.info("Step 2: PostgreSQL 테이블 데이터 삭제")
    logger.info("=" * 80)

    server = None
    conn = None

    try:
        server, conn = init_psql()
        cursor = conn.cursor()

        # 현재 레코드 수 확인
        cursor.execute("SELECT COUNT(*) FROM notice_industry_type")
        current_count = cursor.fetchone()[0]
        logger.info(f"현재 notice_industry_type 테이블 레코드 수: {current_count:,}건")

        if current_count == 0:
            logger.info("테이블이 이미 비어있습니다.")
            return

        # 데이터 삭제
        cursor.execute("DELETE FROM notice_industry_type")
        conn.commit()

        logger.info(f"✅ 데이터 삭제 완료: {current_count:,}건")

        # 검증
        cursor.execute("SELECT COUNT(*) FROM notice_industry_type")
        remaining_count = cursor.fetchone()[0]

        if remaining_count == 0:
            logger.info("✅ 테이블이 성공적으로 비워졌습니다.")
        else:
            logger.warning(f"⚠️  {remaining_count:,}건의 레코드가 남아있습니다.")

    except Exception as e:
        logger.error(f"PostgreSQL 데이터 삭제 실패: {e}", exc_info=True)
        if conn:
            conn.rollback()
        raise

    finally:
        if conn:
            conn.close()
            logger.info("PostgreSQL 연결 종료")
        if server:
            server.stop()
            logger.info("SSH 터널 종료")


def verify_status():
    """재동기화 전 상태 확인"""
    logger.info("\n" + "=" * 80)
    logger.info("재동기화 준비 상태 확인")
    logger.info("=" * 80)

    # MongoDB 상태 확인
    server_mongo = None
    client = None
    server_psql = None
    conn = None

    try:
        server_mongo, client = init_mongodb()
        db = client.get_database("gfcon_raw")
        coll = db["입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회"]

        total_mongo = coll.count_documents({})
        synced_mongo = coll.count_documents({"is_synced": {"$exists": True}})

        logger.info(f"📊 MongoDB 상태:")
        logger.info(f"   - 총 문서 수: {total_mongo:,}건")
        logger.info(f"   - is_synced 있는 문서: {synced_mongo:,}건")
        logger.info(f"   - 동기화 대상: {total_mongo - synced_mongo:,}건")

        # PostgreSQL 상태 확인
        server_psql, conn = init_psql()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM notice_industry_type")
        total_psql = cursor.fetchone()[0]

        logger.info(f"\n📊 PostgreSQL 상태:")
        logger.info(f"   - notice_industry_type 레코드 수: {total_psql:,}건")

        if synced_mongo == 0 and total_psql == 0:
            logger.info("\n✅ 재동기화 준비 완료!")
            logger.info("   다음 명령으로 동기화를 실행하세요:")
            logger.info("   python3 sync_data/examples/sync_notice_industry_type.py")
        else:
            logger.warning("\n⚠️  재동기화 준비가 완료되지 않았습니다.")
            if synced_mongo > 0:
                logger.warning(f"   - MongoDB에 {synced_mongo:,}건의 is_synced 플래그가 남아있습니다.")
            if total_psql > 0:
                logger.warning(f"   - PostgreSQL에 {total_psql:,}건의 레코드가 남아있습니다.")

    except Exception as e:
        logger.error(f"상태 확인 실패: {e}", exc_info=True)

    finally:
        if client:
            client.close()
        if server_mongo:
            server_mongo.stop()
        if conn:
            conn.close()
        if server_psql:
            server_psql.stop()


def main():
    """메인 함수"""
    logger.info("\n" + "=" * 80)
    logger.info("🚀 notice_industry_type 재동기화 스크립트")
    logger.info("=" * 80)
    logger.info("\n이 스크립트는 다음 작업을 수행합니다:")
    logger.info("1. MongoDB의 is_synced 플래그 제거")
    logger.info("2. PostgreSQL notice_industry_type 테이블 데이터 삭제")
    logger.info("3. 재동기화 준비 상태 확인")
    logger.info("\n⚠️  주의: 이 작업은 되돌릴 수 없습니다!")

    response = input("\n계속하시겠습니까? (yes/no): ")

    if response.lower() not in ["yes", "y"]:
        logger.info("❌ 작업이 취소되었습니다.")
        return

    try:
        # Step 1: MongoDB 플래그 제거
        reset_mongodb_flags()

        # Step 2: PostgreSQL 데이터 삭제
        clear_postgresql_data()

        # Step 3: 상태 확인
        verify_status()

        logger.info("\n" + "=" * 80)
        logger.info("✅ 재동기화 준비 완료!")
        logger.info("=" * 80)

    except Exception as e:
        logger.error(f"\n❌ 작업 중 오류 발생: {e}")
        logger.error("일부 작업이 완료되지 않았을 수 있습니다.")
        sys.exit(1)


if __name__ == "__main__":
    main()
