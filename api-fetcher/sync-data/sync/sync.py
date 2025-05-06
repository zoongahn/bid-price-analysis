from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
from tqdm import tqdm
from sync_notice.transform_notice import transform_document


class DataSync:
	def __init__(self):
		self.mongo_server, self.mongo_client = init_mongodb()
		self.mongo_db = self.mongo_client.get_database("gfcon_raw")

		self.psql_server, self.psql_conn = init_psql()
		self.psql_cur = self.psql_conn.cursor()

	def __del__(self):
		self.psql_cur.close()
		self.psql_conn.close()
		self.mongo_server.close()

	def delete_data(self, table_name: str):
		self.psql_cur.execute(f"DELETE FROM {table_name};")
		self.psql_conn.commit()

	def test(self):
		mongo_default = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사조회")
		mongo_bssAmt = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회")

		docs = mongo_default.find().limit(10)

		batch = []

		for doc in docs:
			bss_doc = mongo_bssAmt.find_one({"bidNtceNo": doc.get("bidNtceNo")})
			doc = {**doc, **bss_doc}
			doc = transform_document(doc)
			batch.append(doc)

		self.insert_batch(batch)

	def sync_notice_data(self, batch_size: int = 1000):
		mongo_default = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사조회")
		mongo_bssAmt = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회")

		total_count = mongo_default.count_documents({})
		print(f"🔄 총 {total_count}건 동기화 시작")

		cursor = mongo_default.find({})
		batch = []
		for doc in tqdm(cursor, total=total_count):
			bidNtceNo = doc.get("bidNtceNo")
			bss_doc = mongo_bssAmt.find_one({"bidNtceNo": bidNtceNo})

			print(doc, bss_doc)

			# 두 문서를 병합
			merged_doc = {**doc, **bss_doc}

			batch.append(transform_document(merged_doc))

			if len(batch) >= batch_size:
				self.insert_batch(batch)
				batch.clear()

		if batch:
			self.insert_batch(batch)

		print("✅ 동기화 완료")

	def insert_batch(self, batch):
		if not batch:
			return

		columns = batch[0].keys()
		values = [
			tuple(doc.get(col) for col in columns)
			for doc in batch
		]
		args_str = ",".join(
			self.psql_cur.mogrify(f"({','.join(['%s'] * len(columns))})", row).decode() for row in values)

		query = f"""
	        INSERT INTO notice ({','.join(columns)})
	        VALUES {args_str}
	        ON CONFLICT (bidNtceNo, bidNtceOrd) DO NOTHING;
	        """
		self.psql_cur.execute(query)
		self.psql_conn.commit()
		print(f"✅ {len(batch)}건 커밋 완료")

	def get_table_column_info(self, table_name: str):
		self.psql_cur.execute(f"""
		        SELECT 
		            a.attname AS column_name,
		            pgd.description AS comment,
		            pg_catalog.format_type(a.atttypid, a.atttypmod) AS data_type,
		            CASE WHEN a.attnotnull THEN 'NO' ELSE 'YES' END AS is_nullable
		        FROM pg_catalog.pg_attribute a
		        JOIN pg_catalog.pg_class c ON a.attrelid = c.oid
		        JOIN pg_catalog.pg_namespace n ON c.relnamespace = n.oid
		        LEFT JOIN pg_catalog.pg_description pgd ON pgd.objoid = a.attrelid AND pgd.objsubid = a.attnum
		        WHERE 
		            c.relname = %s
		            AND n.nspname = 'public'
		            AND a.attnum > 0
		            AND NOT a.attisdropped
		        ORDER BY a.attnum;
		    """, (table_name,))
		columns = self.psql_cur.fetchall()
		return [column for column in columns]


if __name__ == "__main__":
	sync = DataSync()
	sync.sync_notice_data()
