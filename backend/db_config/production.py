from pymongo import MongoClient
from urllib.parse import quote_plus
import os

def init_mongodb():
    """ 운영 환경에서 직접 MongoDB에 접속 """
    DB_HOST = os.getenv("DB_HOST", "your-server-ip")
    DB_PORT = int(os.getenv("DB_PORT", "27017"))
    DB_USERNAME = quote_plus(os.getenv("DB_USERNAME", "prod_user"))
    DB_PASSWORD = quote_plus(os.getenv("DB_PASSWORD", "prod_password"))
    DB_NAME = os.getenv("DB_NAME", "gfcon")

    client = MongoClient(f"mongodb://{DB_USERNAME}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}")

    db = client.get_database(DB_NAME)

    return db