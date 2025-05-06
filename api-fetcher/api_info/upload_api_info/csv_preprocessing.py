import csv
import os

from common.utils import get_project_root


def merge_null_rows_into_description(
		input_csv,
		output_csv,
		key_columns=None,
		desc_column="항목설명"
):
	"""
	- input_csv를 DictReader로 읽는다.
	- key_columns(예: ['항목명(영문)', '항목명(국문)', '항목크기', ...]) 중
	  전부 비어있고, desc_column만 있는 행을 "쓰레기(추가) 행"으로 간주.
	- 그 행의 desc_column 내용을 직전 "정상 행"의 desc_column에 이어 붙이고, 쓰레기 행은 제거.
	- 최종적으로 정리된 행들을 output_csv에 기록.
	"""

	if key_columns is None:
		key_columns = ["항목명(영문)", "항목명(국문)", "항목크기", "항목구분", "샘플데이터"]

	# 1) CSV 읽어오기
	with open(input_csv, "r", encoding="utf-8-sig", newline="") as f:
		reader = csv.DictReader(f)
		rows = list(reader)

	# 2) 전처리: 쓰레기(추가) 행 감지 → 직전 행에 병합
	cleaned_rows = []
	for row in rows:
		# key_columns 중 하나라도 값이 있으면 "정상 행"
		# 모두 null/빈문자이면 "쓰레기(추가) 행"이라 가정
		is_key_filled = any(row.get(k, "").strip() for k in key_columns)
		desc_val = row.get(desc_column, "").strip()

		if not is_key_filled and desc_val:
			# => 쓰레기 행 + 항목설명만 있음
			# cleaned_rows[-1] 의 desc_column 끝에 추가
			if cleaned_rows:
				prev_desc = cleaned_rows[-1].get(desc_column, "")
				# 공백이나 구분자 추가 후 병합
				merged_desc = prev_desc.rstrip() + "\n" + desc_val
				cleaned_rows[-1][desc_column] = merged_desc.strip()
		# 그 외에는(만약 cleaned_rows가 비어 있으면) 그냥 무시
		else:
			# => 정상 행이므로 그대로 추가
			cleaned_rows.append(row)

	# 3) 결과 CSV 쓰기
	#    DictWriter를 쓰기 위해 필드명은 원본 csv의 fieldnames를 그대로 쓰거나
	#    cleaned_rows[0]에서 키 목록을 가져와도 됨.
	fieldnames = rows[0].keys() if rows else []
	with open(output_csv, "w", encoding="utf-8-sig", newline="") as outf:
		writer = csv.DictWriter(outf, fieldnames=fieldnames)
		writer.writeheader()
		for crow in cleaned_rows:
			writer.writerow(crow)


def process_csv_lsep(input_csv, output_csv, encoding='utf-8'):
	"""
	CSV 파일을 읽어 각 셀에 대해서:
	  - 텍스트 처음/끝에 있는 LSEP(U+2028)는 strip
	  - 나머지 LSEP는 모두 '\n'으로 치환
	처리 후, output_csv로 저장한다.
	"""
	with open(input_csv, 'r', encoding=encoding, newline='') as inf, \
			open(output_csv, 'w', encoding=encoding, newline='') as outf:

		reader = csv.reader(inf)
		writer = csv.writer(outf)

		for row in reader:
			new_row = []
			for cell in row:
				# 1) 먼저, 셀의 앞뒤에 있는 LSEP(U+2028)만 제거(strip)
				#   strip의 인자로 '\u2028'을 주면, 해당 문자들을 앞뒤에서 모두 제거
				cell = cell.strip('\u2028')

				# 2) 그 외 셀 내부에 남아있는 LSEP는 모두 '\n'으로 변환
				cell = cell.replace('\u2028', '\n')

				new_row.append(cell)

			# 처리된 한 행을 writer로 출력
			writer.writerow(new_row)


if __name__ == "__main__":
	api_list = ["입찰공고정보서비스", "낙찰정보서비스", "계약정보서비스", "사용자정보서비스", "공공데이터개방표준서비스"]

	for api_name in api_list:
		input_file = os.path.join(get_project_root(), "api_info", "operation_fields", "raw", f"{api_name}.csv")
		output_file = os.path.join(get_project_root(), "api_info", "operation_fields", "processed", f"{api_name}.csv")

		process_csv_lsep(input_file, output_file)
		print(f"[완료] '{input_file}' 파일의 LSEP를 처리한 결과가 '{output_file}'에 저장되었습니다.")
