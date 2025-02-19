from datetime import datetime, timedelta


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
