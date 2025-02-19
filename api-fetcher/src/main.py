from data_collector import DataCollector

if __name__ == '__main__':
	start_year = 2010
	end_year = 2024

	collector = DataCollector()
	collector.collect_all_data(start_year, end_year)
