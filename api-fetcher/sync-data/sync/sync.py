from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
from utils.postgres_meta import PostgresMeta
from transform_notice import transform_document
from tqdm import tqdm
from psycopg2.extras import execute_values


class DataSync:
	def __init__(self, batch_size: int = 10000):
		self.mongo_server, self.mongo_client = init_mongodb()
		self.mongo_db = self.mongo_client.get_database("gfcon_raw")

		self.psql_server, self.psql_conn = init_psql()
		self.psql_cur = self.psql_conn.cursor()

		self.mongo_default = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사조회")
		self.mongo_bssAmt = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회")
		self.mongo_reserve_price = self.mongo_db.get_collection("낙찰정보서비스.개찰결과공사예비가격상세목록조회")
		self.mongo_bid_list = self.mongo_db.get_collection("공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보")

		self.batch_size = batch_size

	def delete_data(self, table_name: str):
		self.psql_cur.execute(f"DELETE FROM {table_name};")
		self.psql_conn.commit()

	def _flush(self, rows: list[tuple], table: str, columns: list[str], placeholder: str, conflict_on: str):
		if not rows:
			return
		sql = f"""
			INSERT INTO {table} ({', '.join(columns)})
			VALUES %s 
			ON CONFLICT {conflict_on} DO NOTHING;
		"""
		execute_values(self.psql_cur, sql, rows, template=placeholder)
		self.psql_conn.commit()
		rows.clear()

	def _mark_synced(self, key_list: list[tuple[str, str]]):
		for bid_no, bid_ord in key_list:
			self.mongo_default.update_one({"bidNtceNo": bid_no, "bidNtceOrd": bid_ord}, {"$set": {"is_synced": True}})

	def sync_notice(self):
		meta = PostgresMeta(self.psql_conn).get_column_types("notice")
		psql_columns = list(meta.keys())
		placeholder = "(" + ",".join(["%s"] * len(psql_columns)) + ")"

		total = self.mongo_default.count_documents({"is_synced": {"$ne": True}})
		print(f"🔄  총 {total:,} 건 동기화 시작 (batch={self.batch_size})")

		buffer: list[tuple] = []
		synced_keys: list[tuple[str, str]] = []  # bidNtceNo, bidNtceOrd 쌍 보관

		WIN_FIELDS = [
			"fnlSucsfAmt", "fnlSucsfRt", "fnlSucsfDate",
			"fnlSucsfCorpNm", "fnlSucsfCorpCeoNm", "fnlSucsfCorpOfclNm",
			"fnlSucsfCorpBizrno", "fnlSucsfCorpAdrs", "fnlSucsfCorpContactTel",
			"cntrctCnclsSttusNm", "bidwinrDcsnMthdNm",
		]

		WIN_PROJECTION = {f: 1 for f in WIN_FIELDS}
		WIN_PROJECTION["_id"] = 0  # _id 제외

		cursor = self.mongo_default.find({"is_synced": {"$ne": True}}, {"_id": 0})

		for doc_default in tqdm(cursor, total=40000):
			bid_no = doc_default["bidNtceNo"]
			bid_ord = doc_default["bidNtceOrd"]

			doc_bssAmt = self.mongo_bssAmt.find_one({"bidNtceNo": bid_no, "bidNtceOrd": bid_ord}, {"_id": 0}) or {}
			doc_bid = self.mongo_bid_list.find_one({"bidNtceNo": bid_no, "bidNtceOrd": bid_ord}, WIN_PROJECTION) or {}

			merged = {**doc_default, **doc_bssAmt, **doc_bid}
			row_dict = transform_document(merged)
			row_dict.pop("_id", None)

			buffer.append(tuple(row_dict.get(col) for col in psql_columns))
			synced_keys.append((bid_no, bid_ord))

			if len(buffer) >= self.batch_size:
				self._flush(buffer, "notice", psql_columns, placeholder, "(bidNtceNo, bidNtceOrd)")
				self._mark_synced(synced_keys)
				buffer.clear()
				synced_keys.clear()

		if buffer:
			self._flush(buffer, "notice", psql_columns, placeholder, "(bidNtceNo, bidNtceOrd)")
			self._mark_synced(synced_keys)

		print("✅  동기화 완료")

	def sync_reserve_price(self):

		reserve_meta = PostgresMeta(self.psql_conn).get_column_types("reserve_price_range")
		reserve_columns: list[str] = list(reserve_meta.keys())
		reserve_placeholder = "(" + ",".join(["%s"] * len(reserve_columns)) + ")"

		total = self.mongo_reserve_price.estimated_document_count()
		print(f"🔄  총 {total:,} 건 (reserve_price_range) 동기화 시작 (batch={self.batch_size})")

		buffer: list[tuple] = []

		for doc in tqdm(self.mongo_reserve_price.find({}), total=total):
			row_dict = transform_document(doc)
			row_dict.pop("_id", None)

			# Mongo 필드에는 range_no 가 compnoRsrvtnPrceSno 로 들어있으므로 보정
			if "range_no" not in row_dict and "compnoRsrvtnPrceSno" in doc:
				row_dict["range_no"] = int(doc["compnoRsrvtnPrceSno"])

			buffer.append(tuple(row_dict.get(col) for col in reserve_columns))

			if len(buffer) >= self.batch_size:
				self._flush(buffer, "reserve_price_range", reserve_columns, reserve_placeholder,
				            "(bidNtceNo, bidNtceOrd, range_no)")

		if buffer:
			self._flush(buffer, "reserve_price_range", reserve_columns, reserve_placeholder,
			            "(bidNtceNo, bidNtceOrd, range_no)")

		print("✅  reserve_price_range 동기화 완료")

	def test(self):
		def distinct_bid_keys_mongo(coll):
			# MongoDB에서 (bidNtceNo, bidNtceOrd) 쌍을 가져오기
			pipeline = [
				{"$project": {"_id": 0, "bidNtceNo": 1, "bidNtceOrd": 1}},
				{"$group": {"_id": {"bidNtceNo": "$bidNtceNo", "bidNtceOrd": "$bidNtceOrd"}}},
			]
			for doc in coll.aggregate(pipeline):
				yield doc["_id"]["bidNtceNo"], doc["_id"]["bidNtceOrd"]

		def fetch_notice_keys_postgres():
			self.psql_cur.execute("SELECT bidNtceNo, bidNtceOrd FROM notice;")
			return set(self.psql_cur.fetchall())

		mongo_keys = set(distinct_bid_keys_mongo(self.mongo_reserve_price))
		notice_keys = fetch_notice_keys_postgres()

		missing = mongo_keys - notice_keys
		print(f"🔍 reserve_price 중 notice에 없는 공고 {len(missing):,}건")
		print([i for i, j in missing])


if __name__ == "__main__":
	sync = DataSync(batch_size=1000)
	sync.sync_reserve_price()
