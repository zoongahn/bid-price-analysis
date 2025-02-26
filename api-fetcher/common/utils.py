import csv
import os
from datetime import datetime, timedelta


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


def save_fetched_date(date_str: str, error: bool = False):
	"""
	새로 처리한 날짜를 파일에 한 줄씩 기록
	"""
	dir_path = os.path.join(get_project_root(), "date_record")
	os.makedirs(dir_path, exist_ok=True)

	file_path = os.path.join(dir_path, "fetched_date.txt" if not error else "error_date.txt")
	with open(file_path, "a", encoding="utf-8") as f:
		f.write(date_str + "\n")


def parse_csv_to_listdict(csv_file_path):
	result = []
	with open(csv_file_path, 'r', encoding='utf-8-sig') as f:
		reader = csv.DictReader(f)
		for row in reader:
			# DictReader가 헤더를 기준으로 컬럼명:값 매핑
			# 필요하다면 컬럼명 변환/trim 처리 가능
			result.append(dict(row))
	return result
