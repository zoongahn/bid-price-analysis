import csv

from common.init_mongodb import *

# MongoDB SSH 터널 연결
server, client = init_mongodb()
db = client.get_database("gfcon_raw")
collection_notices = db.get_collection("낙찰정보서비스.낙찰된목록현황공사조회")
collection_bids = db.get_collection("낙찰정보서비스.개찰결과개찰완료목록조회")


def initialize_bids_info_field():
	"""모든 문서에 bids_info_is_collected 필드를 추가하고 기본값을 False로 설정"""
	result = collection_notices.update_many(
		{},  # 모든 문서 대상
		{"$set": {"bids_info_is_collected": False}}
	)
	print(f"✅ {result.modified_count}개의 문서에 bids_info_is_collected=False 설정 완료")


def update_bids_info_field():
	# 1. bidNtceNo 기준으로 그룹화하여 count 계산
	pipeline = [
		{
			"$group": {
				"_id": "$bidNtceNo",
				"count": {"$sum": 1}  # 해당 공고 번호의 개수
			}
		}
	]
	bid_counts = {doc["_id"]: doc["count"] for doc in collection_bids.aggregate(pipeline)}

	# 2. 낙찰된 목록에서 bidNtceNo를 기준으로 prtcptCnum 가져오기
	notice_data = {
		doc["bidNtceNo"]: doc["prtcptCnum"]
		for doc in collection_notices.find({}, {"bidNtceNo": 1, "prtcptCnum": 1, "_id": 0})
	}

	# 3. 비교 후 bids_info_is_collected 업데이트
	update_count = 0
	for bidNtceNo, count in bid_counts.items():
		prtcptCnum = notice_data.get(bidNtceNo)

		if prtcptCnum is not None and int(prtcptCnum) <= count:
			collection_notices.update_one(
				{"bidNtceNo": bidNtceNo},
				{"$set": {"bids_info_is_collected": True}}
			)
			update_count += 1

	print(f"✅ {update_count}개의 문서에 bids_info_is_collected=True 업데이트 완료")


update_bids_info_field()

# MongoDB SSH 터널 종료
server.stop()
