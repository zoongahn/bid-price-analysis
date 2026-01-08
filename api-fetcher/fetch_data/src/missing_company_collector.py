"""
bid 수집 후 누락된 company 증분 수집

data_collection_dag에서 bid 수집 완료 후 호출됩니다.
bid 컬렉션에 있지만 company 컬렉션에 없는 사업자등록번호를 찾아 API로 수집합니다.
"""
import logging
from typing import Set, List

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

        # company 컬렉션에서 기존 bizno 추출
        company_coll = mongo_db[COMPANY_COLLECTION]
        company_bizno_set = set(company_coll.distinct("bizno"))
        logger.info(f"  → company 기존 bizno: {len(company_bizno_set):,}개")

        # 누락된 bizno 계산
        missing_bizno = bid_bizno_set - company_bizno_set
        logger.info(f"  → 누락된 bizno: {len(missing_bizno):,}개")

        if not missing_bizno:
            logger.info("[증분수집] 누락된 bizno 없음")
            return 0

        # 샘플 출력
        sample = list(missing_bizno)[:10]
        logger.info(f"  → 샘플 (최대 10개): {sample}")

        # 누락된 bizno로 company API 수집
        collector = DataCollector(
            service_name="사용자정보서비스",
            operation_number=2,  # 조달업체기본정보
        )
        collector.collect_company_by_bizno(list(missing_bizno))

        logger.info(f"[증분수집] 누락 company 수집 완료: {len(missing_bizno):,}개")
        return len(missing_bizno)

    except Exception as e:
        logger.error(f"[증분수집] 오류 발생: {e}", exc_info=True)
        raise

    finally:
        if server:
            server.stop()
