from common.utils import *
from data_collector import DataCollector


def get_data_in_full_date():
	start_date = '2010-01-01'
	end_date = '2025-03-04'

	collector = DataCollector()
	collector.collect_all_data_by_day(start_date, end_date)


def get_data_by_date_file(txt_file_name: str):
	date_set = sorted(list(load_date_record(txt_file_name)))

	collector = DataCollector()

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
