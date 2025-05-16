from typing import Any
from tqdm import tqdm

from common.logger import setup_loggers
from common.utils import *
from common.init_mongodb import *

from .api_client import ApiClient
from .mongo_writer import MongoWriter
from .params_builder import ParamsBuilder
from .record_writer import RecordWriter


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
		self.api = ApiClient(self.API_BASE_DOMAIN)
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

	def collect_data_by_code(self, params: dict, code: str):
		try:
			data = self.api.get(self.endpoint, params)

			total_count = data['response']['body']['totalCount']
			num_of_rows = params['numOfRows']
			total_pages = -(-total_count // num_of_rows)

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

			return total_success

		except Exception as e:
			self.loggers["application"].error(f"{self.collection_name} - {code} - 처리 중 오류 발생: {str(e)}",
			                                  exc_info=True)
			self.loggers["error"].error(f"{self.collection_name} - {code} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			raise

	def collect_notice_by_NtceNo(self, NtceNo_list: list[str]) -> None:
		for NtceNo in tqdm(NtceNo_list, total=len(NtceNo_list)):
			params = {
				"serviceKey": self.API_SERVICE_KEY,
				"pageNo": 1,
				"numOfRows": 100,
				"inqryDiv": 2,
				"type": "json",
				"bidNtceNo": NtceNo
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
				"type": "json"
			}

			self.collect_data_by_code(params, code=bizno)

	def get_notice_number_list(self):
		collection = self.db.get_collection("낙찰정보서비스.낙찰된목록현황공사조회")
		result = collection.find({}, {"bidNtceNo": 1, "_id": 0})

		result = [doc['bidNtceNo'] for doc in result]

		return result

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
			start_date = '2001-01-01'
			end_date = '2009-12-31'
			self.collect_all_data_by_day(start_date, end_date)
