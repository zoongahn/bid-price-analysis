"""
국세청 사업자등록 상태조회 API 수집 모듈

MongoDB의 조달업체기본정보 컬렉션에서 사업자등록번호를 조회하여
국세청 API를 통해 상태 정보를 수집합니다.

수집 결과는 MongoDB 별도 컬렉션에 저장되며,
company_syncer에서 조달업체기본정보와 merge하여 PostgreSQL로 동기화됩니다.
"""
import os
import logging
import time
import threading
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드 (Airflow 환경에서도 정상 동작)
project_root = Path(__file__).resolve().parent.parent.parent
load_dotenv(project_root / ".env")
from typing import List, Dict, Any, Set
from datetime import datetime, timezone, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from tqdm import tqdm

from common.init_mongodb import init_mongodb

# 로거 설정
logger = logging.getLogger(__name__)

# 한국 표준시 (UTC+9)
KST = timezone(timedelta(hours=9))

# 상수
COMPANY_COLLECTION = "사용자정보서비스.조달업체기본정보"
NTS_STATUS_COLLECTION = "사업자등록정보진위확인및상태조회서비스.상태조회"
NTS_API_URL = "https://api.odcloud.kr/api/nts-businessman/v1/status"
BATCH_SIZE = 100  # API 1회 최대 조회 건수
RETRY_INTERVAL = 10  # 재시도 대기 시간(초)
NUM_WORKERS = 5  # 병렬 처리 워커 수 (API 트래픽 제한 고려)

# 비교 대상 필드 (이 필드들이 변경되면 is_synced = False)
COMPARE_FIELDS = [
    "b_stt",
    "b_stt_cd",
    "tax_type",
    "tax_type_cd",
    "end_dt",
    "utcc_yn",
    "tax_type_change_dt",
    "invoice_apply_dt",
    "rbf_tax_type",
    "rbf_tax_type_cd",
]


class NtsStatusCollector:
    """국세청 사업자등록 상태조회 수집기"""

    def __init__(self):
        """초기화"""
        self.server = None
        self.client = None
        self.db = None
        self.api_key = os.getenv("API_SERVICE_KEY") or os.getenv("API_SERVICE_KEY_1", "")

        if not self.api_key:
            raise ValueError("API_SERVICE_KEY 또는 API_SERVICE_KEY_1 환경변수가 설정되지 않았습니다")

    def connect(self):
        """MongoDB 연결"""
        if not self.client:
            logger.info("MongoDB 연결 중...")
            self.server, self.client = init_mongodb()
            self.db = self.client.get_database("gfcon_raw")
        return self.db

    def close(self):
        """연결 종료"""
        if self.client:
            self.client.close()
            logger.info("MongoDB 클라이언트 종료")
        if self.server:
            self.server.stop()
            logger.info("MongoDB SSH 터널 종료")

    def get_all_bizno(self) -> List[str]:
        """
        조달업체기본정보 컬렉션에서 모든 bizno 조회

        Returns:
            사업자등록번호 리스트
        """
        db = self.connect()
        collection = db[COMPANY_COLLECTION]

        # aggregate로 모든 bizno 조회 (distinct는 16MB 제한)
        pipeline = [
            {"$match": {"bizno": {"$exists": True, "$ne": None, "$ne": ""}}},
            {"$group": {"_id": "$bizno"}},
        ]

        bizno_list = [
            doc["_id"]
            for doc in collection.aggregate(pipeline, allowDiskUse=True)
            if doc["_id"] and doc["_id"].strip()
        ]

        logger.info(f"조회된 bizno 수: {len(bizno_list):,}개")
        return bizno_list

    def get_existing_status(self) -> Dict[str, Dict[str, Any]]:
        """
        기존 상태 조회 결과 조회 (변경 비교용)

        Returns:
            {bizno: {필드들...}} 형태의 딕셔너리
        """
        db = self.connect()
        collection = db[NTS_STATUS_COLLECTION]

        existing = {}
        for doc in collection.find({}, {"_id": 0}):
            bizno = doc.get("b_no")
            if bizno:
                existing[bizno] = doc

        logger.info(f"기존 상태 데이터: {len(existing):,}개")
        return existing

    def call_api(self, bizno_list: List[str]) -> List[Dict[str, Any]]:
        """
        국세청 상태조회 API 호출 (재시도 로직 포함)

        Args:
            bizno_list: 사업자등록번호 리스트 (최대 100개)

        Returns:
            API 응답의 data 리스트
        """
        if not bizno_list:
            return []

        if len(bizno_list) > BATCH_SIZE:
            raise ValueError(f"1회 최대 {BATCH_SIZE}개까지 조회 가능합니다")

        headers = {
            "Content-Type": "application/json",
            "Accept": "application/json",
        }
        params = {"serviceKey": self.api_key}
        payload = {"b_no": bizno_list}

        while True:
            try:
                response = requests.post(
                    NTS_API_URL,
                    params=params,
                    json=payload,
                    headers=headers,
                    timeout=30
                )

                # HTTP 에러 확인
                if response.status_code != 200:
                    # Rate limit 에러 (트래픽 초과) - 재시도
                    if response.status_code == 400:
                        try:
                            error_data = response.json()
                            if error_data.get("code") == -10:
                                logger.warning(f"트래픽 제한 초과 - {RETRY_INTERVAL}초 후 재시도...")
                                time.sleep(RETRY_INTERVAL)
                                continue
                        except ValueError:
                            pass

                    logger.error(f"API 호출 실패 (HTTP {response.status_code})")
                    logger.error(f"응답 본문: {response.text[:500]}")
                    return []

                result = response.json()

                if result.get("status_code") != "OK":
                    logger.warning(f"API 응답 상태: {result.get('status_code')}")
                    return []

                return result.get("data", [])

            except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
                logger.warning(f"API 호출 실패: {e} - {RETRY_INTERVAL}초 후 재시도...")
                time.sleep(RETRY_INTERVAL)
                continue

            except requests.exceptions.RequestException as e:
                logger.error(f"API 호출 실패 (재시도 불가): {e}")
                return []

            except ValueError as e:
                logger.error(f"JSON 파싱 실패: {e}")
                return []

    def is_changed(self, existing: Dict[str, Any], new: Dict[str, Any]) -> bool:
        """
        기존 데이터와 새 데이터 비교

        Args:
            existing: 기존 MongoDB 문서
            new: 새 API 응답 데이터

        Returns:
            변경 여부
        """
        for field in COMPARE_FIELDS:
            old_val = existing.get(field, "")
            new_val = new.get(field, "")
            # 빈 문자열과 None은 동일하게 취급
            if (old_val or "") != (new_val or ""):
                return True
        return False

    def save_status(
        self, data_list: List[Dict[str, Any]], existing_map: Dict[str, Dict[str, Any]]
    ) -> Dict[str, int]:
        """
        상태 조회 결과 저장

        Args:
            data_list: API 응답 데이터 리스트
            existing_map: 기존 데이터 맵 (변경 비교용)

        Returns:
            {"inserted": N, "updated": N, "unchanged": N}
        """
        db = self.connect()
        collection = db[NTS_STATUS_COLLECTION]

        # 인덱스 생성 (최초 1회)
        collection.create_index([("b_no", 1)], unique=True)

        stats = {"inserted": 0, "updated": 0, "unchanged": 0}
        now = datetime.now(KST)

        for item in data_list:
            bizno = item.get("b_no")
            if not bizno:
                continue

            # 수집 시점 추가
            item["collected_at"] = now

            existing = existing_map.get(bizno)

            if existing is None:
                # 신규 삽입
                item["is_synced"] = False
                try:
                    collection.insert_one(item)
                    stats["inserted"] += 1
                except Exception as e:
                    logger.error(f"삽입 실패 ({bizno}): {e}")

            elif self.is_changed(existing, item):
                # 변경됨 → 업데이트 + is_synced = False
                item["is_synced"] = False
                collection.update_one({"b_no": bizno}, {"$set": item})
                stats["updated"] += 1

            else:
                # 변경 없음 → is_synced 유지 (collected_at만 업데이트)
                collection.update_one(
                    {"b_no": bizno},
                    {"$set": {"collected_at": now}},
                )
                stats["unchanged"] += 1

        return stats

    def _process_batch(
        self,
        batch: List[str],
        existing_map: Dict[str, Dict[str, Any]],
        pbar: tqdm,
        stats_lock: threading.Lock,
        stats: Dict[str, int],
    ) -> None:
        """
        단일 배치 처리 (병렬 처리용)

        Args:
            batch: bizno 리스트 (최대 100개)
            existing_map: 기존 데이터 맵
            pbar: 전체 진행률 표시용 tqdm
            stats_lock: 통계 업데이트용 락
            stats: 공유 통계 딕셔너리
        """
        # API 호출
        data_list = self.call_api(batch)

        if not data_list:
            with stats_lock:
                stats["api_errors"] += len(batch)
            pbar.update(1)
            return

        # 저장
        batch_stats = self.save_status(data_list, existing_map)

        # 통계 업데이트
        with stats_lock:
            stats["inserted"] += batch_stats["inserted"]
            stats["updated"] += batch_stats["updated"]
            stats["unchanged"] += batch_stats["unchanged"]

            # API 응답에서 누락된 건수 (미등록 사업자 등)
            responded_count = len(data_list)
            if responded_count < len(batch):
                stats["api_errors"] += len(batch) - responded_count

        pbar.update(1)

    def verify_collection_counts(self) -> bool:
        """
        수집 완료 후 두 컬렉션의 document 수 비교 검증

        Returns:
            일치 여부
        """
        db = self.connect()

        company_count = db[COMPANY_COLLECTION].count_documents(
            {"bizno": {"$exists": True, "$ne": None, "$ne": ""}}
        )
        nts_count = db[NTS_STATUS_COLLECTION].estimated_document_count()

        logger.info("-" * 60)
        logger.info("[검증] 컬렉션 document 수 비교")
        logger.info(f"  - {COMPANY_COLLECTION}: {company_count:,}개")
        logger.info(f"  - {NTS_STATUS_COLLECTION}: {nts_count:,}개")

        if company_count == nts_count:
            logger.info("  → 일치")
            return True
        else:
            diff = abs(company_count - nts_count)
            logger.warning(f"  → 불일치 (차이: {diff:,}개)")
            return False

    def collect(self, num_workers: int = NUM_WORKERS) -> Dict[str, int]:
        """
        전체 수집 실행 (병렬 처리)

        Args:
            num_workers: 병렬 처리 워커 수 (기본값: NUM_WORKERS)

        Returns:
            수집 통계 {"total": N, "inserted": N, "updated": N, "unchanged": N, "api_errors": N}
        """
        logger.info("=" * 60)
        logger.info("[국세청 상태조회] 수집 시작")
        logger.info("=" * 60)

        try:
            # 1. 모든 bizno 조회
            bizno_list = self.get_all_bizno()
            total_count = len(bizno_list)

            if not bizno_list:
                logger.info("수집할 bizno가 없습니다")
                return {"total": 0, "inserted": 0, "updated": 0, "unchanged": 0, "api_errors": 0}

            # 2. 기존 데이터 조회 (변경 비교용)
            existing_map = self.get_existing_status()

            # 3. 배치 분할
            batches = [
                bizno_list[i : i + BATCH_SIZE]
                for i in range(0, len(bizno_list), BATCH_SIZE)
            ]
            total_batches = len(batches)

            logger.info(f"총 {total_count:,}개 bizno를 {total_batches:,}개 배치로 처리")
            logger.info(f"병렬 워커 수: {num_workers}")

            # 4. 병렬 처리
            stats = {"total": total_count, "inserted": 0, "updated": 0, "unchanged": 0, "api_errors": 0}
            stats_lock = threading.Lock()

            with tqdm(total=total_batches, desc="국세청 상태조회") as pbar:
                with ThreadPoolExecutor(max_workers=num_workers) as executor:
                    futures = [
                        executor.submit(
                            self._process_batch,
                            batch,
                            existing_map,
                            pbar,
                            stats_lock,
                            stats,
                        )
                        for batch in batches
                    ]

                    # 모든 작업 완료 대기
                    for future in as_completed(futures):
                        # 예외 발생 시 전파
                        future.result()

            # 5. 결과 출력
            logger.info("=" * 60)
            logger.info("[국세청 상태조회] 수집 완료")
            logger.info("=" * 60)
            logger.info(f"  - 총 bizno: {stats['total']:,}개")
            logger.info(f"  - 신규 삽입: {stats['inserted']:,}개")
            logger.info(f"  - 변경 업데이트: {stats['updated']:,}개")
            logger.info(f"  - 변경 없음: {stats['unchanged']:,}개")
            logger.info(f"  - API 오류/미등록: {stats['api_errors']:,}개")

            # 6. 검증
            self.verify_collection_counts()

            return stats

        except Exception as e:
            logger.error(f"수집 중 오류 발생: {e}", exc_info=True)
            raise

        finally:
            self.close()


def collect_nts_status() -> Dict[str, int]:
    """
    국세청 상태조회 수집 함수 (DAG에서 호출용)

    Returns:
        수집 통계
    """
    collector = NtsStatusCollector()
    return collector.collect()


if __name__ == "__main__":
    # 로깅 설정
    logging.basicConfig(
        level=logging.INFO,
        format="[%(levelname)s] %(asctime)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # 수집 실행
    result = collect_nts_status()
    print(f"\n수집 결과: {result}")
