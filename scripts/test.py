import pandas as pd
import os

raw_data_path = "../data/processed/bids_processed_fixed.csv"

# CSV 읽을 때 dtype 지정 및 low_memory=False 설정
df = pd.read_csv(raw_data_path, encoding="utf-8", dtype={"사업자 등록번호": str}, low_memory=False)

# NaN 값이 있는 행 제거
df = df.dropna(subset=["사업자 등록번호"])

# "*"로 끝나는 사업자 등록번호 필터링
my_df = df[df["사업자 등록번호"].str.endswith("*")]

# 필터링된 데이터 저장
my_df.to_csv("my_df.csv", encoding="utf-8", index=False)

print("✅ 데이터 저장 완료: my_df.csv")
