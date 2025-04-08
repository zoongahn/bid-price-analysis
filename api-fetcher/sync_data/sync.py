from pymongo import UpdateOne

from common.init_mongodb import init_mongodb

server, client = init_mongodb()

# DB 핸들러
raw_db = client["gfcon_raw"]
target_db = client["gfcon"]

# 복사할 컬렉션 및 필드 정의
COLLECTIONS_TO_SYNC = {
	"NOTICE": {
		"filter_fields": ["공고번호", "공고제목", "입찰년도", "발주처", "기초금액", "참여업체수"],
		"unique_fields": ["공고번호"],
	},
	"낙찰된목록현황공사조회": {
		"filter_fields": ["bidNtceNo", "opengDt", "cntrctCnclsDt", "opengResult", "ntceInsttNm"],
		"unique_fields": ["bidNtceNo"],
	},
	# 추가 컬렉션 정의 가능
}


def sync_collection(raw_col_name: str, tgt_col_name: str, filter_fields: list, unique_fields: list):
	raw_col = raw_db[raw_col_name]
	tgt_col = target_db[tgt_col_name]

	operations = []

	for doc in raw_col.find({}):
		# 필요한 필드만 추출
		filtered_doc = {key: doc.get(key) for key in filter_fields}
		filtered_doc["collected_at"] = doc.get("collected_at")  # 수집시간도 유지

		# upsert용 쿼리
		unique_query = {key: doc.get(key) for key in unique_fields}
		operations.append(
			UpdateOne(unique_query, {"$set": filtered_doc}, upsert=True)
		)

	if operations:
		result = tgt_col.bulk_write(operations)
		print(f"✅ [{raw_col_name}] synced: inserted {result.upserted_count}, updated {result.modified_count}")
	else:
		print(f"⚠️ [{raw_col_name}] no documents to sync.")


def sync_bid_results_to_notices():
	raw_bid_col = raw_db["낙찰된목록현황공사조회"]
	target_notice_col = target_db["공고데이터"]

	updated = 0
	for bid_doc in raw_bid_col.find({}):
		bid_ntce_no = bid_doc.get("bidNtceNo")
		if not bid_ntce_no:
			continue

		update_data = {
			"bid_opened": True,
			"낙찰정보": {
				"opengDt": bid_doc.get("opengDt"),
				"cntrctCnclsDt": bid_doc.get("cntrctCnclsDt"),
				"opengResult": bid_doc.get("opengResult"),
				"ntceInsttNm": bid_doc.get("ntceInsttNm"),
			}
		}

		result = target_notice_col.update_one(
			{"공고번호": bid_ntce_no},
			{"$set": update_data}
		)

		if result.modified_count > 0:
			updated += 1

	print(f"✅ 낙찰정보 동기화 완료: {updated}건 업데이트됨.")


def sync_all():
	for col_name, cfg in COLLECTIONS_TO_SYNC.items():
		sync_collection(
			raw_col_name=col_name,
			filter_fields=cfg["filter_fields"],
			unique_fields=cfg["unique_fields"]
		)

	# 입찰공고와 연결되는 낙찰정보를 입찰공고 문서에 추가
	sync_bid_results_to_notices()


if __name__ == "__main__":
	sync_all()
