from src.data_collector import DataCollector
from src.download_methods import input_handler

start_date = '2010-01-01'
end_date = '2025-03-04'

service_name, operation_number = input_handler()

collector = DataCollector(service_name, operation_number)
collector.collect_data_by_day("20160101")
