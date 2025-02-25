import json
import os
from pymongo import MongoClient
import sys

ROOT_DIR = "/absolute/path/to/project"  # 예: "/home/ubuntu/my_project"
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from src.init_mongodb import init_mongodb


def upload_api_list(json_file_path: str, collection_name: str = "api_list"):
	# 1. JSON 파일 읽기
	with open(json_file_path, 'r', encoding='utf-8') as f:
		data = json.load(f)

	# 2. 몽고디비 접속 (접속 정보는 환경에 맞게 수정)
	db = init_mongodb()
	collection = db[collection_name]

	# 3. 읽어온 data(전체 JSON)를 그대로 하나의 도큐먼트로 insert
	#    기존에 유사한 구조가 있다면 upsert 등을 고려할 수도 있음
	result = collection.insert_one(data)
	print("MongoDB에 업로드 완료. 도큐먼트 ID:", result.inserted_id)


if __name__ == "__main__":
	API_OPER_LIST_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "api_info",
	                                  "api_operation_lists.json")

	upload_api_list(API_OPER_LIST_PATH)
