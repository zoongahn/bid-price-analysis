import pandas as pd
import os
from collections import Counter


def process_notices_data(raw_data_path: str = "../data/raw/공고_기본_정보/공고기본정보_서울_통신.csv"):
	processed_data_path = "../data/processed/notices_processed.csv"

	df = pd.read_csv(raw_data_path, index_col=0)

	# 🚀 공고번호가 공백인 행 삭제
	df.dropna(subset=["공고번호"], inplace=True)

	# "-" 값을 공백("")으로 변경
	df.replace("-", "", inplace=True)

	if "입찰년도" in df.columns:
		df["입찰년도"] = df["입찰년도"].fillna(0).astype(int)  # NaN을 0으로 대체 후 정수 변환

	# 변경된 데이터 저장 (선택 사항)
	df.to_csv(processed_data_path, index=False, encoding="utf-8")


def check_columns():
	data_dir = "../data/raw/공고별_기업_투찰정보_년도별"

	expected_columns = [
		'순위', '사업자 등록번호', '업체명', '대표', '경쟁사 분석', '투찰금액', '가격점수',
		'예가대비 투찰률(%)', '기초대비 투찰률(%)', '기초대비 사정률(%)', '추첨번호', '투찰일시', '비고'
	]

	different_column = Counter()

	years = sorted(
		[folder for folder in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, folder))])

	for year in years:
		year_path = os.path.join(data_dir, year)

		files = os.listdir(year_path)

		for file in files:
			print(file)
			if file.endswith(".csv"):
				file_path = os.path.join(year_path, file)

				df = pd.read_csv(file_path, encoding='utf-8')

				current_columns = tuple(df.columns)

				different_column.update(list(current_columns))

	print(different_column)


def merge_bids_data(raw_data_dir: str = "../data/raw/공고별_기업_투찰정보_년도별"):
	MERGED_CSV_PATH = "../data/raw/공고별_기업_투찰정보.csv"

	standard_column_list = ['입찰년도', '공고번호', '순위', '사업자 등록번호', '업체명', '대표', '경쟁사 분석', '투찰금액', '가격점수', '예가대비 투찰률(%)',
	                        '기초대비 투찰률(%)', '기초대비 사정률(%)', '추첨번호', '투찰일시', '비고']
	result = []

	years = sorted(
		[folder for folder in os.listdir(raw_data_dir) if os.path.isdir(os.path.join(raw_data_dir, folder))])
	for year in years:
		year_path = os.path.join(raw_data_dir, year)

		for file in os.listdir(year_path):
			if file.endswith(".csv"):
				print(file)
				file_path = os.path.join(year_path, file)
				print(file_path)

				if os.path.getsize(file_path) == 0:
					print(f"⚠️ 빈 파일 발견: {file_path}, 스킵합니다.")
					continue  # 빈 파일이면 건너뛰기

				df_new = pd.read_csv(file_path, encoding="utf-8")

				# 입찰년도 및 공고번호 추가
				df_new.insert(0, "입찰년도", year)
				df_new.insert(1, "공고번호", file.replace(".csv", ""))

				# 새로운 파일의 데이터 컬럼 정렬 (부족한 컬럼은 NaN 처리)
				df_new = df_new.reindex(columns=standard_column_list, fill_value="")

				result.append(df_new)

	# 리스트에 있는 데이터프레임 한 번에 병합
	df_result = pd.concat(result, ignore_index=True)

	# 최종 데이터 저장
	df_result.to_csv(MERGED_CSV_PATH, encoding="utf-8", index=False)


def process_bids_data(raw_data_path: str = "../data/raw/공고별_기업_투찰정보.csv"):
	df = pd.read_csv(raw_data_path, encoding="utf-8")

	# 같은 업체명을 가진 다른 행에서 사업자 등록번호를 채움
	df["사업자 등록번호"] = df.groupby("업체명")["사업자 등록번호"].transform(lambda x: x.ffill().bfill())

	# 같은 사업자 등록번호를 가진 다른 행에서 대표명을 채움
	df["대표"] = df.groupby("사업자 등록번호")["대표"].transform(lambda x: x.ffill().bfill())

	df.to_csv("../data/processed/bids_processed_1.csv", encoding="utf-8", index=False)


def clean_masking():
	raw_data_path = "../data/processed/bids_processed.csv"

	# CSV 읽기 (dtype=str로 설정하여 숫자도 문자열로 유지)
	df = pd.read_csv(raw_data_path, encoding="utf-8", dtype={"사업자 등록번호": str}, low_memory=False)

	# NaN 값이 있는 행 제거
	df = df.dropna(subset=["사업자 등록번호", "업체명"])

	# 마스킹된 사업자 등록번호를 가진 행 필터링
	masked_rows = df["사업자 등록번호"].str.contains(r"\*+", regex=True, na=False)

	# 온전한 사업자 등록번호를 찾기 위한 딕셔너리 생성
	company_registry_map = df[~masked_rows].set_index("업체명")["사업자 등록번호"].to_dict()

	# 마스킹된 사업자 등록번호를 가진 행을 온전한 값으로 교체
	df.loc[masked_rows, "사업자 등록번호"] = df.loc[masked_rows, "업체명"].map(company_registry_map).fillna(
		df.loc[masked_rows, "사업자 등록번호"])

	# 결과 저장
	df.to_csv("../data/processed/bids_processed_fixed.csv", encoding="utf-8", index=False)

	print("✅ 마스킹된 사업자 등록번호가 성공적으로 교체되었습니다.")


if __name__ == "__main__":
	process_bids_data("../data/processed/bids_processed.csv")
