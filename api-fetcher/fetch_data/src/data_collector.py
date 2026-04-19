from typing import Any
import time
from tqdm import tqdm

from common.logger import setup_loggers, update_log_meta
from common.utils import *
from common.init_mongodb import *
from common.init_psql import init_psql
from common.api_key_manager import api_key_manager
from .api_client import ApiClient
from .mongo_writer import MongoWriter
from .params_builder import ParamsBuilder
from .record_writer import RecordWriter


# progrsdivcdnm -> operation 매핑 (투찰데이터 수집용)
PROGRS_DIV_OPERATION_MAP = {
    "개찰완료": 13,
    "유찰": 14,
    "재입찰": 15,
    "재시담": 15,
}


# ---------------------------------------------------------------------------
# DataCollector orchestrator
# ---------------------------------------------------------------------------
class DataCollector:
    """Top‑level orchestrator that glues API ↔ DB ↔ filesystem."""

    # bsnsDivCd (사업구분코드) 매핑: 1=물품, 2=외자, 3=공사, 5=용역
    BSNS_DIV_MAP = {
        1: "물품",
        2: "외자",
        3: "공사",
        5: "용역",
    }

    # 서비스별 API 도메인
    SERVICE_DOMAIN_MAP = {
        "낙찰정보서비스": "https://apis.data.go.kr/1230000",
        "default": None,  # 환경변수 사용
    }

    def __init__(
        self,
        service_name: str | None = None,
        operation_number: str | int | None = None,
        year: str | int | None = None,
        start_date: str | None = None,
        end_date: str | None = None,
        bsns_div_cd: int | None = None,
        existing_log_dir: str | None = None,
    ) -> None:
        # ------------------------------------------------------------------
        # Resolve user input / defaults
        # ------------------------------------------------------------------
        self.executed_year = year
        self.start_date = start_date
        self.end_date = end_date
        self._original_bsns_div_cd = bsns_div_cd  # 원래 전달된 값 (로깅용)
        self.bsns_div_cd = bsns_div_cd if bsns_div_cd is not None else 3  # 기본값: 공사
        if service_name is None and operation_number is None:
            service_name, operation_number = input_handler()
        self.service_name, self.operation_number = service_name, operation_number

        # ------------------------------------------------------------------
        # External resources
        # ------------------------------------------------------------------
        self.server, self.client = init_mongodb()
        self.db = self.client.get_database("gfcon_raw")

        # 서비스별 API 도메인 설정
        if self.service_name in self.SERVICE_DOMAIN_MAP:
            self.API_BASE_DOMAIN = self.SERVICE_DOMAIN_MAP[self.service_name]
        else:
            self.API_BASE_DOMAIN = os.getenv("API_BASE_DOMAIN", "https://api.g2b.go.kr")
        self.API_SERVICE_KEY = os.getenv("API_SERVICE_KEY", "")

        # ------------------------------------------------------------------
        # Service metadata (dynamic per user choice)
        # ------------------------------------------------------------------
        svc_info = get_service_info(
            service_name=self.service_name, operation_number=self.operation_number
        )
        op_info = svc_info["filtered_operations"][0]

        # 컬렉션명 생성 (공공데이터개방표준서비스는 사업구분 suffix 추가)
        base_collection_name = op_info["raw_data_collection_name"]
        if self.service_name == "공공데이터개방표준서비스":
            bsns_div_name = self.BSNS_DIV_MAP.get(self.bsns_div_cd, "공사")
            self.collection_name = f"{base_collection_name}-{bsns_div_name}"
        else:
            self.collection_name = base_collection_name

        self.operation_name = op_info["오퍼레이션명(국문)"]
        service_endpoint = svc_info["service_endpoint"]
        operation_endpoint = op_info["오퍼레이션명(영문)"]
        self.endpoint = f"{service_endpoint}/{operation_endpoint}"
        self.unique_fields = op_info["unique_fields"]

        # ------------------------------------------------------------------
        # Utilities / helpers (로거에 컨텍스트 정보 전달)
        # ------------------------------------------------------------------
        log_result = setup_loggers(
            year=str(self.executed_year) if self.executed_year else None,
            service_name=self.service_name,
            operation_name=self.operation_name,
            target_start=self.start_date,
            target_end=self.end_date,
            bsns_div_cd=self._original_bsns_div_cd,  # 원래 전달된 값 (None이면 None)
            existing_log_dir=existing_log_dir,
        )
        self.loggers = log_result["loggers"]
        self.log_dir = log_result["log_dir"]
        self.meta_path = log_result["meta_path"]

        # 수집 통계 추적
        self._total_records = 0
        self._total_inserted = 0
        self._total_updated = 0
        self._error_count = 0

        self.api = ApiClient(self.API_BASE_DOMAIN)
        self.params_builder = ParamsBuilder(self.API_SERVICE_KEY)
        self.mongo = MongoWriter(self.db, self.collection_name, self.unique_fields)
        self.recorder = RecordWriter(self.collection_name)

    # 공고 데이터 및 기업 데이터 수집에 사용
    def collect_data_by_day(
        self,
        date: str,
        collect_bids: bool = False,
        bid_counter_by_date: dict | None = None,
    ) -> int | None | Any:

        if self.service_name == "공공데이터개방표준서비스":
            api_type, sub_type = "pubData", self.operation_number
        elif self.service_name == "사용자정보서비스":
            if self.operation_number == 1:  # 수요기관정보조회
                api_type, sub_type = "institution", 1
            elif self.operation_number == 2:  # 조달업체기본정보
                api_type, sub_type = "company", 2
            elif self.operation_number == 3:  # 조달업체업종정보조회
                api_type, sub_type = "company", 3
            else:
                api_type, sub_type = "notice", 0
        elif self.service_name == "낙찰정보서비스":
            # 오퍼레이션 5,6,7,8 (개찰결과) / 9,10,11,12 (예비가격)
            api_type, sub_type = "opengResult", 0
        else:
            api_type, sub_type = "notice", 0
        params = self.params_builder.build(
            api_type, date, sub_type, bsns_div_cd=self.bsns_div_cd
        )

        try:
            data = self.api.get(self.endpoint, params)

            total_count = data["response"]["body"]["totalCount"]
            num_of_rows = params["numOfRows"]
            total_pages = -(-total_count // num_of_rows)

            self.loggers["application"].day(
                f"{self.collection_name} - {date} - 전체 데이터 수: {total_count}"
            )
            self.loggers["day"].day(
                f"{self.collection_name} - {date} - 전체 데이터 수: {total_count}"
            )

            if collect_bids:
                try:
                    db_date_count = bid_counter_by_date[
                        f"{date[:4]}-{date[4:6]}-{date[6:]}"
                    ]
                except KeyError:
                    db_date_count = 0

                # ±5%까지 허용하도록...
                margin_rate = 0.05
                if abs(db_date_count - total_count) <= total_count * margin_rate:
                    self.loggers["application"].verify(
                        f"{date} - 데이터 개수 차이 5% 내외 - API:{total_count} | DB:{db_date_count} PASSED"
                    )
                    return None
                else:
                    self.loggers["application"].verify(
                        f"{date} - 데이터 개수 불일치 - API:{total_count} | DB:{db_date_count} - CONTINUE"
                    )

            total_success, total_insert, total_update, total_failed = 0, 0, 0, 0

            for page in range(1, total_pages + 1):
                page_insert_count = 0
                page_update_count = 0

                params["pageNo"] = page
                data = self.api.get(self.endpoint, params)

                items = data["response"]["body"]["items"]
                if isinstance(items, dict):
                    items = [items]

                for item in items:
                    result = self.mongo.upsert(item)
                    if result == "insert":
                        page_insert_count += 1
                    elif result == "update":
                        page_update_count += 1
                    else:
                        total_failed += 1

                success_count = page_insert_count + page_update_count
                total_insert += page_insert_count
                total_update += page_update_count
                total_success += success_count
                self.loggers["application"].fetch(
                    f"{date} - {page}/{total_pages} 페이지 처리완료: {success_count}({page_insert_count}+{page_update_count})건"
                )

            self.loggers["application"].day(
                f"{self.collection_name} - {date} - 최종 저장 건수: {total_success}({total_insert}+{total_update})"
            )
            self.loggers["day"].day(
                f"{self.collection_name} - {date} - 최종 저장 건수: {total_success}({total_insert}+{total_update})"
            )

            # 통계 누적
            self._total_records += total_success
            self._total_inserted += total_insert
            self._total_updated += total_update

            return total_success

        except Exception as e:
            self._error_count += 1
            self.loggers["application"].error(
                f"{self.collection_name} - {date} - 처리 중 오류 발생: {str(e)}",
                exc_info=True,
            )
            self.loggers["error"].error(
                f"{self.collection_name} - {date} - 처리 중 오류 발생: {str(e)}",
                exc_info=True,
            )
            raise

    def collect_all_data_by_day(self, start_date: str, end_date: str) -> None:
        # 투찰 데이터 수집인지?
        collect_bids: bool = (
            self.collection_name
            == "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보"
        )

        date_list = list(generate_dates(start_date, end_date))
        self.loggers["application"].info(
            f"{start_date} ~ {end_date} 내 데이터를 모두 가져옵니다."
        )

        bid_counter_by_date = (
            self.count_data_by_date(start_date, end_date) if collect_bids else None
        )

        pending_dates = date_list
        attempt = 1

        while pending_dates:
            # 이번시도에서 실패한 날짜 기록
            error_dates: list[str] = []

            for date in pending_dates:
                try:
                    self.collect_data_by_day(
                        date, collect_bids, bid_counter_by_date=bid_counter_by_date
                    )
                except Exception as e:
                    self.loggers["error"].error(
                        f"{self.collection_name} - {date} - 수집 실패: {str(e)}"
                    )
                    self.recorder.append(date, "error_date.txt")
                    error_dates.append(date)

            if not error_dates:
                self.loggers["application"].info(
                    "🎉 모든 데이터가 성공적으로 수집되었습니다."
                )
                break

            # 에러가 발생한 날짜들에 대해 다시 시도
            self.loggers["application"].warning(
                f"⚠️ [Attempt {attempt}] {len(error_dates)}개의 날짜에서 오류 발생. 재시도 진행."
            )
            pending_dates = error_dates  # 에러 발생한 날짜들만 다시 시도
            attempt += 1  # 다음 반복을 위해 시도 횟수 증가

    def collect_data_by_code(self, params: dict, code: str) -> dict:
        """
        코드(공고번호, 사업자번호 등)로 데이터 수집

        Returns:
            dict: {"total_count": int, "insert": int, "update": int, "failed": int}
        """
        try:
            data = self.api.get(self.endpoint, params)

            # API 에러 응답 체크 (response 키 없음 = 에러)
            if "response" not in data:
                error_info = str(data)[:200]
                self.loggers["application"].warning(
                    f"{self.collection_name} - {code} - API 에러 응답 (스킵): {error_info}"
                )
                return {"total_count": 0, "insert": 0, "update": 0, "failed": 0}

            total_count = data["response"]["body"]["totalCount"]
            num_of_rows = params["numOfRows"]
            total_pages = -(-total_count // num_of_rows)

            total_success, total_insert, total_update, total_failed = 0, 0, 0, 0

            for page in range(1, total_pages + 1):
                page_insert_count = 0
                page_update_count = 0

                params["pageNo"] = page
                data = self.api.get(self.endpoint, params)

                items = data["response"]["body"]["items"]
                if isinstance(items, dict):
                    items = [items]

                for item in items:
                    result = self.mongo.upsert(item)
                    if result == "insert":
                        page_insert_count += 1
                    elif result == "update":
                        page_update_count += 1
                    else:
                        total_failed += 1

                success_count = page_insert_count + page_update_count
                total_insert += page_insert_count
                total_update += page_update_count
                total_success += success_count

            return {
                "total_count": total_count,
                "insert": total_insert,
                "update": total_update,
                "failed": total_failed,
            }

        except Exception as e:
            self.loggers["application"].error(
                f"{self.collection_name} - {code} - 처리 중 오류 발생: {str(e)}",
                exc_info=True,
            )
            self.loggers["error"].error(
                f"{self.collection_name} - {code} - 처리 중 오류 발생: {str(e)}",
                exc_info=True,
            )
            raise

    def collect_notice_by_NtceNo(self, NtceNo_list: list[str]) -> None:
        # 투찰데이터 API (13,14,15)는 inqryDiv=4 사용
        if self.service_name == "낙찰정보서비스" and self.operation_number in [13, 14, 15]:
            inqry_div = 4
        else:
            inqry_div = 2

        for NtceNo in tqdm(NtceNo_list, total=len(NtceNo_list)):
            params = {
                "serviceKey": self.API_SERVICE_KEY,
                "pageNo": 1,
                "numOfRows": 100,
                "inqryDiv": inqry_div,
                "type": "json",
                "bidNtceNo": NtceNo,
            }

            self.collect_data_by_code(params, code=NtceNo)

    def collect_company_by_bizno(self, bizno_list: list[str]) -> None:
        for bizno in tqdm(bizno_list, total=len(bizno_list)):
            params = {
                "serviceKey": self.API_SERVICE_KEY,
                "pageNo": 1,
                "numOfRows": 100,
                "inqryDiv": 3,
                "bizno": bizno,
                "type": "json",
            }

            self.collect_data_by_code(params, code=bizno)

    def get_notice_number_list(self):
        collection = self.db.get_collection("낙찰정보서비스.낙찰된목록현황공사조회")
        result = collection.find({}, {"bidNtceNo": 1, "_id": 0})

        result = [doc["bidNtceNo"] for doc in result]

        return result

    def count_data_by_date(self, start_date: str, end_date: str) -> dict:
        pipeline = []

        # 투찰데이터 수집의 경우
        if (
            self.collection_name
            == "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보"
        ):
            date_field_name = "opengDate"

            pipeline = [
                {"$match": {date_field_name: {"$gte": start_date, "$lte": end_date}}},
                {"$group": {"_id": f"${date_field_name}", "count": {"$sum": 1}}},
                {"$sort": {"_id": 1}},
            ]

        # 공고 기초금액 관련 데이터 수집의 경우
        elif (
            self.collection_name
            == "입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회"
        ):
            date_field_name = "bssamtOpenDt"
        elif (
            self.collection_name == "입찰공고정보서비스.입찰공고목록정보에대한공사조회"
        ):
            date_field_name = "rgstDt"

        result = list(self.mongo.collection.aggregate(pipeline))
        return {item["_id"]: item["count"] for item in result}

    def execute(self):
        try:
            # 특정 기간 수집 (우선순위 1)
            if self.start_date and self.end_date:
                self.loggers["application"].info(
                    f"특정 기간 수집 모드: {self.start_date} ~ {self.end_date}"
                )
                self.collect_all_data_by_day(self.start_date, self.end_date)

            # 특정년도 수집 (우선순위 2)
            elif self.executed_year:
                start_date = f"{self.executed_year}-01-01"
                end_date = f"{self.executed_year}-12-31"
                self.loggers["application"].info(
                    f"특정 연도 수집 모드: {self.executed_year}"
                )
                self.collect_all_data_by_day(start_date, end_date)

            # 전체수집 (우선순위 3)
            else:
                start_date = "2001-01-01"
                end_date = "2009-12-31"
                self.loggers["application"].info(
                    f"전체 수집 모드: {start_date} ~ {end_date}"
                )
                self.collect_all_data_by_day(start_date, end_date)

            # 수집 완료 - 메타데이터 업데이트
            status = "success" if self._error_count == 0 else "completed_with_errors"
            update_log_meta(
                self.meta_path,
                status=status,
                records_total=self._total_records,
                records_inserted=self._total_inserted,
                records_updated=self._total_updated,
                error_count=self._error_count,
            )

        except Exception as e:
            # 수집 실패 - 메타데이터 업데이트
            update_log_meta(
                self.meta_path,
                status="failed",
                records_total=self._total_records,
                records_inserted=self._total_inserted,
                records_updated=self._total_updated,
                error_count=self._error_count,
                error_message=str(e),
            )
            raise

    # -------------------------------------------------------------------------
    # 투찰데이터 수집 (오퍼레이션 13, 14, 15)
    # -------------------------------------------------------------------------
    @classmethod
    def collect_bid_data(
        cls,
        schema: str = "test",
        progrs_type: str | None = None,
        batch_size: int = 100,
        limit: int | None = None,
        max_retries: int = 3,
        worker_id: int | None = None,
        num_workers: int | None = None,
        shared_log_dir: str | None = None,
    ) -> dict:
        """
        PostgreSQL notice 테이블에서 투찰데이터 수집 대상을 조회하고 수집 진행

        Args:
            schema: PostgreSQL 스키마명 (test 또는 data)
            progrs_type: 특정 진행구분만 수집 (개찰완료/유찰/재입찰/재시담)
            batch_size: 배치 크기 (bid_collected 업데이트 단위)
            limit: 수집할 최대 공고 수
            max_retries: 실패 시 최대 재시도 횟수
            worker_id: 워커 ID (0부터 시작, 병렬 처리용)
            num_workers: 총 워커 수 (병렬 처리용)
            shared_log_dir: 공유 로그 디렉토리 경로 (멀티워커 통합 로깅용)

        Returns:
            수집 통계 dict
        """
        # PostgreSQL 연결
        psql_server, psql_conn = init_psql()

        # 통계
        stats = {
            "total_notices": 0,
            "total_success": 0,
            "total_failed": 0,
            "total_bids": 0,
            "total_inserted": 0,
            "total_updated": 0,
            "by_type": {},
        }
        failed_notices: list[tuple[str, str]] = []
        _log_dir = None  # 첫 collector에서 설정됨

        try:
            worker_info = f", worker {worker_id}/{num_workers}" if num_workers else ""
            print(f"[INFO] 투찰데이터 수집 시작 (schema: {schema}{worker_info})")

            # API 키 상태 출력
            key_status = api_key_manager.get_status()
            print(f"[INFO] API 키 상태: {key_status['available_today']}/{key_status['total_keys']}개 사용 가능")

            # 수집 대상 공고 조회
            grouped_notices = cls._get_bid_target_notices(
                psql_conn, schema, progrs_type, limit, worker_id, num_workers
            )

            if not grouped_notices:
                print("[INFO] 수집할 공고가 없습니다.")
                return stats

            # 전체 현황 출력
            total_target = sum(len(notices) for notices in grouped_notices.values())
            print(f"[INFO] 수집 대상 총 {total_target:,}건")
            for progrs_div, notices in grouped_notices.items():
                op_num = PROGRS_DIV_OPERATION_MAP.get(progrs_div, "?")
                print(f"[INFO]   - {progrs_div} (op {op_num}): {len(notices):,}건")

            # 각 progrsdivcdnm별로 수집
            for progrs_div, notice_list in grouped_notices.items():
                operation_number = PROGRS_DIV_OPERATION_MAP.get(progrs_div)

                if not operation_number:
                    print(f"[WARN] 알 수 없는 progrsdivcdnm: {progrs_div}")
                    continue

                # DataCollector 인스턴스 생성
                collector = cls(
                    service_name="낙찰정보서비스",
                    operation_number=operation_number,
                    existing_log_dir=shared_log_dir,
                )
                # 이 collector의 로거 사용
                loggers = collector.loggers
                _log_dir = collector.log_dir

                # 수집 진행
                collected_notices = []
                type_stats = {
                    "total": len(notice_list),
                    "success": 0,
                    "failed": 0,
                    "bids": 0,
                    "inserted": 0,
                    "updated": 0,
                }

                pending_notices = notice_list.copy()
                attempt = 1

                # 멀티프로세스 모드에서는 tqdm 비활성화
                use_tqdm = num_workers is None or num_workers <= 1
                progress_interval = 100  # 로그 출력 간격

                while pending_notices:
                    error_notices: list[str] = []

                    iterator = tqdm(pending_notices, desc=f"{progrs_div}", unit="건") if use_tqdm else enumerate(pending_notices)
                    for item in iterator:
                        if use_tqdm:
                            bidntceno = item
                            idx = None
                        else:
                            idx, bidntceno = item
                            # 주기적 진행상황 로그
                            if idx > 0 and idx % progress_interval == 0:
                                loggers["application"].info(
                                    f"[Worker {worker_id}] 진행: {idx:,}/{len(pending_notices):,} ({idx/len(pending_notices)*100:.1f}%)"
                                )
                        try:
                            result = cls._collect_single_bid(
                                collector, bidntceno, max_retries, loggers
                            )

                            if result is not None:
                                collected_notices.append(bidntceno)
                                type_stats["success"] += 1
                                type_stats["bids"] += result["total_count"]
                                type_stats["inserted"] += result["insert"]
                                type_stats["updated"] += result["update"]
                            else:
                                error_notices.append(bidntceno)

                            # 배치 크기마다 플래그 업데이트
                            if len(collected_notices) >= batch_size:
                                updated = cls._update_bid_collected_flags(
                                    psql_conn, schema, collected_notices
                                )
                                loggers["application"].info(
                                    f"[BATCH] bid_collected 업데이트: {updated}건"
                                )
                                collected_notices = []

                        except RuntimeError as e:
                            if "exhausted" in str(e).lower():
                                # 현재까지 수집한 것 저장
                                if collected_notices:
                                    cls._update_bid_collected_flags(
                                        psql_conn, schema, collected_notices
                                    )
                                    collected_notices = []

                                # 실패 목록 저장
                                for ntce in pending_notices[pending_notices.index(bidntceno):]:
                                    failed_notices.append((ntce, progrs_div))

                                cls._save_failed_notices(failed_notices, _log_dir, loggers)
                                loggers["application"].error("모든 API 키 소진! 다음 날 다시 실행하세요.")
                                return stats

                        except Exception as e:
                            loggers["error"].error(f"{bidntceno} 수집 실패: {str(e)}")
                            error_notices.append(bidntceno)
                            continue

                    if not error_notices:
                        break

                    # 재시도
                    loggers["application"].warning(
                        f"⚠️ [Attempt {attempt}] {len(error_notices)}개 공고 오류 발생. 재시도 진행."
                    )
                    pending_notices = error_notices
                    attempt += 1

                    if attempt > max_retries:
                        loggers["application"].warning(
                            f"최대 재시도 횟수 초과. {len(error_notices)}건 실패 처리."
                        )
                        type_stats["failed"] += len(error_notices)
                        for ntce in error_notices:
                            failed_notices.append((ntce, progrs_div))
                        break

                # 남은 공고 플래그 업데이트
                if collected_notices:
                    updated = cls._update_bid_collected_flags(
                        psql_conn, schema, collected_notices
                    )
                    loggers["application"].info(f"[BATCH] bid_collected 업데이트: {updated}건")

                stats["by_type"][progrs_div] = type_stats
                stats["total_notices"] += type_stats["total"]
                stats["total_success"] += type_stats["success"]
                stats["total_failed"] += type_stats["failed"]
                stats["total_bids"] += type_stats["bids"]
                stats["total_inserted"] += type_stats["inserted"]
                stats["total_updated"] += type_stats["updated"]

                loggers["application"].info(
                    f"[{progrs_div}] 완료: 공고 {type_stats['success']:,}건 성공, "
                    f"{type_stats['failed']:,}건 실패 | "
                    f"투찰 {type_stats['bids']:,}건 (insert: {type_stats['inserted']:,}, update: {type_stats['updated']:,})"
                )

            # 실패 목록 저장
            if failed_notices:
                cls._save_failed_notices(failed_notices, _log_dir, loggers)

            # 결과 로깅
            loggers["application"].info(
                f"🎉 투찰데이터 수집 완료: "
                f"공고 {stats['total_notices']:,}건 (성공: {stats['total_success']:,}, 실패: {stats['total_failed']:,}) | "
                f"투찰 {stats['total_bids']:,}건 (insert: {stats['total_inserted']:,}, update: {stats['total_updated']:,})"
            )

            return stats

        finally:
            if psql_conn:
                psql_conn.close()
            if psql_server:
                psql_server.stop()

    @staticmethod
    def _get_bid_target_notices(
        conn,
        schema: str,
        progrs_type: str | None = None,
        limit: int | None = None,
        worker_id: int | None = None,
        num_workers: int | None = None,
    ) -> dict[str, list[str]]:
        """투찰데이터 수집 대상 공고 조회"""
        query = f"""
            SELECT bidntceno, progrsdivcdnm
            FROM {schema}.notice
            WHERE progrsdivcdnm IS NOT NULL
              AND (bid_collected = FALSE OR bid_collected IS NULL)
        """

        if progrs_type:
            query += f" AND progrsdivcdnm = '{progrs_type}'"

        # 워커 분할 (해시 기반 균등 분배)
        if worker_id is not None and num_workers is not None:
            query += f" AND abs(hashtext(bidntceno)) % {num_workers} = {worker_id}"

        query += " ORDER BY actual_opengdt DESC NULLS LAST"

        if limit:
            query += f" LIMIT {limit}"

        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        cursor.close()

        # progrsdivcdnm별로 그룹화
        grouped: dict[str, list[str]] = {}
        for bidntceno, progrsdivcdnm in results:
            if progrsdivcdnm not in grouped:
                grouped[progrsdivcdnm] = []
            grouped[progrsdivcdnm].append(bidntceno)

        return grouped

    @staticmethod
    def _collect_single_bid(
        collector: "DataCollector",
        bidntceno: str,
        max_retries: int,
        loggers: dict,
    ) -> dict | None:
        """
        단일 공고 투찰데이터 수집 (재시도 포함)

        Returns:
            dict: {"total_count": int, "insert": int, "update": int} 성공 시
            None: 실패 시
        """
        for attempt in range(max_retries):
            try:
                params = {
                    "serviceKey": collector.API_SERVICE_KEY,
                    "pageNo": 1,
                    "numOfRows": 100,
                    "inqryDiv": 4,
                    "type": "json",
                    "bidNtceNo": bidntceno,
                }
                result = collector.collect_data_by_code(params, code=bidntceno)

                # 상세 로깅
                loggers["application"].info(
                    f"  {bidntceno} - 투찰 {result['total_count']}건 "
                    f"(insert: {result['insert']}, update: {result['update']})"
                )
                return result

            except RuntimeError as e:
                if "exhausted" in str(e).lower():
                    raise
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                loggers["error"].error(f"{bidntceno} 수집 실패 (재시도 소진): {str(e)}")
                return None
            except Exception as e:
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                loggers["error"].error(f"{bidntceno} 수집 실패: {str(e)}")
                return None
        return None

    @staticmethod
    def _update_bid_collected_flags(conn, schema: str, bidntcenos: list[str]) -> int:
        """bid_collected 플래그 일괄 업데이트"""
        if not bidntcenos:
            return 0

        cursor = conn.cursor()
        placeholders = ",".join(["%s"] * len(bidntcenos))
        query = f"""
            UPDATE {schema}.notice
            SET bid_collected = TRUE
            WHERE bidntceno IN ({placeholders})
        """
        cursor.execute(query, bidntcenos)
        updated = cursor.rowcount
        conn.commit()
        cursor.close()
        return updated

    @staticmethod
    def _save_failed_notices(
        failed_notices: list[tuple[str, str]],
        log_dir: str,
        loggers: dict,
    ) -> None:
        """실패한 공고 목록 저장"""
        if not failed_notices:
            return

        from datetime import datetime
        from pathlib import Path

        filepath = Path(log_dir) / f"failed_notices_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
        with open(filepath, "w") as f:
            for bidntceno, progrs_type in failed_notices:
                f.write(f"{bidntceno},{progrs_type}\n")
        loggers["application"].info(f"실패한 공고 목록 저장: {filepath}")
