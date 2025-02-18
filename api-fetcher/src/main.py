import configparser
import ssl
import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager
from pymongo import MongoClient
from datetime import datetime, timedelta
import logging
import colorlog


# 로깅
def setup_logger(log_file="application.log", log_level=logging.INFO):
	# 기존 root logger의 핸들러 제거 (중복 방지)
	logging.getLogger().handlers = []

	# 1) 콘솔 로그 설정 (colorlog 사용)
	log_format_console = "%(log_color)s[%(levelname)s] %(asctime)s - %(message)s"
	console_handler = colorlog.StreamHandler()
	console_formatter = colorlog.ColoredFormatter(
		log_format_console,
		datefmt="%Y-%m-%d %H:%M:%S",
		log_colors={
			"DEBUG": "cyan",
			"INFO": "green",
			"WARNING": "yellow",
			"ERROR": "red",
			"CRITICAL": "bold_red"
		}
	)
	console_handler.setFormatter(console_formatter)
	console_handler.setLevel(log_level)

	# 2) 파일 로그 설정 (일반 텍스트로 저장)
	log_format_file = "[%(levelname)s] %(asctime)s - %(message)s"
	file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
	file_formatter = logging.Formatter(log_format_file, datefmt="%Y-%m-%d %H:%M:%S")
	file_handler.setFormatter(file_formatter)
	file_handler.setLevel(log_level)

	# 3) 루트 로거에 두 개의 핸들러(콘솔, 파일)를 연결
	logging.getLogger().setLevel(log_level)
	logging.getLogger().addHandler(console_handler)
	logging.getLogger().addHandler(file_handler)


log_format = "%(log_color)s[%(levelname)s] %(asctime)s - %(message)s"
logging.basicConfig(level=logging.INFO, format=log_format)


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


# 2) 날짜 반복 함수 -----------------------------------------------------------
def generate_dates(start_date_str, end_date_str, input_date_format="%Y-%m-%d", output_date_format="%Y%m%d"):
	"""
	시작일 ~ 종료일 범위를 일(day) 단위로 순회하며 날짜 객체를 yield하는 함수
	예: start_date_str="2010-01-01", end_date_str="2024-12-31"
	"""
	start_date = datetime.strptime(start_date_str, input_date_format).date()
	end_date = datetime.strptime(end_date_str, input_date_format).date()

	current_date = start_date
	while current_date <= end_date:
		yield current_date.strftime(output_date_format)
		current_date += timedelta(days=1)


# 3) 파일 입출력 함수 (이미 처리한 날짜) -------------------------------------
def load_fetched_date(file_path: str):
	"""
	이미 처리된 날짜(YYYY-MM-DD 문자열)를 저장한 파일을 읽어와 set으로 반환
	파일이 없거나 비어있으면 빈 set 반환
	"""
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			return set(line.strip() for line in f if line.strip())
	except FileNotFoundError:
		return set()


def save_fetched_date(file_path: str, date_str: str):
	"""
	새로 처리한 날짜를 파일에 한 줄씩 기록
	"""
	with open(file_path, "a", encoding="utf-8") as f:
		f.write(date_str + "\n")


# 4) 실제 데이터 수집 -------------------------------------------------
class DataCollector:
	def __init__(self):
		self.config = configparser.RawConfigParser()
		self.config.read('../config.ini')

		db_host = self.config['database']['host']
		db_port = self.config.getint('database', 'port')
		db_user = self.config['database']['username']
		db_pass = self.config['database']['password']
		db_name = self.config['database']['db']

		self.api_base_domain = self.config['api']['base_domain']
		self.api_key = self.config['api']['service_key']

		self.client = MongoClient(f"mongodb://{db_user}:{db_pass}@{db_host}:{db_port}")
		self.db = self.client.get_database(db_name)

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

	def collect_data_for_endpoint(self, endpoint_key: str, date: str) -> int:
		# date should be like "%Y%m%d" (ex. 20230101)
		endpoint = self.endpoints[endpoint_key]
		url = self.api_base_domain + endpoint['url']
		collection = self.db[endpoint_key]
		# datetime_format = '%Y%m%d%H%M'
		start_datetime = date + '0000'
		end_datetime = date + '2359'
		try:
			params = {
				'serviceKey': self.api_key,
				'pageNo': 1,
				'numOfRows': 100,
				'inqryDiv': 1,
				'inqryBgnDt': start_datetime,
				'type': 'json',
				'inqryEndDt': end_datetime
			}

			response = self.session.get(url, params=params)

			print(response.request.url)

			data = response.json()

			total_count = data['response']['body']['totalCount']
			num_of_rows = params['numOfRows']
			total_pages = -(-total_count // num_of_rows)

			logging.info(f'{endpoint_key} - {date} - 전체 데이터 수: {total_count}')

			total_success = 0
			total_failed = 0
			api_bid_numbers = set()
			duplicate_check = set()

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
							bid_number_attr = 'bidNtceNo'
							bid_number = item[bid_number_attr]

							# 중복 document
							if bid_number in duplicate_check:
								continue

							duplicate_check.add(bid_number)
							api_bid_numbers.add(bid_number)

							item['bidType'] = endpoint['type']
							item['collected_at'] = datetime.now()

							query = {bid_number_attr: bid_number}
							collection.update_one(query, {'$set': item}, upsert=True)
							success_count += 1

						except Exception as e:
							logging.error(f'저장 실패: {bid_number}, 에러: {e}')
							total_failed += 1

					total_success += success_count
					logging.info(f"{endpoint_key} - {page}/{total_pages} 페이지 처리완료: {success_count}건")

			logging.info(f"{endpoint_key} - 최종 저장 건수: {total_success}")
			return total_success

		except Exception as e:
			logging.error(f"{endpoint_key} 처리 중 오류 발생: {str(e)}", exc_info=True)
			raise

	def collect_all_data(self):
		total_results = {}
		endpoint_key = 'construction'

		start_date = '2010-01-01'
		end_date = '2024-12-31'

		date_list = generate_dates(start_date, end_date)

		for date in date_list:
			try:
				result = self.collect_data_for_endpoint(endpoint_key, date)
				save_fetched_date('../fetched_date.txt', date)
				total_results[date] = result
			except Exception as e:
				logging.error(f"{endpoint_key} - {date} - 수집 실패: {str(e)}")
				save_fetched_date('../error_date.txt', date)
				total_results[endpoint_key] = 0

		logging.info("=== 전체 수집 결과 ===")
		for key, value in total_results.items():
			logging.info(f"{key}: {value}건")

		return total_results


# 5) 메인 실행 --------------------------------------
def run_scheduler():
	logging.info("작업 시작")
	collector = DataCollector()
	collector.collect_all_data()
	logging.info("작업 완료")


if __name__ == '__main__':
	setup_logger()
	run_scheduler()
