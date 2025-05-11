from db_connect import get_mongo_client
from db_connect.get_psql_conn import get_psql_conn  # 정확한 경로 확인

conn = get_psql_conn()


def get_field_list(service_name: str = "입찰공고정보서비스", operation_number: int = 1, lang: str = "kor") -> list:
	with get_mongo_client() as client:
		db = client.get_database("gfcon")
		coll = db.get_collection("api_list")

		result = coll.find_one(
			{
				"service_name": service_name,
				"operations.일련번호": str(operation_number),
			},
			{
				"_id": 0,
				"operations.$": 1
			}
		)["operations"][0]["response_fields"]

		return [field["항목명(국문)" if lang == "kor" else "항목명(영문)"] for field in result]


def check_duplicate_fields(a: list, b: list) -> bool:
	service_name = "입찰공고정보서비스"
	operation_number = 24
	print(a)
	print(b)
	duplicates = list(set(a) & set(b))
	print(duplicates)


def print_comment_query(eng_fields: list, kor_fields: list, table_name: str):
	for e, k in zip(eng_fields[5:], kor_fields[5:]):
		print(f"COMMENT ON COLUMN {table_name}.{e} IS '{k}';")


if __name__ == '__main__':
	service_name = "입찰공고정보서비스"
	operation_number = 6
	eng_fields = get_field_list(service_name, operation_number, lang="eng")
	kor_fields = get_field_list(service_name, operation_number, lang="kor")
	print_comment_query(eng_fields, kor_fields, "notice")
