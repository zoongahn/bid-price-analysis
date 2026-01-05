import argparse
from src.data_collector import DataCollector

if __name__ == "__main__":
	parser = argparse.ArgumentParser(description="데이터 수집용 스크립트")
	parser.add_argument('--service', type=str, help='수집할 서비스명')
	parser.add_argument('--oper', type=int, help='수집할 오퍼레이션 일련번호')
	parser.add_argument('--year', type=str, help='수집할 연도 (예: 2012)')
	parser.add_argument('--start-date', type=str, help='수집 시작 날짜 (YYYY-MM-DD)')
	parser.add_argument('--end-date', type=str, help='수집 종료 날짜 (YYYY-MM-DD)')
	parser.add_argument(
		'--bsns-div',
		type=int,
		choices=[1, 2, 3, 5],
		default=3,
		help='사업구분코드: 1=물품, 2=외자, 3=공사(기본값), 5=용역'
	)

	args = parser.parse_args()

	collector = DataCollector(
		service_name=args.service,
		operation_number=args.oper,
		year=args.year,
		start_date=getattr(args, 'start_date', None),
		end_date=getattr(args, 'end_date', None),
		bsns_div_cd=args.bsns_div,
	)
	collector.execute()
