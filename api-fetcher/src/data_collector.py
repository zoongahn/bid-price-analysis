import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from urllib.parse import quote_plus
from pymongo import MongoClient
from dotenv import load_dotenv

from logger import setup_loggers
from utils import *


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
	def __init__(self):
		load_dotenv()

		DB_HOST = os.getenv("DB_HOST")
		DB_PORT = int(os.getenv("DB_PORT"))  # 기본값 설정 가능
		DB_USERNAME = quote_plus(os.getenv("DB_USERNAME"))
		DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
		DB_NAME = os.getenv("DB_NAME")

		self.API_BASE_DOMAIN = os.getenv("API_BASE_DOMAIN")
		self.API_SERVICE_KEY = os.getenv("API_SERVICE_KEY")

		self.client = MongoClient(f"mongodb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}")
		self.db = self.client.get_database(DB_NAME)

		# 1) SSLContext 생성
		ssl_ctx = ssl.create_default_context()
		# 2) TLS 1.3 비활성 → TLS 1.2 이하
		ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
		# 3) "보안 레벨"을 1로 낮추어, 구버전 Cipher까지 허용
		ssl_ctx.set_ciphers("DEFAULT:@SECLEVEL=1")

		self.session = requests.Session()
		self.session.mount("https://", SSLContextAdapter(ssl_context=ssl_ctx))

		self.endpoints = {
			'construction': {
				'url': '/getBidPblancListInfoCnstwk',
				'type': '공사',
				'description': '입찰공고목록 정보에 대한 공사조회'
			}
		}

		self.loggers = setup_loggers()

	def collect_data_by_day(self, endpoint_key: str, date: str) -> int:
		# date should be like "%Y%m%d" (ex. 20230101)
		endpoint = self.endpoints[endpoint_key]
		url = self.API_BASE_DOMAIN + endpoint['url']
		collection = self.db[endpoint_key]
		# datetime_format = '%Y%m%d%H%M'
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

			response = self.session.get(url, params=params)

			data = response.json()

			total_count = data['response']['body']['totalCount']
			num_of_rows = params['numOfRows']
			total_pages = -(-total_count // num_of_rows)

			self.loggers["application"].day(f'{endpoint_key} - {date} - 전체 데이터 수: {total_count}')
			self.loggers["day"].day(f'{endpoint_key} - {date} - 전체 데이터 수: {total_count}')

			total_success = 0
			total_failed = 0

			for page in range(1, total_pages + 1):
				params['pageNo'] = page
				response = self.session.get(url, params=params)
				data = response.json()

				if 'response' in data:
					items = data['response']['body']['items']
					if isinstance(items, dict):
						items = [items]

					success_count = 0
					for item in items:
						try:
							# 공고번호
							bid_number_attr = 'bidNtceNo'
							bid_number = item[bid_number_attr]

							item['bidType'] = endpoint['type']
							item['collected_at'] = datetime.now()

							collection.insert_one(item)
							success_count += 1

						except Exception as e:
							self.loggers["application"].error(f'저장 실패: {item['bidNtceNo']}, 에러: {e}')
							self.loggers["error"].error(f'저장 실패: {item['bidNtceNo']}, 에러: {e}')
							total_failed += 1

					total_success += success_count
					self.loggers['application'].fetch(
						f"{endpoint_key} - {page}/{total_pages} 페이지 처리완료: {success_count}건")

			self.loggers["application"].day(f"{endpoint_key} - {date} - 최종 저장 건수: {total_success}")
			self.loggers["day"].day(f"{endpoint_key} - {date} - 최종 저장 건수: {total_success}")
			return total_success

		except Exception as e:
			self.loggers["application"].error(f"{endpoint_key} - {date} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			self.loggers["error"].error(f"{endpoint_key} - {date} - 처리 중 오류 발생: {str(e)}", exc_info=True)
			raise

	def collect_data_by_year(self, year: str):
		# year should be like '2023'
		year_result = {}
		endpoint_key = 'construction'

		start_date = '2010-01-01'
		end_date = '2024-12-31'

		date_list = generate_dates(f'{year}-01-01', f'{year}-12-31')

		self.loggers["application"].year(f"===== {year}년도 데이터 수집 시작 =====")

		for date in date_list:
			try:
				result = self.collect_data_by_day(endpoint_key, date)
				save_fetched_date(date, error=False)
				year_result[date] = result
			except Exception as e:
				self.loggers["error"].error(f"{endpoint_key} - {date} - 수집 실패: {str(e)}")
				save_fetched_date(date, error=True)
				year_result[endpoint_key] = 0

		self.loggers["application"].info(f"===== {year}년도 데이터 수집 결과 =====")
		for key, value in year_result.items():
			self.loggers["application"].info(f"{key}: {value}건")

		return year_result

	def collect_all_data(self, start_year: int, end_year: int):

		for year in range(start_year, end_year + 1):
			self.collect_data_by_year(str(year))
			self.loggers["year"].year(f"========== YEAR={year} 데이터 수집 완료 ==========")
