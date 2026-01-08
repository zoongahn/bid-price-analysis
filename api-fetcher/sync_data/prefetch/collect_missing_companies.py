"""
bid 컬렉션에는 있지만 company 컬렉션에는 없는 사업자등록번호 수집

동기화 전에 실행하여 FK 위반을 방지합니다.

1. bid 동기화 대상 4개 컬렉션에서 distinct bidprccorpbizrno 구하기
2. company 동기화 대상 컬렉션에서 distinct bizno 구하기
3. bid에는 있지만 company에는 없는 사업자등록번호 찾기
4. 해당 사업자등록번호로 조달업체기본정보 API 호출하여 수집
"""
import os
import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from common.init_mongodb import init_mongodb
from fetch_data.src.data_collector import DataCollector
import logging

# 로거 설정
logging.basicConfig(
    level=logging.INFO,
    format='[%(levelname)s] %(asctime)s - %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

# bid 동기화 대상 컬렉션 (4개 카테고리)
BID_COLLECTIONS = [
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사",
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품",
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자",
    "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역",
]

# company 동기화 대상 컬렉션
COMPANY_COLLECTION = "사용자정보서비스.조달업체기본정보"


def get_bid_bizno_set(mongo_db) -> set:
    """
    bid 동기화 대상 4개 컬렉션에서 distinct bidprccorpbizrno 구하기
    (미동기화 문서만 대상)
    """
    all_bizno = set()

    for coll_name in BID_COLLECTIONS:
        logger.info(f"  - {coll_name} 조회 중...")
        collection = mongo_db[coll_name]

        # 미동기화 문서에서만 distinct 추출
        bizno_list = collection.distinct(
            "bidprcCorpBizrno",  # 소문자 p
            {"is_synced": {"$ne": True}}
        )

        # 빈 값 제외
        valid_bizno = {b for b in bizno_list if b and b.strip()}
        logger.info(f"    → {len(valid_bizno):,}개 사업자등록번호")
        all_bizno.update(valid_bizno)

    return all_bizno


def get_company_bizno_set(mongo_db) -> set:
    """
    company 동기화 대상 컬렉션에서 distinct bizno 구하기
    """
    logger.info(f"  - {COMPANY_COLLECTION} 조회 중...")
    collection = mongo_db[COMPANY_COLLECTION]

    # 전체 문서에서 distinct 추출 (이미 수집된 것 포함)
    bizno_list = collection.distinct("bizno")

    # 빈 값 제외
    valid_bizno = {b for b in bizno_list if b and b.strip()}
    logger.info(f"    → {len(valid_bizno):,}개 사업자등록번호")

    return valid_bizno


def collect_missing_companies(dry_run: bool = False) -> int:
    """
    누락된 사업자등록번호의 업체 정보 수집

    Args:
        dry_run: True면 수집하지 않고 개수만 확인

    Returns:
        수집된 (또는 수집 대상) 사업자등록번호 개수
    """
    server = None

    try:
        logger.info("=" * 80)
        logger.info("누락된 사업자등록번호 업체 정보 수집")
        logger.info("=" * 80)

        # MongoDB 연결
        logger.info("MongoDB 연결 중...")
        server, client = init_mongodb()
        mongo_db = client.get_database("gfcon_raw")

        # Step 1: bid 컬렉션에서 bizno 추출
        logger.info("\n[Step 1] bid 컬렉션에서 사업자등록번호 추출")
        bid_bizno_set = get_bid_bizno_set(mongo_db)
        logger.info(f"  → bid 컬렉션 총: {len(bid_bizno_set):,}개")

        # Step 2: company 컬렉션에서 bizno 추출
        logger.info("\n[Step 2] company 컬렉션에서 사업자등록번호 추출")
        company_bizno_set = get_company_bizno_set(mongo_db)
        logger.info(f"  → company 컬렉션 총: {len(company_bizno_set):,}개")

        # Step 3: 차집합 구하기
        logger.info("\n[Step 3] 누락된 사업자등록번호 계산")
        missing_bizno = bid_bizno_set - company_bizno_set
        logger.info(f"  → 누락된 사업자등록번호: {len(missing_bizno):,}개")

        if not missing_bizno:
            logger.info("\n✅ 누락된 사업자등록번호가 없습니다.")
            return 0

        # 샘플 출력
        sample = list(missing_bizno)[:10]
        logger.info(f"  → 샘플 (최대 10개): {sample}")

        if dry_run:
            logger.info(f"\n[Dry Run] 수집하지 않고 종료합니다.")
            return len(missing_bizno)

        # Step 4: 누락된 업체 정보 수집
        logger.info(f"\n[Step 4] 누락된 업체 정보 수집 ({len(missing_bizno):,}개)")

        # DataCollector 생성 (조달업체기본정보 API)
        collector = DataCollector(
            service_name="사용자정보서비스",
            operation_number=2,  # 조달업체 기본정보
        )

        # 사업자등록번호 리스트로 변환
        missing_bizno_list = list(missing_bizno)

        # 수집 실행
        collector.collect_company_by_bizno(missing_bizno_list)

        logger.info(f"\n✅ 누락된 업체 정보 수집 완료: {len(missing_bizno_list):,}개")

        return len(missing_bizno_list)

    except Exception as e:
        logger.error(f"오류 발생: {e}", exc_info=True)
        raise

    finally:
        if server:
            server.stop()


def main():
    """메인 함수"""
    import argparse

    parser = argparse.ArgumentParser(description="누락된 사업자등록번호 업체 정보 수집")
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="수집하지 않고 개수만 확인"
    )
    args = parser.parse_args()

    collect_missing_companies(dry_run=args.dry_run)


if __name__ == "__main__":
    main()
