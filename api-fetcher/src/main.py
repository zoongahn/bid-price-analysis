from data_collector import DataCollector


def input_handler():
	service_name_list={
		1:"입찰공고정보서비스",
		2:"낙찰정보서비스",
		3:"사용자정보서비스",
		4:"공공데이터개방표준서비스",
		5:"계약정보표준서비스"
	}
	

if __name__ == '__main__':
	start_date = '2010-01-01'
	end_date = '2025-03-04'

	service_name = '입찰공고정보서비스'
	operation_number = 1

	collector = DataCollector(service_name, operation_number)
	collector.collect_all_data(start_date, end_date)
