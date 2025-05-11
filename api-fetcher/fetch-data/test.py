from data_collector import DataCollector

data_collector = DataCollector("낙찰정보서비스", 10, "2022")
data_collector.collect_data_by_day(date="20221209")
