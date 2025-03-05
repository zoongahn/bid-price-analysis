from data_collector import DataCollector

if __name__ == '__main__':
	start_date = '2010-01-01'
	end_date = '2024-12-31'

	service_name = '입찰공고정보서비스'
	operation_number = 1

	collector = DataCollector(service_name, operation_number)
	collector.collect_all_data(start_date, end_date)
