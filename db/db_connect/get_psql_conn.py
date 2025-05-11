# db_connect/get_db_conn.py
import os
from contextlib import contextmanager
from dotenv import load_dotenv
import psycopg2
from sshtunnel import SSHTunnelForwarder

load_dotenv()

# 환경 변수 설정
ENV = os.getenv("ENV", "local").lower()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))

SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PKEY_PATH = os.getenv("SSH_PKEY_PATH")
LOCAL_BIND_PORT = int(os.getenv("LOCAL_BIND_PORT", 5433))


@contextmanager
def _ssh_tunnel():
    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_pkey=SSH_PKEY_PATH,
        remote_bind_address=(POSTGRES_HOST, POSTGRES_PORT),
        local_bind_address=("127.0.0.1", LOCAL_BIND_PORT),
    ) as tunnel:
        yield tunnel


@contextmanager
def get_psql_conn():
    if ENV == "remote":
        with _ssh_tunnel():
            conn = psycopg2.connect(
                host="127.0.0.1",
                port=LOCAL_BIND_PORT,
                dbname=POSTGRES_DB,
                user=POSTGRES_USER,
                password=POSTGRES_PASSWORD,
            )
            try:
                yield conn
            finally:
                conn.close()
    else:
        conn = psycopg2.connect(
            host=POSTGRES_HOST,
            port=POSTGRES_PORT,
            dbname=POSTGRES_DB,
            user=POSTGRES_USER,
            password=POSTGRES_PASSWORD,
        )
        try:
            yield conn
        finally:
            conn.close()