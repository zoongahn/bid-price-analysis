# db_connect/get_mongo_conn.py
import os
from contextlib import contextmanager
from dotenv import load_dotenv
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder

load_dotenv()

ENV = os.getenv("ENV", "local").lower()

MONGO_USER = os.getenv("MONGODB_USER")
MONGO_PASSWORD = os.getenv("MONGODB_PASSWORD")
MONGO_HOST = os.getenv("MONGODB_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGODB_PORT", 27017))
MONGO_AUTH_DB = os.getenv("MONGODB_AUTH_SOURCE", "admin")

SSH_HOST = os.getenv("SSH_HOST")
SSH_PORT = int(os.getenv("SSH_PORT", 22))
SSH_USER = os.getenv("SSH_USER")
SSH_PKEY_PATH = os.getenv("SSH_PKEY_PATH")
LOCAL_BIND_PORT = int(os.getenv("MONGO_LOCAL_BIND_PORT", 27018))


@contextmanager
def _ssh_tunnel():
    with SSHTunnelForwarder(
        (SSH_HOST, SSH_PORT),
        ssh_username=SSH_USER,
        ssh_pkey=SSH_PKEY_PATH,
        remote_bind_address=(MONGO_HOST, MONGO_PORT),
        local_bind_address=("127.0.0.1", LOCAL_BIND_PORT),
    ) as tunnel:
        yield tunnel


@contextmanager
def get_mongo_client():
    if ENV == "remote":
        with _ssh_tunnel():
            client = MongoClient(
                host="127.0.0.1",
                port=LOCAL_BIND_PORT,
                username=MONGO_USER,
                password=MONGO_PASSWORD,
                authSource=MONGO_AUTH_DB,
            )
            try:
                yield client
            finally:
                client.close()
    else:
        client = MongoClient(
            host=MONGO_HOST,
            port=MONGO_PORT,
            username=MONGO_USER,
            password=MONGO_PASSWORD,
            authSource=MONGO_AUTH_DB,
        )
        try:
            yield client
        finally:
            client.close()