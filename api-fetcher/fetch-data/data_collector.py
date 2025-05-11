import ssl
import time
import math
from itertools import count
from typing import Any, Dict, List, Optional

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from pymongo.errors import DuplicateKeyError

from common.logger import setup_loggers
from common.utils import *
from common.init_mongodb import *


# SSLContextAdapter (TLS 1.2 이하 강제 & 보안레벨 낮추기) ----------------
class SSLContextAdapter(HTTPAdapter):
	def __init__(self, ssl_context=None, **kwargs):
		self._ssl_context = ssl_context
		super().__init__(**kwargs)

	def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
		if self._ssl_context is not None:
			kwargs["ssl_context"] = self._ssl_context
		self.poolmanager = PoolManager(
			num_pools=connections, maxsize=maxsize, block=block, **kwargs
		)


class ApiClient:
	"""Handles all HTTP communication with retry logic."""

	def __init__(self, base_url: str):
		self.base_url = base_url
		self.logger = setup_loggers()
		self.session = self._create_ssl_session()

	# ---------------------------------------------------------------------
	# Public helpers
	# ---------------------------------------------------------------------
	def get(self, endpoint: str, params: Dict[str, Any], retry_interval: int = 10) -> Dict[str, Any]:
		"""GET with automatic JSON decode & retry."""
		full_url = f"{self.base_url}/{endpoint}"
		while True:
			try:
				response = self.session.get(full_url, params=params, timeout=30)
				response.raise_for_status()
				return response.json()
			except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError) as exc:
				self.logger["application"].error(
					f"{exc.__class__.__name__} while requesting {full_url} – retry in {retry_interval}s"
				)
				time.sleep(retry_interval)
				continue
			except Exception as exc:  # pragma: no cover
				self.logger["error"].error("Unhandled exception in ApiClient", exc_info=True)
				raise

	# ------------------------------------------------------------------
	# Private helpers
	# ------------------------------------------------------------------
	@staticmethod
	def _create_ssl_session() -> requests.Session:
		# 1) SSLContext 생성
		ssl_ctx = ssl.create_default_context()
		# 2) TLS 1.3 비활성 → TLS 1.2 이하
		ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
		# 3) "보안 레벨"을 1로 낮추어, 구버전 Cipher까지 허용
		ssl_ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
		session = requests.Session()
		session.mount("https://", SSLContextAdapter(ssl_context=ssl_ctx))
		return session


# ---------------------------------------------------------------------------
# Persistence layer
# ---------------------------------------------------------------------------
class MongoWriter:
	"""Wraps MongoDB collection with safe insert/update (upsert) behaviour."""

	def __init__(self, db, collection_name: str, unique_fields: List[str]):
		self.collection = db[collection_name]
		self.unique_fields = unique_fields
		self._ensure_index()

	def upsert(self, item: Dict[str, Any]) -> str:
		"""
			"insert"  -> 새 문서가 삽입됨
			"update"  -> 중복으로 인해 수정 수행
			"error"   -> 다른 예외가 발생 (로그는 여기서 남기고, 예외는 상위에서 처리)
		"""
		try:
			# 1) insert 시도
			self.collection.insert_one(item)
			return "insert"

		except DuplicateKeyError:
			# 2) 중복이면 update 수행
			item.pop("_id", None)  # _id 필드 제거 (원본 로직과 동일)

			update_query = {field: item[field] for field in self.unique_fields}
			self.collection.update_one(update_query, {"$set": item})
			return "update"

		except Exception as exc:
			# 3) 기타 에러는 내부 로깅 후 'error' 반환
			from common.logger import setup_loggers

			loggers = setup_loggers()
			loggers["application"].error(f"Mongo upsert 실패: {exc}", exc_info=True)
			loggers["error"].error(f"Mongo upsert 실패: {exc}", exc_info=True)
			return "error"

	def _ensure_index(self) -> None:
		index_spec = [(field, 1) for field in self.unique_fields]
		self.collection.create_index(index_spec, unique=True)


# ---------------------------------------------------------------------------
# Parameter builder
# ---------------------------------------------------------------------------
class ParamsBuilder:
	"""Generate API params & map date fields."""

	def __init__(self, api_service_key: str, num_of_rows: int = 500):
		self.api_service_key = api_service_key
		self.num_of_rows = num_of_rows
		self.params_list = self._build_params_list()
		self.date_field_map = self._build_date_field_map()

	def build(self, api_type: str, date: str, sub_type: Optional[int] = None) -> Dict[str, Any]:
		params = (
			self.params_list[api_type][sub_type].copy()
			if api_type == "pubData"
			else self.params_list[api_type].copy()
		)
		return self._set_date_params(api_type, params, date, sub_type)

	# ------------------------------------------------------------------
	# Internal helpers
	# ------------------------------------------------------------------
	def _set_date_params(self, api_type: str, params: Dict[str, Any], date: str, sub_type: Optional[int]):
		start, end = f"{date}0000", f"{date}2359"
		fields = (
			self.date_field_map[api_type][sub_type]
			if api_type == "pubData"
			else self.date_field_map[api_type]
		)
		for idx, key in enumerate(fields):
			params[key] = start if idx == 0 else end
		return params

	def _build_params_list(self):
		sk, n = self.api_service_key, self.num_of_rows
		return {
			"notice": {
				"serviceKey": sk,
				"pageNo": 1,
				"numOfRows": n,
				"inqryDiv": 1,
				"type": "json",
				"inqryBgnDt": None,
				"inqryEndDt": None,
			},
			"bid": {
				"serviceKey": sk,
				"pageNo": 1,
				"numOfRows": n,
				"type": "json",
				"bidNtceNo": None,
			},
			"pubData": {
				1: {
					"serviceKey": sk,
					"pageNo": 1,
					"numOfRows": n,
					"type": "json",
					"bsnsDivCd": None,
					"bidNtceBgnDt": None,
					"bidNtceEndDt": None,
				},
				2: {
					"serviceKey": sk,
					"pageNo": 1,
					"numOfRows": n,
					"type": "json",
					"bsnsDivCd": 3,
					"opengBgnDt": None,
					"opengEndDt": None,
				},
				3: {
					"serviceKey": sk,
					"pageNo": 1,
					"numOfRows": n,
					"type": "json",
					"cntrctCnclsBgnDate": None,
					"cntrctCnclsEndDate": None,
				},
			},
		}

	@staticmethod
	def _build_date_field_map():
		return {
			"notice": ["inqryBgnDt", "inqryEndDt"],
			"bid": [],
			"pubData": {
				1: ["bidNtceBgnDt", "bidNtceEndDt"],
				2: ["opengBgnDt", "opengEndDt"],
				3: ["cntrctCnclsBgnDate", "cntrctCnclsEndDate"],
			},
		}


# ---------------------------------------------------------------------------
# Record writer
# ---------------------------------------------------------------------------
class RecordWriter:
	"""Append processed ids/dates to text files under fetch_record/"""

	def __init__(self, collection_name: str):
		self.root = os.path.join(get_project_root(), "fetch_record", collection_name)
		os.makedirs(self.root, exist_ok=True)

	def append(self, text: str, filename: str):
		with open(os.path.join(self.root, filename), "a", encoding="utf-8") as fh:
			fh.write(text + "\n")


# ---------------------------------------------------------------------------
# DataCollector orchestrator
# ---------------------------------------------------------------------------
class DataCollector:
	"""Top‑level orchestrator that glues API ↔ DB ↔ filesystem."""

	def __init__(
			self,
			service_name: str | None = None,
			operation_number: str | int | None = None,
			year: str | int | None = None,
	) -> None:
		# ------------------------------------------------------------------
		# Resolve user input / defaults
		# ------------------------------------------------------------------
		self.executed_year = year
		if service_name is None and operation_number is None:
			service_name, operation_number = input_handler()
		self.service_name, self.operation_number = service_name, operation_number

		# ------------------------------------------------------------------
		# External resources
		# ------------------------------------------------------------------
		self.server, self.client = init_mongodb()
		self.db = self.client.get_database("gfcon_raw")

		self.API_BASE_DOMAIN = os.getenv("API_BASE_DOMAIN", "https://api.g2b.go.kr")
		self.API_SERVICE_KEY = os.getenv("API_SERVICE_KEY", "")

		# ------------------------------------------------------------------
		# Service metadata (dynamic per user choice)
		# ------------------------------------------------------------------
		svc_info = get_service_info(service_name=self.service_name, operation_number=self.operation_number)
		op_info = svc_info["filtered_operations"][0]

		self.collection_name = op_info["raw_data_collection_name"]
		service_endpoint = svc_info["service_endpoint"]
		operation_endpoint = op_info["오퍼레이션명(영문)"]
		self.endpoint = f"{service_endpoint}/{operation_endpoint}"
		self.unique_fields = op_info["unique_fields"]

		# ------------------------------------------------------------------
		# Utilities / helpers
		# ------------------------------------------------------------------
		self.loggers = setup_loggers(year=self.executed_year)
		self.api = ApiClient(self.API_BASE_DOMAIN, self.loggers)
		self.params_builder = ParamsBuilder(self.API_SERVICE_KEY)
		self.mongo = MongoWriter(self.db, self.collection_name, self.unique_fields)
		self.recorder = RecordWriter(self.collection_name)

	# 공고 데이터 및 기업 데이터 수집에 사용
	def collect_data_by_day(self, date: str, collect_bids: bool = False,
	                        bid_counter_by_date: dict | None = None) -> int | None | Any:

		if self.service_name == "공공데이터개방표준서비스":
			api_type, sub_type = "pubData", self.operation_number
		else:
			api_type, sub_type = "notice", None
		params = self.params_builder.build(api_type, date, sub_type)

		try:
			data = self.api.get(self.endpoint, params)

			total_count = data['response']['body']['totalCount']
			num_of_rows = params['numOfRows']
			total_pages = -(-total_count // num_of_rows)

			self.loggers["application"].day(f'{self.collection_name} - {date} - 전체 데이터 수: {total_count}')
			self.loggers["day"].day(f'{self.collection_name} - {date} - 전체 데이터 수: {total_count}')

			if collect_bids:
				try:
					db_date_count = bid_counter_by_date[f"{date[:4]}-{date[4:6]}-{date[6:]}"]
				except KeyError:
					db_date_count = 0

				# ±5%까지 허용하도록...
				margin_rate = 0.05
				if abs(db_date_count - total_count) <= total_count * margin_rate:
					self.loggers["application"].verify(
						f'{date} - 데이터 개수 차이 5% 내외 - API:{total_count} | DB:{db_date_count} PASSED')
					return None
				else:
					self.loggers["application"].verify(
						f'{date} - 데이터 개수 불일치 - API:{total_count} | DB:{db_date_count} - CONTINUE')

			total_success, total_insert, total_update, total_failed = 0, 0, 0, 0

			for page in range(1, total_pages + 1):
				page_insert_count = 0
				page_update_count = 0

				params['pageNo'] = page
				data = self.api.get(self.endpoint, params)

				items = data['response']['body']['items']
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
				self.loggers['application'].fetch(
					f"{date} - {page}/{total_pages} 페이지 처리완료: {success_count}({page_insert_count}+{page_update_count})건")

			self.loggers["application"].day(
				f"{self.collection_name} - {date} - 최종 저장 건수: {total_success}({total_insert}+{total_update})")
			self.loggers["day"].day(
				f"{self.collection_name} - {date} - 최종 저장 건수: {total_success}({total_insert}+{total_update})")
			return total_success


		except Exception as e:
			self.loggers["application"].error(f"{self.collection_name} - {date} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			self.loggers["error"].error(f"{self.collection_name} - {date} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			raise

	def collect_all_data_by_day(self, start_date: str, end_date: str) -> None:
		# 투찰 데이터 수집인지?
		collect_bids: bool = (self.collection_name == "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보")

		date_list = list(generate_dates(start_date, end_date))
		self.loggers["application"].info(f"{start_date} ~ {end_date} 내 데이터를 모두 가져옵니다.")

		bid_counter_by_date = self.count_data_by_date(start_date, end_date) if collect_bids else None

		pending_dates = date_list
		attempt = 1

		while pending_dates:
			# 이번시도에서 실패한 날짜 기록
			error_dates: list[str] = []

			for date in pending_dates:
				try:
					self.collect_data_by_day(date, collect_bids, bid_counter_by_date=bid_counter_by_date)
				except Exception as e:
					self.loggers["error"].error(f"{self.collection_name} - {date} - 수집 실패: {str(e)}")
					self.recorder.append(date, "error_date.txt")
					error_dates.append(date)

			if not error_dates:
				self.loggers["application"].info("🎉 모든 데이터가 성공적으로 수집되었습니다.")
				break

			# 에러가 발생한 날짜들에 대해 다시 시도
			self.loggers["application"].warning(f"⚠️ [Attempt {attempt}] {len(error_dates)}개의 날짜에서 오류 발생. 재시도 진행.")
			pending_dates = error_dates  # 에러 발생한 날짜들만 다시 시도
			attempt += 1  # 다음 반복을 위해 시도 횟수 증가

	def collect_bids_by_NtceNo(self, NtceNo: str):
		try:
			# 1) 파라미터 준비 (ParamsBuilder 내부 기본값 활용)
			params = self.params_builder.params_list["bid"].copy()
			params["bidNtceNo"] = NtceNo

			# 2) 첫 페이지 호출 → 전체 건수 파악
			data = self.api.get(self.endpoint, params)
			total_count = data["response"]["body"]["totalCount"]
			num_rows = params["numOfRows"]
			total_pages = -(-total_count // num_rows)  # ceiling division

			self.loggers["application"].day(f"{self.collection_name} - {NtceNo} - 전체 데이터 수: {total_count}")
			self.loggers["day"].day(f"{self.collection_name} - {NtceNo} - 전체 데이터 수: {total_count}")

			total_success = total_insert = total_update = total_failed = 0

			# 3) 페이지 루프
			for page in range(1, total_pages + 1):
				page_insert_count = page_update_count = 0

				params["pageNo"] = page
				data = self.api.get(self.endpoint, params)

				items = data["response"]["body"]["items"]
				if isinstance(items, dict):
					items = [items]

				for item in items:
					item["collected_at"] = datetime.now()
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
					f"{self.collection_name} - {page}/{total_pages} 페이지 처리완료: "
					f"{success_count}({page_insert_count}+{page_update_count})건"
				)

			# 4) 최종 요약 로그
			self.loggers["application"].day(
				f"{self.collection_name} - {NtceNo} - 최종 저장 건수: "
				f"{total_success}({total_insert}+{total_update})"
			)
			self.loggers["day"].day(
				f"{self.collection_name} - {NtceNo} - 최종 저장 건수: "
				f"{total_success}({total_insert}+{total_update})"
			)
			return total_success

		except Exception as e:
			self.loggers["application"].error(
				f"{self.collection_name} - {NtceNo} - 처리 중 오류 발생: {e}", exc_info=True
			)
			self.loggers["error"].error(
				f"{self.collection_name} - {NtceNo} - 처리 중 오류 발생: {e}", exc_info=True
			)
			raise

	def get_notice_number_list(self):
		collection = self.db.get_collection("낙찰정보서비스.낙찰된목록현황공사조회")
		result = collection.find({}, {"bidNtceNo": 1, "_id": 0})

		result = [doc['bidNtceNo'] for doc in result]

		return result

	def collect_all_bids_by_NtceNo(self):

		collection_notices = self.db.get_collection("낙찰정보서비스.낙찰된목록현황공사조회")

		# 1. bids_info_is_collected=False인 공고번호만 가져오기
		notice_number_list = [
			doc["bidNtceNo"]
			for doc in collection_notices.find(
				{"bids_info_is_collected": False},
				{"bidNtceNo": 1, "_id": 0}
			)
		]

		if not notice_number_list:
			self.loggers["application"].info("✅ 수집할 공고가 없습니다.")
			return

		self.loggers["application"].info(f"{notice_number_list[0]} ~ {notice_number_list[-1]} 내 데이터를 모두 가져옵니다.")

		pending_notices = notice_number_list
		attempt = 1

		while pending_notices:
			# 이번시도에서 실패한 공고번호 기록
			error_notices = []
			for notice_number in pending_notices:
				try:
					result = self.collect_bids_by_NtceNo(notice_number)
					self.recorder.append(notice_number, "fetched_notice.txt")

					# 수집이 완료되면 해당 공고의 bids_info_is_collected를 True로 업데이트
					collection_notices.update_one(
						{"bidNtceNo": notice_number},
						{"$set": {"bids_info_is_collected": True}}
					)

				except Exception as e:
					self.loggers["error"].error(f"{self.collection_name} - {notice_number} - 수집 실패: {str(e)}")
					self.recorder.append(notice_number, "error_notice.txt")
					error_notices.append(notice_number)

			if not error_notices:
				self.loggers["application"].info("🎉 모든 데이터가 성공적으로 수집되었습니다.")
				break

			# 에러가 발생한 날짜들에 대해 다시 시도
			self.loggers["application"].warning(f"⚠️ [{attempt}차 시도] {len(error_notices)}개의 날짜에서 오류 발생. 재시도 진행.")
			pending_notices = error_notices  # 에러 발생한 날짜들만 다시 시도
			attempt += 1  # 다음 반복을 위해 시도 횟수 증가

	def count_data_by_date(self, start_date: str, end_date: str) -> dict:
		pipeline = []

		# 투찰데이터 수집의 경우
		if self.collection_name == "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보":
			date_field_name = "opengDate"

			pipeline = [
				{
					"$match": {
						date_field_name: {
							"$gte": start_date,
							"$lte": end_date
						}
					}
				},
				{
					"$group": {
						"_id": f"${date_field_name}",
						"count": {"$sum": 1}
					}
				},
				{
					"$sort": {"_id": 1}
				}
			]

		# 공고 기초금액 관련 데이터 수집의 경우
		elif self.collection_name == "입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회":
			date_field_name = "bssamtOpenDt"
		elif self.collection_name == "입찰공고정보서비스.입찰공고목록정보에대한공사조회":
			date_field_name = "rgstDt"

		result = list(self.mongo.collection.aggregate(pipeline))
		return {item['_id']: item['count'] for item in result}

	def execute(self):
		# 특정년도 수집
		if self.executed_year:
			start_date = f'{self.executed_year}-01-01'
			end_date = f'{self.executed_year}-12-31'
			self.collect_all_data_by_day(start_date, end_date)

		# 전체수집
		else:
			if self.service_name == "낙찰정보서비스" and self.operation_number == 13:
				self.collect_all_bids_by_NtceNo()
			else:
				start_date = '2010-01-01'
				end_date = '2024-12-31'
				self.collect_all_data_by_day(start_date, end_date)
