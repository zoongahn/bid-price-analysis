import os

from common.init_mongodb import *


class ApiInfo:

	def __init__(self):
		server, client = init_mongodb()

		db = client.get_database("gfcon")

		self.collection = db["api_list"]

	def get_full_data(self):
		return list(self.collection.find({}, {"_id": 0}))[0]

	def get_service(self, service_name: str):
		return list(self.collection.find({"service_name": service_name}, {"_id": 0}))[0]

	def get_operation(self, service_name: str, operation_number: int | str) -> dict | None:
		"""
		지정된 서비스명과 일련번호(operation_number)에 해당하는 오퍼레이션 정보를 반환.
		"""
		# 일련번호는 DB에 문자열로 저장되어 있으므로 str 변환
		operation_number = str(operation_number)

		service = self.get_service(service_name)
		if not service:
			return None

		return self.collection.find_one(
			{
				"service_name": service_name,
				"operations.일련번호": operation_number,
			},
			{
				"_id": 0,
				"operations.$": 1
			}
		)["operations"][0]

	def get_response_fields(self, service_name: str, operation_number: int | str):
		return self.get_operation(service_name, operation_number)["response_fields"]

	def get_field_names(self, service_name: str, operation_number: int | str):
		fields = self.get_response_fields(service_name, operation_number)
		return [field['항목명(영문)'] for field in fields]


api_info = ApiInfo()
print(api_info.get_response_fields("입찰공고정보서비스", 1))
