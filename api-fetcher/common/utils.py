import csv
import os
from datetime import datetime, timedelta

from common.init_mongodb import *


def get_project_root():
	return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


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


def load_date_record(file_name: str):
	"""
	이미 처리된 날짜(YYYY-MM-DD 문자열)를 저장한 파일을 읽어와 set으로 반환
	파일이 없거나 비어있으면 빈 set 반환
	"""
	file_path = os.path.join(get_project_root(), "date_record", file_name)
	try:
		with open(file_path, "r", encoding="utf-8") as f:
			return set(line.strip() for line in f if line.strip())
	except FileNotFoundError:
		return set()


def parse_csv_to_listdict(csv_file_path):
	result = []
	with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
		reader = csv.DictReader(f)
		for row in reader:
			# DictReader가 헤더를 기준으로 컬럼명:값 매핑
			# 필요하다면 컬럼명 변환/trim 처리 가능
			result.append(dict(row))
	return result


def get_service_info(service_name: str, operation_number: int):
	server, client = None, None

	if os.getenv("DJANGO_ENV") == "local":
		server, client = connect_mongodb_via_ssh()
	else:
		client = init_mongodb()

	db = client.get_database("gfcon")

	collection = db["api_list"]

	# Aggregation Pipeline 사용
	pipeline = [
		{"$match": {"service_name": service_name}},  # service_name이 일치하는 문서 조회
		{
			"$project": {
				"_id": 0,  # _id 필드 제외 (선택 사항)
				"service_name": 1,
				"service_endpoint": 1,
				"filtered_operations": {
					"$filter": {
						"input": "$operations",  # operations 배열을 필터링
						"as": "operation",
						"cond": {"$eq": ["$$operation.일련번호", str(operation_number)]}  # 일련번호(n) 필터
					}
				}
			}
		}
	]

	# MongoDB에서 쿼리 실행
	result = list(collection.aggregate(pipeline))[0]

	return result
