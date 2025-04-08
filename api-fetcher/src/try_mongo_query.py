from common.init_mongodb import init_mongodb
import pandas as pd

# MongoDB 연결
server, client = init_mongodb()
db = client.get_database("gfcon_raw")
col = db.get_collection("공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보")

# pipeline = [
# 	{
# 		"$project": {
# 			"_id": 0,
# 			"opengDate": 1,
# 			"bidNtceNo": 1,
# 			"bidNtceNm": 1,
# 			"opengRank": 1,
# 			"bidprcCorpNm": 1
# 		},
# 	},
# 	{
# 		"$sort": {
# 			"collected_at": -1
# 		}
# 	},
# 	{
# 		"$limit": 8560
# 	}
# ]

pipeline = [
	{
		"$sort": {
			"opengDate": -1
		}
	},
	{
		"$limit": 8560
	}
]

# 결과 가져오기
result = list(col.aggregate(pipeline))

# pandas DataFrame으로 변환 후 CSV 저장
df = pd.DataFrame(result)
df.to_csv("opengDate_collected_at_1.csv", index=False, encoding="utf-8-sig")  # Excel 호환 인코딩

# MongoDB 연결 종료
server.stop()
