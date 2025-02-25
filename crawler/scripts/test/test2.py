import pandas as pd

# CSV 파일 로드
file_path = "../data/processed/bids_processed_fixed.csv"

df = pd.read_csv(file_path, encoding="utf-8")

df[df["사업자 등록번호"] == "12081*****"] = 1208153421

df.to_csv(file_path, encoding="utf-8", index=False)
