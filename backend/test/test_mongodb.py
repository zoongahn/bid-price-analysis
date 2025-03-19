import os
import sys

# 현재 스크립트의 부모 디렉토리를 시스템 경로에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from db_config.local import connect_mongodb_via_ssh
from db_config.production import init_mongodb
from dotenv import load_dotenv

load_dotenv()

DJANGO_ENV = os.getenv("DJANGO_ENV")

print(DJANGO_ENV)

if DJANGO_ENV == "local":
    server, db = connect_mongodb_via_ssh()
else:
    db = init_mongodb()