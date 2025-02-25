import pandas as pd

raw_data_path = "../data/processed/bids_processed.csv"

# CSV 읽을 때 dtype 지정 및 low_memory=False 설정
df = pd.read_csv(raw_data_path, encoding="utf-8", dtype={"사업자 등록번호": str}, low_memory=False)

print(len(df))
