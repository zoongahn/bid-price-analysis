import os

from common.init_mongodb import *


class ApiInfo:
	def __init__(self):
		server, client = None, None

		if os.getenv("DJANGO_ENV") == "local":
			server, client = connect_mongodb_via_ssh()
		else:
			client = init_mongodb()

		db = client.get_database("gfcon")

		self.collection = db["api_list"]

	def get_full_data(self):
		return list(self.collection.find({}, {"_id": 0}))[0]

	def get_service(self, service_name: str):
		return list(self.collection.find({"service_name": service_name}, {"_id": 0}))[0]


api_info = ApiInfo()
print(api_info.get_service("입찰공고정보서비스"))
