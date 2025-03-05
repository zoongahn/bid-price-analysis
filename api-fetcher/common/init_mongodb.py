import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder

load_dotenv()


def init_mongodb():
	MONGODB_HOST = os.getenv("MONGODB_HOST")
	MONGODB_PORT = int(os.getenv("MONGODB_PORT"))
	MONGODB_USER = quote_plus(os.getenv("MONGODB_USER"))
	MONGODB_PASSWORD = quote_plus(os.getenv("MONGODB_PASSWORD"))
	MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE")


	mongodb_url = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@{MONGODB_HOST}:{MONGODB_PORT}/?authSource={MONGODB_AUTH_SOURCE}"

	client = MongoClient(mongodb_url)

	return client


def connect_mongodb_via_ssh():
	""" SSH 터널을 생성하여 MongoDB에 연결 """
	global server

	SSH_HOST = os.getenv("SSH_HOST")
	SSH_PORT = int(os.getenv("SSH_PORT"))
	SSH_USERNAME = os.getenv("SSH_USER")
	SSH_PASSWORD = None  # 비밀번호 방식 사용 시 설정
	SSH_PKEY = os.getenv("SSH_PKEY_PATH")  # SSH 키 사용

	MONGODB_HOST = os.getenv("MONGODB_HOST")
	MONGODB_PORT = int(os.getenv("MONGODB_PORT"))
	MONGODB_USER = quote_plus(os.getenv("MONGODB_USER"))
	MONGODB_PASSWORD = quote_plus(os.getenv("MONGODB_PASSWORD"))
	MONGODB_AUTH_SOURCE = os.getenv("MONGODB_AUTH_SOURCE")

	# SSH 터널링 설정
	server = SSHTunnelForwarder(
		(SSH_HOST, SSH_PORT),
		ssh_username=SSH_USERNAME,
		ssh_password=SSH_PASSWORD if SSH_PKEY is None else None,
		ssh_pkey=SSH_PKEY if SSH_PKEY else None,
		remote_bind_address=(MONGODB_HOST, MONGODB_PORT),
	)

	server.start()

	local_port = server.local_bind_port  # SSH 터널링된 포트(매번다름)

	# 로컬 포트를 통해 MongoDB 연결
	mongodb_url = f"mongodb://{MONGODB_USER}:{MONGODB_PASSWORD}@localhost:{local_port}/?authSource={MONGODB_AUTH_SOURCE}"
	mongo_client = MongoClient(mongodb_url)

	return server, mongo_client
