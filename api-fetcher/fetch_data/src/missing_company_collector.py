"""
bid 수집 후 누락된 company 증분 수집

data_collection_dag에서 bid 수집 완료 후 호출됩니다.
bid 컬렉션에 있지만 company 컬렉션에 없는 사업자등록번호를 찾아 API로 수집합니다.
"""
import logging
from typing import Set

from common.init_mongodb import init_mongodb
from fetch_data.src.data_collector import DataCollector

# 로거 설정
logger = logging.getLogger(__name__)

# bid 컬렉션명 (4개 카테고리)
BID_COLLECTIONS = [
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사",
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품",
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자",
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역",
]
COMPANY_COLLECTION = "사용자정보서비스.조달업체기본정보"


def _get_company_bizno_set(company_coll) -> Set[str]:
    """
    company 컬렉션에서 모든 bizno를 aggregate로 조회

    MongoDB distinct 명령은 16MB 제한이 있어 aggregate 사용
    """
    pipeline = [{"$group": {"_id": "$bizno"}}]
    return {
        doc["_id"]
        for doc in company_coll.aggregate(pipeline, allowDiskUse=True)
        if doc["_id"]
    }


def collect_missing_companies() -> int:
    """
    bid 컬렉션에 있지만 company 컬렉션에 없는 사업자등록번호 수집

    Returns:
        수집된 사업자등록번호 개수
    """
    server = None

    try:
        logger.info("=" * 60)
        logger.info("[증분수집] 누락 company 수집 시작")
        logger.info("=" * 60)

        # MongoDB 연결
        server, client = init_mongodb()
        mongo_db = client.get_database("gfcon_raw")

        # bid 컬렉션에서 미동기화 문서의 bizno 추출
        bid_bizno_set: Set[str] = set()
        for coll_name in BID_COLLECTIONS:
            collection = mongo_db[coll_name]
            bizno_list = collection.distinct(
                "bidprcCorpBizrno",
                {"is_synced": {"$ne": True}}
            )
            valid_bizno = {b for b in bizno_list if b and b.strip()}
            bid_bizno_set.update(valid_bizno)
            logger.info(f"  - {coll_name.split('.')[-1]}: {len(valid_bizno):,}개")

        logger.info(f"  → bid 총 bizno: {len(bid_bizno_set):,}개")

        if not bid_bizno_set:
            logger.info("[증분수집] 수집할 bizno 없음")
            return 0

        # company 컬렉션에서 기존 bizno 추출 (aggregate 사용 - 16MB 제한 우회)
        company_coll = mongo_db[COMPANY_COLLECTION]
        company_bizno_set_before = _get_company_bizno_set(company_coll)
        logger.info(f"  → company 기존 bizno: {len(company_bizno_set_before):,}개")

        # 누락된 bizno 계산 (수집 전)
        missing_bizno_before = bid_bizno_set - company_bizno_set_before
        logger.info(f"  → 누락된 bizno (before): {len(missing_bizno_before):,}개")

        if not missing_bizno_before:
            logger.info("[증분수집] 누락된 bizno 없음")
            return 0

        # 샘플 출력
        sample = list(missing_bizno_before)[:10]
        logger.info(f"  → 샘플 (최대 10개): {sample}")

        # 기존 MongoDB 연결 종료 (DataCollector가 자체 연결 생성)
        if client:
            client.close()
            logger.info("  → MongoDB 클라이언트 종료")
        if server:
            server.stop()
            server = None
            logger.info("  → MongoDB SSH 터널 종료")

        # 누락된 bizno로 company API 수집
        logger.info("-" * 60)
        logger.info(f"[증분수집] API 수집 시작... ({len(missing_bizno_before)}개)")
        collector = DataCollector(
            service_name="사용자정보서비스",
            operation_number=2,  # 조달업체기본정보
        )
        collector.collect_company_by_bizno(list(missing_bizno_before))
        logger.info("[증분수집] API 수집 완료")
        logger.info("-" * 60)

        # 수집 후 누락 bizno 재계산을 위해 MongoDB 재연결
        server, client = init_mongodb()
        mongo_db = client.get_database("gfcon_raw")
        company_coll = mongo_db[COMPANY_COLLECTION]

        # 수집 후 누락 bizno 재계산 (before/after 비교)
        company_bizno_set_after = _get_company_bizno_set(company_coll)
        missing_bizno_after = bid_bizno_set - company_bizno_set_after

        collected_count = len(missing_bizno_before) - len(missing_bizno_after)
        still_missing_count = len(missing_bizno_after)

        logger.info("=" * 60)
        logger.info("[증분수집] 결과 요약")
        logger.info("=" * 60)
        logger.info(f"  - 누락 bizno (before): {len(missing_bizno_before):,}개")
        logger.info(f"  - 누락 bizno (after):  {still_missing_count:,}개")
        logger.info(f"  - 수집 성공:           {collected_count:,}개")
        logger.info(f"  - 수집 실패 (API 미조회): {still_missing_count:,}개")

        if still_missing_count > 0:
            still_missing_sample = list(missing_bizno_after)[:10]
            logger.info(f"  → 미조회 샘플: {still_missing_sample}")

        return collected_count

    except Exception as e:
        logger.error(f"[증분수집] 오류 발생: {e}", exc_info=True)
        raise

    finally:
        if server:
            server.stop()
