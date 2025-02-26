import os
from urllib.parse import quote_plus
from dotenv import load_dotenv
from pymongo import MongoClient
from sshtunnel import SSHTunnelForwarder


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


def init_mongodb_via_ssh():
	# SSH 서버 정보
	SSH_HOST = "gfcon.ddnsfree.com"
	SSH_PORT = 22
	SSH_USERNAME = "gfadmin"
	SSH_PASSWORD = "mypassword"
	SSH_PKEY = "/Users/joonghyun/.ssh/ubuntu_server_id_rsa"  # SSH 키를 쓸 경우

	# 원격 MongoDB 정보 (SSH 서버 내부에서 접근할 MongoDB 주소/포트)
	REMOTE_MONGO_HOST = "127.0.0.1"
	REMOTE_MONGO_PORT = 27017

	# 연결 시도
	server, mongo_client = connect_mongodb_via_ssh(
		ssh_host=SSH_HOST,
		ssh_port=SSH_PORT,
		ssh_username=SSH_USERNAME,
		ssh_password=SSH_PASSWORD,
		ssh_pkey=SSH_PKEY,
		remote_mongo_host=REMOTE_MONGO_HOST,
		remote_mongo_port=REMOTE_MONGO_PORT
	)

	db = mongo_client.get_database("gfcon")

	return server, db


def connect_mongodb_via_ssh(
		ssh_host: str,
		ssh_port: int,
		ssh_username: str,
		ssh_password: str = None,
		ssh_pkey: str = None,
		remote_mongo_host: str = '127.0.0.1',
		remote_mongo_port: int = 27017,
		local_bind_host: str = '127.0.0.1'
):
	# SSH 터널 생성
	server = SSHTunnelForwarder(
		(ssh_host, ssh_port),
		ssh_username=ssh_username,
		ssh_password=ssh_password,  # 비밀번호 방식
		ssh_pkey=ssh_pkey,  # 또는 SSH 키 파일 (둘 중 하나만 사용)
		remote_bind_address=(remote_mongo_host, remote_mongo_port),
		local_bind_address=(local_bind_host, 0)  # 0을 지정하면 자동 할당
	)

	server.start()

	# server.local_bind_port를 통해 동적으로 할당된 포트 확인 가능
	print(f"SSH tunnel established. Forwarded port: {server.local_bind_port}")

	# 이제 local_bind_host:server.local_bind_port 로 MongoDB 접근 가능
	client = MongoClient(local_bind_host, server.local_bind_port)
	return server, client
