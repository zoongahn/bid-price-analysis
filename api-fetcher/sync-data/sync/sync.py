from typing import Optional, Callable

from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
from utils.postgres_meta import PostgresMeta
from transform_document import transform_document
from tqdm import tqdm
from psycopg2.extras import execute_values
from pymongo import UpdateOne


class DataSync:
	def __init__(self, batch_size: int = 10000):
		self.mongo_server, self.mongo_client = init_mongodb()
		self.mongo_db = self.mongo_client.get_database("gfcon_raw")

		self.psql_server, self.psql_conn = init_psql()
		self.psql_cur = self.psql_conn.cursor()

		self.mongo_default = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사조회")
		self.mongo_bssAmt = self.mongo_db.get_collection("입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회")
		self.mongo_reserve_price = self.mongo_db.get_collection("낙찰정보서비스.개찰결과공사예비가격상세목록조회")
		self.mongo_bid = self.mongo_db.get_collection("공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보")
		self.mongo_company = self.mongo_db.get_collection("사용자정보서비스.조달업체기본정보")

		self.batch_size = batch_size

		self.total_skip = 0

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

	def _mark_synced(self, collection, key_list: list[tuple], key_fields: tuple[str, ...]):
		ops = []
		for keys in key_list:
			query = dict(zip(key_fields, keys))
			ops.append(UpdateOne(query, {"$set": {"is_synced": True}}))

		if ops:
			collection.bulk_write(ops, ordered=False)

	def sync_notice(self):
		WIN_FIELDS = [
			"opengDate", "opengTm", "opengRsltDivNm",
			"fnlSucsfAmt", "fnlSucsfRt", "fnlSucsfDate",
			"fnlSucsfCorpNm", "fnlSucsfCorpCeoNm", "fnlSucsfCorpOfclNm",
			"fnlSucsfCorpBizrno", "fnlSucsfCorpAdrs", "fnlSucsfCorpContactTel",
			"cntrctCnclsSttusNm", "bidwinrDcsnMthdNm",
		]

		WIN_PROJECTION = {f: 1 for f in WIN_FIELDS}
		WIN_PROJECTION["_id"] = 0

		cursor = self.mongo_default.find({"is_synced": {"$ne": True}}, {"_id": 0})

		def transform_with_merge(doc: dict) -> dict:
			bid_no = doc["bidNtceNo"]
			bid_ord = doc["bidNtceOrd"]

			doc_bssAmt = self.mongo_bssAmt.find_one({"bidNtceNo": bid_no, "bidNtceOrd": bid_ord}, {"_id": 0}) or {}
			doc_bid = self.mongo_bid.find_one({"bidNtceNo": bid_no, "bidNtceOrd": bid_ord}, WIN_PROJECTION) or {}

			merged = {**doc, **doc_bssAmt, **doc_bid}
			row_dict = transform_document("notice", merged, None)
			row_dict.pop("_id", None)

			return row_dict

		self.sync_mongo_to_postgres(
			mongo_collection=self.mongo_default,
			psql_table="notice",
			psql_pk=("bidntceno", "bidntceord"),
			mongo_unique_keys=("bidNtceNo", "bidNtceOrd"),
			preprocess=transform_with_merge
		)

	def sync_mongo_to_postgres(self, *, mongo_collection, psql_table: str, psql_pk: tuple[str, ...],
	                           mongo_unique_keys: tuple[str, ...],
	                           field_aliases: list[tuple[str, str]] | None = None,
	                           preprocess: Optional[Callable[[dict], dict]] = None):
		"""
		Parameters:
		    mongo_collection:
		        동기화 대상이 되는 MongoDB 컬렉션 객체입니다. 예: self.mongo_default
		    psql_table (str):
		        데이터를 삽입할 PostgreSQL 테이블 이름입니다.
		    psql_pk (tuple[str, ...]):
		        PSQL INSERT 쿼리의 ON CONFLICT 절에서 사용할 PK 튜플입니다.
		        PSQL로 sync 과정에서 필드명은 모두 소문자로 변환되므로 파라미터 역시 반드시 소문자로 제공되어야함.
		        예: ("bidntceno", "bidntceord")
		    mongo_unique_keys (tuple[str, ...]):
				is_synced를 toggle할때 사용되는 몽고디비 컬렉션의 unique key. 예: ("bidNtceNo", "bidNtceOrd")
		    field_aliases (list[tuple[str, str]]):
		        MongoDB 필드명과 PostgreSQL 컬럼명을 다르게 설정할 경우의 매핑 리스트.
		        형식: [(psql_field, mongo_field)]
		        예: [("range_no", "compnoRsrvtnPrceSno")]
		    preprocess (Optional[Callable[[dict], dict]]):
		        각 Mongo 문서를 PostgreSQL row 형식의 dict로 변환하는 사용자 정의 함수입니다.
		        제공되지 않으면 기본 transform_document()가 사용됩니다.
		"""
		meta = PostgresMeta(self.psql_conn).get_column_types(psql_table)
		psql_columns = list(meta.keys())
		placeholder = "(" + ",".join(["%s"] * len(psql_columns)) + ")"

		# total = mongo_collection.count_documents({"is_synced": {"$ne": True}})
		total = mongo_collection.count_documents({"bidNtceNo": "20091221595", "bidNtceOrd": "000"})
		print(f"🔄 [{psql_table}] 총 {total:,} 건 동기화 시작 (batch={self.batch_size})")

		buffer: list[tuple] = []
		synced_keys: list[tuple] = []

		# cursor = mongo_collection.find({"is_synced": {"$ne": True}}, {"_id": 0})
		cursor = mongo_collection.find({"bidNtceNo": "20091221595", "bidNtceOrd": "000"}, {"_id": 0})

		for doc in tqdm(cursor, total=total):
			# 별도 함수가 파라미터로 전달되었는지?
			if preprocess:
				row_dict = preprocess(doc)
				if row_dict is None:
					continue
			else:
				row_dict = transform_document(psql_table, doc, field_aliases=field_aliases)
				row_dict.pop("_id", None)

			buffer.append(tuple(row_dict.get(col) for col in psql_columns))
			synced_keys.append(tuple(doc[field] for field in mongo_unique_keys))

			if len(buffer) >= self.batch_size:
				self._flush(buffer, psql_table, psql_columns, placeholder, f"({', '.join(psql_pk)})")
				self._mark_synced(mongo_collection, synced_keys, mongo_unique_keys)
				buffer.clear()
				synced_keys.clear()

				exit()

		if buffer:
			self._flush(buffer, psql_table, psql_columns, placeholder, f"({', '.join(psql_pk)})")
			self._mark_synced(mongo_collection, synced_keys, mongo_unique_keys)

		print(f"✅  {psql_table} 동기화 완료")

	def sync_notice_openg_fields(self):
		meta = PostgresMeta(self.psql_conn).get_column_types("notice")
		psql_columns = ["bidntceno", "bidntceord", "opengdate", "opengtm", "opengrsltdivnm"]
		placeholder = "(" + ",".join(["%s"] * len(psql_columns)) + ")"

		self.psql_cur.execute("SELECT bidntceno, bidntceord FROM notice;")
		notice_keys = self.psql_cur.fetchall()
		print(f"🔄 [notice.openg_fields] 총 {len(notice_keys):,}건 업데이트 시작")

		buffer = []
		for bid_no, bid_ord in tqdm(notice_keys, total=len(notice_keys)):
			doc = self.mongo_bid.find_one(
				{"bidNtceNo": bid_no, "bidNtceOrd": bid_ord},
				{"_id": 0, "opengDate": 1, "opengTm": 1, "opengRsltDivNm": 1}
			)
			if not doc:
				continue

			row = (
				bid_no,
				bid_ord,
				doc.get("opengDate"),
				doc.get("opengTm"),
				doc.get("opengRsltDivNm"),
			)

			buffer.append(row)

			if len(buffer) >= self.batch_size:
				self._flush_openg_fields(buffer, psql_columns, placeholder)
				buffer.clear()

		if buffer:
			self._flush_openg_fields(buffer, psql_columns, placeholder)

		print("✅  openg 필드 동기화 완료")

	def _flush_openg_fields(self, rows: list[tuple], columns: list[str], placeholder: str):
		if not rows:
			return
		sql = f"""
			INSERT INTO notice ({', '.join(columns)})
			VALUES %s
			ON CONFLICT (bidntceno, bidntceord) DO UPDATE SET
				opengdate = EXCLUDED.opengdate,
				opengtm = EXCLUDED.opengtm,
				opengrsltdivnm = EXCLUDED.opengrsltdivnm;
		"""
		execute_values(self.psql_cur, sql, rows, template=placeholder)
		self.psql_conn.commit()
		rows.clear()

	def execute(self, sync_table: str):
		match sync_table:
			case "notice":
				self.sync_notice()
			case "reserve_price_range":
				self.sync_mongo_to_postgres(
					mongo_collection=self.mongo_reserve_price,
					psql_table="reserve_price_range",
					psql_pk=("bidntceno", "bidntceord", "range_no"),
					mongo_unique_keys=("bidNtceNo", "bidNtceOrd", "compnoRsrvtnPrceSno"),
					field_aliases=[("range_no", "compnoRsrvtnPrceSno")]
				)
			case "company":
				self.sync_mongo_to_postgres(
					mongo_collection=self.mongo_company,
					psql_table="company",
					psql_pk=("bizno",),
					mongo_unique_keys=("bizno",)
				)
			case "bid":
				self.psql_cur.execute("SELECT bidntceno, bidntceord FROM notice;")
				notice_keys = self.psql_cur.fetchall()
				print(notice_keys)

				def preprocess_bid(doc: dict) -> dict | None:
					row_dict = transform_document("bid", doc, None)
					row_dict.pop("_id", None)

					# 외래키 관계 확인: notice에 존재하는 공고번호인지?
					fk_key = (row_dict.get("bidntceno"), row_dict.get("bidntceord"))
					if fk_key not in notice_keys:
						self.total_skip += 1
						return None  # None 반환 → 이후 insert 제외 처리

					if not row_dict.get("bidprccorpbizrno"):
						row_dict["bidprccorpbizrno"] = "__DEFAULT__"
					return row_dict

				self.sync_mongo_to_postgres(
					mongo_collection=self.mongo_bid,
					psql_table="bid",
					psql_pk=("bidntceno", "bidntceord", "bidprccorpbizrno"),
					mongo_unique_keys=("bidNtceNo", "bidNtceOrd", "bidprcCorpBizrno"),
					preprocess=preprocess_bid
				)
				print(f"notice 테이블에 존재하지않는 공고번호 갯수(skip 횟수): {self.total_skip:,}회")
				
			case _:
				raise ValueError(f"Invalid sync_table: {sync_table}")

	def verify_notice_sync(self):
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

	def verify_company_sync(self):
		def distinct_bizrno_mongo():
			# MongoDB 투찰데이터에서 bidprcCorpBizrno 고유값 추출
			return set(self.mongo_bid.distinct("bidprcCorpBizrno", {"bidprcCorpBizrno": {"$ne": None}}))

		def fetch_bizno_postgres():
			self.psql_cur.execute("SELECT bizno FROM company;")
			return set(row[0] for row in self.psql_cur.fetchall())

		mongo_bizrno = distinct_bizrno_mongo()
		psql_bizno = fetch_bizno_postgres()

		missing = mongo_bizrno - psql_bizno
		print(f"🔍 bid_list 중 company에 없는 사업자번호 {len(missing):,}건")
		print(list(missing))


if __name__ == "__main__":
	sync = DataSync(batch_size=10)
	sync.execute("bid")
