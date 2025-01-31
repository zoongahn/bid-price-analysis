import re

import pandas as pd
import psycopg2
import os
from dotenv import load_dotenv
from psycopg2.extras import execute_batch

load_dotenv()

# PostgreSQL 연결 정보
DB_CONFIG = {
	"dbname": os.getenv("DB_NAME"),
	"user": os.getenv("DB_USER"),
	"password": os.getenv("DB_PASSWORD"),
	"host": os.getenv("DB_HOST"),  # Ubuntu 서버의 IP를 직접 사용
	"port": os.getenv("DB_PORT")
}

# 업로드할 CSV 파일 경로
NOTICES_CSV_DIR = "../data/processed/notices_processed.csv"
BIDS_CSV_DIR = "../data/processed/bids_processed.csv"

# 테이블명 설정
NOTICES_TABLE = "notices"
BIDS_TABLE = "bids"
COMPANIES_TABLE = "companies"


def upload_notices():
	try:
		# PostgreSQL 연결
		conn = psycopg2.connect(**DB_CONFIG)
		cursor = conn.cursor()

		# CSV 파일 로드
		df = pd.read_csv(NOTICES_CSV_DIR)

		# 컬럼명 통일 (필요한 경우)
		df.rename(columns={
			"발주처(수요기관)": "발주처",
			"투찰률(%)": "투찰률",
			"정답사정률(%)": "정답사정률"
		}, inplace=True)

		# 필요한 컬럼 선택 (실제 존재하는 컬럼만 사용)
		required_columns = ["공고번호", "입찰년도", "공고제목", "발주처", "지역제한", "기초금액", "예정가격", "예가범위", "A값", "투찰률", "참여업체수",
		                    "공고구분표시", "정답사정률"]
		df = df[df.columns.intersection(required_columns)]

		# 숫자형 컬럼에서 "-" 값을 NULL로 변환
		numeric_columns = ["기초금액", "예정가격", "A값", "투찰률", "정답사정률"]  # 실제 컬럼명에 맞게 수정
		df[numeric_columns] = df[numeric_columns].replace("-", None)

		# PostgreSQL에 데이터 삽입
		for _, row in df.iterrows():
			cursor.execute(f"""
                INSERT INTO {NOTICES_TABLE} 
                ("공고번호", "입찰년도", "공고제목", "발주처", "지역제한", "기초금액", "예정가격", "예가범위", "A값", "투찰률", "참여업체수", "공고구분표시", "정답사정률")
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT ("공고번호") DO NOTHING
            """, tuple(row))

		# 변경사항 커밋
		conn.commit()
		print("✅ CSV 데이터를 성공적으로 업로드했습니다.")

	except Exception as e:
		print("❌ 오류 발생:", e)

	finally:
		cursor.close()
		conn.close()


# "기초대비 사정률" 컬럼 처리 함수
# 예: "-0.87170 (99.1283)" → -0.8717
def extract_first_number(value):
	if pd.isna(value) or value == "-":  # NaN 또는 "-" 값 처리
		return None
	match = re.search(r"-?\d+\.\d+", str(value))  # 첫 번째 숫자 추출
	return float(match.group()) if match else None


# 투찰일시 값이 유효한지 확인 후 변환
def clean_datetime(value):
	if pd.isna(value) or value in ["0000/00/00 00:00:00", "-", "NaN", "None"]:
		return None
	try:
		return pd.to_datetime(value, errors="coerce")  # 유효하지 않은 값은 NaT로 변환
	except Exception:
		return None


def upload_bids_and_companies():
	# PostgreSQL 연결
	conn = psycopg2.connect(**DB_CONFIG)
	cursor = conn.cursor()

	df = pd.read_csv(BIDS_CSV_DIR, dtype={"사업자 등록번호": str})

	# 컬럼명 통일
	df.rename(columns={
		"투찰률(%)": "투찰률",
		"예가대비 투찰률(%)": "예가대비 투찰률",
		"기초대비 투찰률(%)": "기초대비 투찰률",
		"기초대비 사정률(%)": "기초대비 사정률",
		"대표": "대표명",
	}, inplace=True)

	# 필요한 컬럼만 선택

	required_columns = ["입찰년도", "공고번호", "순위", "사업자 등록번호", "업체명", "대표명", "투찰금액", "가격점수", "예가대비 투찰률", "기초대비 투찰률",
	                    "기초대비 사정률", "추첨번호", "투찰일시", "비고"]
	df = df[df.columns.intersection(required_columns)]

	# NaN 값을 None으로 변환 (PostgreSQL에서 NULL로 인식)
	df = df.where(pd.notna(df), None)

	# 업체명 정리: "[최종낙찰]" 문자열 제거 (순위 1인 행에 한정)
	df.loc[df["순위"] == 1, "업체명"] = df.loc[df["순위"] == 1, "업체명"].str.replace("  [최종낙찰]$", "")

	df["투찰일시"] = df["투찰일시"].apply(clean_datetime)

	# 데이터 삽입
	for _, row in df.iterrows():
		# 1️⃣ 공고번호(notice_id) 찾기
		cursor.execute("""
		        SELECT id FROM notices WHERE "공고번호" = %s
		    """, (row["공고번호"],))
		notice_result = cursor.fetchone()

		if notice_result:
			notice_id = notice_result[0]
		else:
			print(f"⚠️ 공고번호 {row['공고번호']}에 해당하는 notice_id를 찾을 수 없습니다. 건너뜁니다.")
			continue

		# 2️⃣ 업체 정보(company_id) 찾기
		# 이미 업체정보가 존재하는지 확인
		cursor.execute("""
					SELECT id FROM companies WHERE "사업자 등록번호" = %s
				""", (row["사업자 등록번호"],))
		company_result = cursor.fetchone()

		if company_result:
			company_id = company_result[0]
		else:
			cursor.execute("""
				INSERT INTO companies ("사업자 등록번호", "업체명", "대표명")
				VALUES (%s, %s, %s)
				RETURNING id
			""", (row["사업자 등록번호"], row["업체명"], row["대표명"]))
			company_id = cursor.fetchone()[0]

		# 3️⃣ 낙찰 여부 설정
		is_winner = True if row["순위"] == 1 else False

		# 4️⃣ 입찰 데이터 삽입
		cursor.execute("""
		    INSERT INTO bids (notice_id, company_id, "순위", "투찰금액", "가격점수", "예가대비 투찰률", 
		                      "기초대비 투찰률", "기초대비 사정률", "추첨번호", "낙찰여부", "투찰일시", "비고") 
		    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
		""", (notice_id, company_id, row["순위"], row["투찰금액"], row["가격점수"],
		      row["예가대비 투찰률"], row["기초대비 투찰률"], extract_first_number(row["기초대비 사정률"]),
		      row["추첨번호"], is_winner, row["투찰일시"], row["비고"]))

	# 변경 사항 저장 후 종료
	conn.commit()
	cursor.close()
	conn.close()

	print("✅ 데이터 업로드 완료!")


if __name__ == "__main__":
	# upload_notices()
	upload_bids_and_companies()
