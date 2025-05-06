import os
from dotenv import load_dotenv
import psycopg2
from sshtunnel import SSHTunnelForwarder

load_dotenv()

POSTGRES_DB = os.getenv("POSTGRES_DB")
POSTGRES_USER = os.getenv("POSTGRES_USER")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD")
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", 5432))


def connect_psql_local():
	return psycopg2.connect(
		host=POSTGRES_HOST,
		port=POSTGRES_PORT,
		dbname=POSTGRES_DB,
		user=POSTGRES_USER,
		password=POSTGRES_PASSWORD,
	)


def connect_psql_via_ssh():
	SSH_HOST = os.getenv("SSH_HOST")
	SSH_PORT = int(os.getenv("SSH_PORT"))
	SSH_USERNAME = os.getenv("SSH_USER")
	SSH_PASSWORD = None  # 비밀번호 방식 사용 시 설정
	SSH_PKEY = os.getenv("SSH_PKEY_PATH")  # SSH 키 사용

	# SSH 터널링 설정
	server = SSHTunnelForwarder(
		(SSH_HOST, SSH_PORT),
		ssh_username=SSH_USERNAME,
		ssh_password=SSH_PASSWORD if SSH_PKEY is None else None,
		ssh_pkey=SSH_PKEY if SSH_PKEY else None,
		remote_bind_address=(POSTGRES_HOST, POSTGRES_PORT),
	)

	server.start()

	LOCAL_BIND_PORT = server.local_bind_port

	conn = psycopg2.connect(
		host="127.0.0.1",
		port=LOCAL_BIND_PORT,
		dbname=POSTGRES_DB,
		user=POSTGRES_USER,
		password=POSTGRES_PASSWORD,
	)

	return server, conn


def init_psql():
	server, conn = None, None

	ENV = os.getenv("DJANGO_ENV")

	if ENV == "remote":
		server, conn = connect_psql_via_ssh()
	elif ENV == "local":
		conn = connect_psql_local()

	return server, conn
