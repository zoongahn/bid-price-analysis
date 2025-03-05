from common.utils import get_operation_info
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

	return service_name, operation_number


if __name__ == '__main__':
	start_date = '2010-01-01'
	end_date = '2025-03-04'

	service_name, operation_number = input_handler()
	operation_name = get_operation_info(service_name, operation_number)["오퍼레이션명(국문)"]

	while True:
		print(f"서비스명: {service_name} / 오퍼레이션명: {operation_name}")
		user_input = input("다음 API를 가져오시려면 ENTER (or 'exit'):")
		if user_input == "":
			break
		elif user_input == "exit":
			exit()

	collector = DataCollector(service_name, operation_number)
	collector.collect_all_data(start_date, end_date)
