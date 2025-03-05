import ssl
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from pymongo.errors import DuplicateKeyError

from common.logger import setup_loggers
from common.utils import *
from common.init_mongodb import *


# 1) SSLContextAdapter (TLS 1.2 이하 강제 & 보안레벨 낮추기) ----------------
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


# 4) 실제 데이터 수집 -------------------------------------------------
class DataCollector:
	def __init__(self, service_name: str, operation_number: int):
		self.server, self.client = None, None

		if os.getenv("DJANGO_ENV") == "local":
			self.server, self.client = connect_mongodb_via_ssh()
		else:
			self.client = init_mongodb()

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

		self.operation_info = get_operation_info(service_name=service_name, operation_number=operation_number)
		self.coll_name = self.operation_info["raw_data_collection_name"]

		endpoint = self.operation_info["오퍼레이션명(영문)"]

		self.url = f"{self.API_BASE_DOMAIN}/{endpoint}"

		db = self.client.get_database("gfcon_raw")

		self.collection = db[self.coll_name]

		self.loggers = setup_loggers()

	def collect_data_by_day(self, date: str) -> int | None | Any:
		start_datetime = date + '0000'
		end_datetime = date + '2359'
		try:
			params = {
				'serviceKey': self.API_SERVICE_KEY,
				'pageNo': 1,
				'numOfRows': 100,
				'inqryDiv': 1,
				'inqryBgnDt': start_datetime,
				'type': 'json',
				'inqryEndDt': end_datetime
			}

			response = self.session.get(self.url, params=params)

			data = response.json()

			total_count = data['response']['body']['totalCount']
			num_of_rows = params['numOfRows']
			total_pages = -(-total_count // num_of_rows)

			self.loggers["application"].day(f'{self.coll_name} - {date} - 전체 데이터 수: {total_count}')
			self.loggers["day"].day(f'{self.coll_name} - {date} - 전체 데이터 수: {total_count}')

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
							# 공고번호 및 순번 필드명 정의
							bid_number_attr = 'bidNtceNo'
							bid_order_attr = 'bidNtceOrd'

							bid_number = item[bid_number_attr]
							bid_order = item[bid_order_attr]

							item['collected_at'] = datetime.now()

							# 먼저 insert를 시도, 중복되면 update 수행
							try:
								self.collection.insert_one(item)  # 새로운 데이터 삽입
								page_insert_count += 1
							except DuplicateKeyError:
								# 중복된 경우 update 수행
								item.pop("_id", None)
								self.collection.update_one(
									{bid_number_attr: bid_number, bid_order_attr: bid_order},
									{"$set": item}
								)
								record_txt(f"{bid_number} - {bid_order}", "duplicate_notices.txt")
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
						f"{self.coll_name} - {page}/{total_pages} 페이지 처리완료: {success_count}({page_insert_count}+{page_update_count})건")

			self.loggers["application"].day(
				f"{self.coll_name} - {date} - 최종 저장 건수: {total_success}({total_insert}+{total_update})")
			self.loggers["day"].day(
				f"{self.coll_name} - {date} - 최종 저장 건수: {total_success}({total_insert}+{total_update})")
			return total_success

		except Exception as e:
			self.loggers["application"].error(f"{self.coll_name} - {date} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			self.loggers["error"].error(f"{self.coll_name} - {date} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			raise

	def collect_all_data(self, start_date: str, end_date: str) -> dict:
		# 복합 인덱스 생성 (이미 존재하면 무시됨)
		self.collection.create_index([("bidNtceNo", 1), ("bidNtceOrd", 1)], unique=True)

		date_list = list(generate_dates(start_date, end_date))

		self.loggers["application"].info(f"{start_date} ~ {end_date} 내 데이터를 모두 가져옵니다.")

		for date in date_list:
			try:
				result = self.collect_data_by_day(date)
				record_txt(date, "fetched_date.txt")
			except Exception as e:
				self.loggers["error"].error(f"{self.coll_name} - {date} - 수집 실패: {str(e)}")
				record_txt(date, "error_date.txt")
