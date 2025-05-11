from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
from utils.postgres_meta import PostgresMeta
from transform_notice import transform_document
from tqdm import tqdm
from psycopg2.extras import execute_values


class DataSync:
	def __init__(self, batch_size: int = 1000):
		self.mongo_server, self.mongo_client = init_mongodb()
		self.mongo_db = self.mongo_client.get_database("gfcon_raw")

		self.psql_server, self.psql_conn = init_psql()
		self.psql_cur = self.psql_conn.cursor()

		self.mongo_default = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사조회")
		self.mongo_bssAmt = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회")
		self.mongo_reserve_price = self.mongo_db.get_collection("낙찰정보서비스.개찰결과공사예비가격상세목록조회")
		self.mongo_bid_list = self.mongo_db.get_collection("공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보")

		self.batch_size = batch_size
		meta = PostgresMeta(self.psql_conn).get_column_types("notice")
		self.psql_columns = list(meta.keys())
		self.placeholder = "(" + ",".join(["%s"] * len(self.psql_columns)) + ")"

	def __del__(self):
		self.psql_cur.close()
		self.psql_conn.close()
		self.mongo_server.close()

	def delete_data(self, table_name: str):
		self.psql_cur.execute(f"DELETE FROM {table_name};")
		self.psql_conn.commit()

	def sync_notice(self):
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

			buffer.append(tuple(row_dict.get(col) for col in self.psql_columns))

	def _flush(self, rows: list[tuple]):
		if not rows:
			return
		insert_sql = f"""
			INSERT INTO notice ({', '.join(self.psql_columns)})
			VALUES %s,
			ON CONFLICT (bidNtceNo, bidNtceOrd) DO NOTHING;
		"""
		execute_values(self.psql_cur, insert_sql, rows, template=self.placeholder)
		self.psql_conn.commit()
		rows.clear()


if __name__ == "__main__":
	sync = DataSync()
	sync.sync_notice()
