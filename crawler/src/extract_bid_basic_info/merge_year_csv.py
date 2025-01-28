import pandas as pd
import os

# 파일 경로

base_path = "../../output/공고_기본_정보/년도별"

# 데이터를 합치기 위한 빈 데이터프레임
combined_data = pd.DataFrame()

# 각 파일을 읽고 '년도' 컬럼 추가 후 데이터프레임에 추가
for year in range(2014, 2025):
	df = pd.read_csv(f"{base_path}/공고기본정보_{year}_서울_통신.csv")
	df.insert(2, '입찰년도', year)
	combined_data = pd.concat([combined_data, df], ignore_index=True)

# 합쳐진 데이터 저장
output_path = '../../output/공고_기본_정보/공고기본정보_서울_통신.csv'
combined_data.to_csv(output_path, index=False)
