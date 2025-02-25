import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient


def init_mongodb():
	load_dotenv()

	DB_HOST = os.getenv("DB_HOST")
	DB_PORT = int(os.getenv("DB_PORT"))  # 기본값 설정 가능
	DB_USERNAME = quote_plus(os.getenv("DB_USERNAME"))
	DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD"))
	DB_NAME = os.getenv("DB_NAME")

	client = MongoClient(f"mongodb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}")

	db = client.get_database(DB_NAME)

	return db
