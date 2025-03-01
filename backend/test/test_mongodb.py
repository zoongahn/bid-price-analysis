import os
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


