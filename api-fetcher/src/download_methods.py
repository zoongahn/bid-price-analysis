from common.utils import *
from data_collector import DataCollector


def input_handler():
	service_name_list = {
		1: "입찰공고정보서비스",
		2: "낙찰정보서비스",
		3: "사용자정보서비스",
		4: "공공데이터개방표준서비스",
		5: "계약정보표준서비스"
	}

	for k, v in service_name_list.items():
		print(f"{k}. {v}")
	service_name = service_name_list[int(input("서비스명: "))]
	operation_number = int(input("오퍼레이션 일련번호: "))

	operation_name = get_service_info(service_name, operation_number)["filtered_operations"][0]["오퍼레이션명(국문)"]

	while True:
		print(f"서비스명: {service_name} / 오퍼레이션명: {operation_name}")
		user_input = input("다음 API를 가져오시려면 ENTER (or 'exit'):")
		if user_input == "":
			break
		elif user_input == "exit":
			exit()

	return service_name, operation_number


def get_data_in_full_range():
	start_date = '2010-01-01'
	end_date = '2025-03-04'

	service_name, operation_number = input_handler()

	collector = DataCollector(service_name, operation_number)
	collector.collect_all_data(start_date, end_date)


def get_data_by_date_file(txt_file_name: str):
	date_set = sorted(list(load_fetched_date(txt_file_name)))
	service_name, operation_number = input_handler()
	collector = DataCollector(service_name, operation_number)

	error_date_list = []

	for date in date_set:
		try:
			collector.collect_data_by_day(date)
		except Exception as e:
			error_date_list.append(date)
			print(f"Error: {e}")

	if len(error_date_list) > 0:
		for date in error_date_list:
			collector.record_txt(date, "get_data_by_date_file__error_date.txt")
	else:
		print("All data has been collected.")
