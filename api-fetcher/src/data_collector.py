import ssl
import time
from itertools import count
from typing import Any

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


class DataCollector:
	def __init__(self, service_name: str | None = None, operation_number: str | int | None = None):

		self.service_name, self.operation_number = service_name, operation_number

		if service_name is None and operation_number is None:
			self.service_name, self.operation_number = input_handler()

		self.server, self.client = init_mongodb()

		self.API_BASE_DOMAIN = os.getenv("API_BASE_DOMAIN")
		self.API_SERVICE_KEY = os.getenv("API_SERVICE_KEY")

		# 1) SSLContext 생성
		ssl_ctx = ssl.create_default_context()
		# 2) TLS 1.3 비활성 → TLS 1.2 이하
		ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
		# 3) "보안 레벨"을 1로 낮추어, 구버전 Cipher까지 허용
		ssl_ctx.set_ciphers("DEFAULT:@SECLEVEL=1")

		self.session = requests.Session()
		self.session.mount("https://", SSLContextAdapter(ssl_context=ssl_ctx))

		service_info = get_service_info(service_name=self.service_name, operation_number=self.operation_number)

		service_endpoint = service_info["service_endpoint"]
		operation_info = service_info["filtered_operations"][0]
		operation_endpoint = operation_info["오퍼레이션명(영문)"]
		self.collection_name = operation_info["raw_data_collection_name"]

		self.url = f"{self.API_BASE_DOMAIN}/{service_endpoint}/{operation_endpoint}"

		self.db = self.client.get_database("gfcon_raw")

		self.collection = self.db[self.collection_name]

		self.loggers = setup_loggers()

		self.unique_fields = operation_info["unique_fields"]

		self.params_list = {
			"notice": {
				'serviceKey': self.API_SERVICE_KEY,
				'pageNo': 1,
				'numOfRows': 100,
				'inqryDiv': 1,
				'type': 'json',
				'inqryBgnDt': None,
				'inqryEndDt': None
			},
			"bid": {
				'serviceKey': self.API_SERVICE_KEY,
				'pageNo': 1,
				'numOfRows': 100,
				'type': 'json',
				'bidNtceNo': None,
			},
			"pubData": {
				1: {
					'serviceKey': self.API_SERVICE_KEY,
					'pageNo': 1,
					'numOfRows': 100,
					'type': 'json',
					'bsnsDivCd': None,
					'bidNtceBgnDt': None,
					'bidNtceEndDt': None,
				},
				2: {
					'serviceKey': self.API_SERVICE_KEY,
					'pageNo': 1,
					'numOfRows': 500,
					'type': 'json',
					'bsnsDivCd': 3,
					'opengBgnDt': None,
					'opengEndDt': None,
				},
				3: {
					'serviceKey': self.API_SERVICE_KEY,
					'pageNo': 1,
					'numOfRows': 100,
					'type': 'json',
					'cntrctCnclsBgnDate': None,
					'cntrctCnclsEndDate': None,
				}
			}
		}

		self.date_field_map = {
			"notice": ["inqryBgnDt", "inqryEndDt"],
			"bid": [],  # 날짜필드 없음
			"pubData": {
				1: ["bidNtceBgnDt", "bidNtceEndDt"],
				2: ["opengBgnDt", "opengEndDt"],
				3: ["cntrctCnclsBgnDate", "cntrctCnclsEndDate"]
			}
		}

	def set_date_params(self, api_type: str, params: dict, sub_type: int = None, date: str = ""):
		start = date + "0000"
		end = date + "2359"

		if api_type == "pubData":
			fields = self.date_field_map[api_type][sub_type]
		else:
			fields = self.date_field_map[api_type]

		for i, key in enumerate(fields):
			params[key] = start if i == 0 else end

		return params

	def record_txt(self, record_str: str, txt_file_name):
		"""
		새로 처리한 날짜를 파일에 한 줄씩 기록
		"""
		root_dir_path = os.path.join(get_project_root(), "fetch_record")
		os.makedirs(root_dir_path, exist_ok=True)

		collection_name_dir_path = os.path.join(root_dir_path, self.collection_name)
		os.makedirs(collection_name_dir_path, exist_ok=True)

		file_path = os.path.join(collection_name_dir_path, txt_file_name)
		with open(file_path, "a", encoding="utf-8") as f:
			f.write(record_str + "\n")

	def get_json_with_retry(self, url, params, date, retry_interval=10):
		from requests.exceptions import JSONDecodeError, ConnectionError

		def error_handler(e: str, interval: int):
			self.loggers["application"].error(
				f'{date} - {e} 발생, {interval}초 후 재시도 중...')
			self.loggers["error"].error(
				f'{date} - {e} 발생, {interval}초 후 재시도 중...')
			time.sleep(interval)

		while True:
			try:
				response = self.session.get(url, params=params)
				try:
					return response.json()
				except JSONDecodeError:
					error_handler("JSONDecodeError", interval=retry_interval)
				except ConnectionError:
					error_handler("ConnectionError", interval=retry_interval)
			except Exception as e:
				self.loggers["application"].error(
					f"{self.collection_name} - 요청 중 오류 발생: {str(e)}", exc_info=True)
				self.loggers["error"].error(
					f"{self.collection_name} - 요청 중 오류 발생: {str(e)}", exc_info=True)
				raise

	# 공고 데이터 및 기업 데이터 수집에 사용
	def collect_data_by_day(self, date: str, collect_bids: bool = False,
	                        bid_counter_by_date: dict | None = None) -> int | None | Any:

		if self.service_name == "공공데이터개방표준서비스":
			api_type = "pubData"
			sub_type = self.operation_number
			params = self.params_list[api_type][sub_type].copy()
		else:
			api_type = "notice"
			sub_type = None
			params = self.params_list[api_type].copy()

		# 날짜 필드 자동 설정
		params = self.set_date_params(api_type, params, sub_type=sub_type, date=date)

		try:
			data = self.get_json_with_retry(self.url, params)

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

			total_success = 0
			total_insert = 0
			total_update = 0
			total_failed = 0

			for page in range(1, total_pages + 1):
				page_insert_count = 0
				page_update_count = 0

				params['pageNo'] = page
				data = self.get_json_with_retry(self.url, params, date)

				if 'response' in data:
					items = data['response']['body']['items']
					if isinstance(items, dict):
						items = [items]

					success_count = 0
					for item in items:
						try:
							item['collected_at'] = datetime.now()

							# 먼저 insert를 시도, 중복되면 update 수행
							try:
								self.collection.insert_one(item)  # 새로운 데이터 삽입
								page_insert_count += 1
							except DuplicateKeyError:
								# 중복된 경우 update 수행
								item.pop("_id", None)

								update_query = {}
								for uf in self.unique_fields:
									update_query[uf] = item[uf]

								self.collection.update_one(
									update_query,
									{"$set": item}
								)
								page_update_count += 1

						except Exception as e:
							self.loggers["application"].error(
								f'저장 실패: {item["bidNtceNo"]} - {item["bidNtceOrd"]}, 에러: {e}')
							self.loggers["error"].error(f'저장 실패: {item["bidNtceNo"]} - {item["bidNtceOrd"]}, 에러: {e}')
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

	def collect_all_data_by_day(self, start_date: str, end_date: str):
		# 투찰 데이터 수집인지?
		collect_bids: bool = (self.collection_name == "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보")

		# 유니크 인덱스 설정
		unique_fields_query: list[tuple] = []  # Like [("bidNtceNo", 1), ("bidNtceOrd", 1)]
		for uf in self.unique_fields:
			unique_fields_query.append(tuple([uf, 1]))

		# 복합 인덱스 생성 (이미 존재하면 무시됨)
		self.collection.create_index(unique_fields_query, unique=True)

		date_list = list(generate_dates(start_date, end_date))

		self.loggers["application"].info(f"{start_date} ~ {end_date} 내 데이터를 모두 가져옵니다.")

		bid_counter_by_date = self.count_by_openg_date() if collect_bids else None

		pending_dates = date_list

		attempt = 1

		while pending_dates:
			# 이번시도에서 실패한 날짜 기록
			error_dates = []
			for date in pending_dates:
				try:
					result = self.collect_data_by_day(date, collect_bids, bid_counter_by_date=bid_counter_by_date)
					self.record_txt(date, "fetched_date.txt")
				except Exception as e:
					self.loggers["error"].error(f"{self.collection_name} - {date} - 수집 실패: {str(e)}")
					self.record_txt(date, "error_date.txt")
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
			params = self.params_list["bid"]
			params["bidNtceNo"] = NtceNo

			response = self.session.get(self.url, params=params)

			data = response.json()

			total_count = data['response']['body']['totalCount']
			num_of_rows = params['numOfRows']
			total_pages = -(-total_count // num_of_rows)

			self.loggers["application"].day(f'{self.collection_name} - {NtceNo} - 전체 데이터 수: {total_count}')
			self.loggers["day"].day(f'{self.collection_name} - {NtceNo} - 전체 데이터 수: {total_count}')

			total_success = 0
			total_insert = 0
			total_update = 0
			total_failed = 0

			for page in range(1, total_pages + 1):
				page_insert_count = 0
				page_update_count = 0

				params['pageNo'] = page
				response = self.session.get(self.url, params=params)
				data = response.json()

				if 'response' in data:
					items = data['response']['body']['items']
					if isinstance(items, dict):
						items = [items]

					success_count = 0
					for item in items:
						try:
							item['collected_at'] = datetime.now()

							# 먼저 insert를 시도, 중복되면 update 수행
							try:
								self.collection.insert_one(item)  # 새로운 데이터 삽입
								page_insert_count += 1
							except DuplicateKeyError:
								# 중복된 경우 update 수행
								item.pop("_id", None)

								update_query = {}
								for uf in self.unique_fields:
									update_query[uf] = item[uf]

								self.collection.update_one(
									update_query,
									{"$set": item}
								)
								page_update_count += 1

						except Exception as e:
							self.loggers["application"].error(
								f'저장 실패: {item["bidNtceNo"]} - {item["prcbdrBizno"]}, 에러: {e}')
							self.loggers["error"].error(f'저장 실패: {item["bidNtceNo"]} - {item["prcbdrBizno"]}, 에러: {e}')
							total_failed += 1

					success_count = page_insert_count + page_update_count
					total_insert += page_insert_count
					total_update += page_update_count
					total_success += success_count
					self.loggers['application'].fetch(
						f"{self.collection_name} - {page}/{total_pages} 페이지 처리완료: {success_count}({page_insert_count}+{page_update_count})건")

			self.loggers["application"].day(
				f"{self.collection_name} - {NtceNo} - 최종 저장 건수: {total_success}({total_insert}+{total_update})")
			self.loggers["day"].day(
				f"{self.collection_name} - {NtceNo} - 최종 저장 건수: {total_success}({total_insert}+{total_update})")
			return total_success

		except Exception as e:
			self.loggers["application"].error(f"{self.collection_name} - {NtceNo} - 처리 중 오류 발생: {str(e)}",
			                                  exc_info=True)
			self.loggers["error"].error(f"{self.collection_name} - {NtceNo} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			raise

	def get_notice_number_list(self):
		db = self.client.get_database("gfcon_raw")
		collection = db.get_collection("낙찰정보서비스.낙찰된목록현황공사조회")
		result = collection.find({}, {"bidNtceNo": 1, "_id": 0})

		result = [doc['bidNtceNo'] for doc in result]

		return result

	def collect_all_bids_by_NtceNo(self):

		unique_fields_query: list[tuple] = []  # Like [("bidNtceNo", 1), ("bidNtceOrd", 1)]
		for uf in self.unique_fields:
			unique_fields_query.append(tuple([uf, 1]))

		# 복합 인덱스 생성 (이미 존재하면 무시됨)
		self.collection.create_index(unique_fields_query, unique=True)

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
					self.record_txt(notice_number, "fetched_notice.txt")

					# 수집이 완료되면 해당 공고의 bids_info_is_collected를 True로 업데이트
					collection_notices.update_one(
						{"bidNtceNo": notice_number},
						{"$set": {"bids_info_is_collected": True}}
					)

				except Exception as e:
					self.loggers["error"].error(f"{self.collection_name} - {notice_number} - 수집 실패: {str(e)}")
					self.record_txt(notice_number, "error_notice.txt")
					error_notices.append(notice_number)

			if not error_notices:
				self.loggers["application"].info("🎉 모든 데이터가 성공적으로 수집되었습니다.")
				break

			# 에러가 발생한 날짜들에 대해 다시 시도
			self.loggers["application"].warning(f"⚠️ [{attempt}차 시도] {len(error_notices)}개의 날짜에서 오류 발생. 재시도 진행.")
			pending_notices = error_notices  # 에러 발생한 날짜들만 다시 시도
			attempt += 1  # 다음 반복을 위해 시도 횟수 증가

	def count_by_openg_date(self) -> dict:
		pipeline = [
			{
				"$group": {
					"_id": "$opengDate",
					"count": {"$sum": 1}
				}
			},
			{
				"$sort": {"_id": 1}
			}
		]

		result = list(self.collection.aggregate(pipeline))
		return {item['_id']: item['count'] for item in result}

	def execute(self):
		if self.service_name == "낙찰정보서비스" and self.operation_number == 13:
			self.collect_all_bids_by_NtceNo()
		else:
			start_date = '2010-01-04'
			end_date = '2010-01-04'
			self.collect_all_data_by_day(start_date, end_date)
