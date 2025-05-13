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

	def __del__(self):
		self.psql_cur.close()
		self.psql_conn.close()
		self.mongo_server.close()

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

	def sync_notice(self):
		meta = PostgresMeta(self.psql_conn).get_column_types("notice")
		psql_columns = list(meta.keys())
		placeholder = "(" + ",".join(["%s"] * len(psql_columns)) + ")"

		total = self.mongo_default.estimated_document_count()
		print(f"🔄  총 {total:,} 건 동기화 시작 (batch={self.batch_size})")

		buffer: list[tuple] = []

		WIN_FIELDS = [
			"fnlSucsfAmt", "fnlSucsfRt", "fnlSucsfDate",
			"fnlSucsfCorpNm", "fnlSucsfCorpCeoNm", "fnlSucsfCorpOfclNm",
			"fnlSucsfCorpBizrno", "fnlSucsfCorpAdrs", "fnlSucsfCorpContactTel",
			"cntrctCnclsSttusNm", "bidwinrDcsnMthdNm",
		]

		WIN_PROJECTION = {f: 1 for f in WIN_FIELDS}
		WIN_PROJECTION["_id"] = 0  # _id 제외

		for doc_default in tqdm(self.mongo_default.find({}), total=total):
			bid_no = doc_default["bidNtceNo"]
			bid_ord = doc_default["bidNtceOrd"]

			doc_bssAmt = self.mongo_bssAmt.find_one({"bidNtceNo": bid_no, "bidNtceOrd": bid_ord}, {"_id": 0}) or {}
			doc_bid = self.mongo_bid_list.find_one({"bidNtceNo": bid_no, "bidNtceOrd": bid_ord}, WIN_PROJECTION) or {}

			merged = {**doc_default, **doc_bssAmt, **doc_bid}
			row_dict = transform_document(merged)

			row_dict.pop("_id", None)

			buffer.append(tuple(row_dict.get(col) for col in psql_columns))

			if len(buffer) >= self.batch_size:
				self._flush(buffer, "notice", psql_columns, placeholder, "(bidNtceNo, bidNtceOrd)")
				buffer.clear()

		if buffer:
			self._flush(buffer, "notice", psql_columns, placeholder, "(bidNtceNo, bidNtceOrd)")

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
		def distinct_stream(coll, field):
			pipeline = [
				{"$group": {"_id": f"${field}"}},
				{"$project": {field: "$_id", "_id": 0}},
			]
			for doc in coll.aggregate(pipeline, allowDiskUse=True):
				yield doc[field]

		a = set(distinct_stream(self.mongo_reserve_price, "bidNtceNo"))
		b = set(distinct_stream(self.mongo_default, "bidNtceNo"))
		print(a - b)


if __name__ == "__main__":
	sync = DataSync()
	sync.test()
