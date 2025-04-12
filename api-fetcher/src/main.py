import argparse
from data_collector import DataCollector

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="데이터 수집용 스크립트")
	parser.add_argument('--year', type=str, help='수집할 연도 (예: 2012)')

	args = parser.parse_args()

	collector = DataCollector("공공데이터개방표준서비스", 2)

	if args.year:
		# 년도별 수집
		collector.execute_by_year(args.year)
	else:
		# 전체 수집
		collector.execute()
