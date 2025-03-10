from common.init_mongodb import *
from common.utils import *


def upload_api_list(csv_file_path: str, collection_name: str = "api_list"):
	opnum_col = "일련번호"
	openg_col = "오퍼레이션명(영문)"
	opkr_col = "오퍼레이션명(국문)"
	op_desc = "오퍼레이션 설명"

	# 1) CSV 읽어들여, 서비스명별로 묶기
	service_dict = {}

	with open(csv_file_path, 'r', encoding='utf-8') as f:
		reader = csv.DictReader(f)
		for row in reader:
			service_name = row["서비스명"].strip()

			op_info = {
				opnum_col: row[opnum_col].strip(),
				openg_col: row[openg_col].strip(),
				opkr_col: row[opkr_col].strip(),
				op_desc: row[op_desc].strip()
			}

			# 서비스명 키가 아직 없다면 배열 생성
			if service_name not in service_dict:
				service_dict[service_name] = []

			# 해당 서비스명 배열에 op_info 추가
			service_dict[service_name].append(op_info)

	# (2) service_groups -> [{service_name:..., operations: [...]}, ...] 형태로 변환
	docs = []
	for svc_name, ops_list in service_dict.items():
		doc = {
			"service_name": svc_name,
			"operations": ops_list
		}
		docs.append(doc)

	DJANGO_ENV = os.getenv("DJANGO_ENV")
	server, db = None, None

	if DJANGO_ENV == "local":
		server, db = connect_mongodb_via_ssh()
	else:
		db = init_mongodb()

	collection = db[collection_name]

	if docs:
		result = collection.insert_many(docs)
		print(f"{len(result.inserted_ids)}개 도큐먼트를 업로드했습니다.")
	else:
		print("CSV가 비어 있거나 유효한 데이터가 없습니다.")

	if server:
		server.stop()


def add_response_fields_to_operations(csv_file_path, collection_name: str = "api_list"):
	opnum_col = "오퍼레이션 번호"
	opkr_col = "오퍼레이션명(국문)"
	field_eng = "항목명(영문)"
	field_kor = "항목명(국문)"
	field_size = "항목크기"
	field_div = "항목구분"
	field_sample = "샘플데이터"
	field_desc = "항목설명"

	DJANGO_ENV = os.getenv("DJANGO_ENV")
	server, db = None, None

	if DJANGO_ENV == "local":
		server, db = connect_mongodb_via_ssh()
	else:
		db = init_mongodb()

	collection = db[collection_name]

	docs = list(collection.find({}))

	with open(csv_file_path, "r", encoding="utf-8-sig") as f:
		reader = csv.DictReader(f)
		for row in reader:
			csv_op_num = row[opnum_col].strip()
			csv_op_kr = row[opkr_col].replace(" ", "").strip()

			response_item = {
				field_eng: row[field_eng].strip(),
				field_kor: row[field_kor].strip(),
				field_size: row[field_size].strip(),
				field_div: row[field_div].strip(),
				field_sample: row[field_sample].strip(),
				field_desc: row[field_desc].strip()
			}

			for doc in docs:
				updated = False
				for op in doc.get("operations", []):
					op_kr_no_space = op.get(opkr_col, "").replace(" ", "").strip()
					if op.get("일련번호") == csv_op_num and op_kr_no_space == csv_op_kr:
						if "response_fields" not in op:
							op["response_fields"] = []
						op["response_fields"].append(response_item)
						updated = True

	# 수정된 문서들을 다시 DB에 저장
	for doc in docs:
		_id = doc["_id"]

		collection.replace_one({"_id": _id}, doc)

	print("모든 CSV 행에 대한 response_field 추가가 완료되었습니다.")

	if server:
		server.stop()
