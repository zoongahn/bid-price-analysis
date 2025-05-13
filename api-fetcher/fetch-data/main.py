import argparse
from src.data_collector import DataCollector

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="데이터 수집용 스크립트")
	parser.add_argument('--service', type=str, help='수집할 서비스명')
	parser.add_argument('--oper', type=int, help='수집할 오퍼레이션 일련번호')
	parser.add_argument('--year', type=str, help='수집할 연도 (예: 2012)')

	args = parser.parse_args()

	collector = DataCollector(args.service, args.oper, args.year)
	collector.execute()
