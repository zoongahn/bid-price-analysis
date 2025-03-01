import os

from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ViewSet

from db_config.local import connect_mongodb_via_ssh
from db_config.production import init_mongodb
from dotenv import load_dotenv


load_dotenv()

class ApiInfoViewSet(ViewSet):
	def dispatch(self, request, *args, **kwargs):
		"""ViewSet이 처음 실행될 때 DB 연결 설정"""
		DJANGO_ENV = os.getenv("DJANGO_ENV")

		if DJANGO_ENV == "local":
			self.server, self.db = connect_mongodb_via_ssh()
		else:
			self.db = init_mongodb()

		self.collection = self.db.get_collection("api_list")
		return super().dispatch(request, *args, **kwargs)

	def list(self, request):
		"""모든 데이터 조회"""
		data = list(self.collection.find({}, {"_id": 0}))
		return Response(data)

	@csrf_exempt
	@action(detail=False, methods=["POST"])
	def save_selected_fields(self, request):
		try:
			data = request.data
			service_name = data.get("service_name")  # 서비스 이름 추가
			operation_name = data.get("operation_name")
			selected_fields = data.get("selected_fields")  # { "항목명(영문)": True/False }

			# 해당 서비스와 오퍼레이션 찾기
			query = {"service_name": service_name, "operations.오퍼레이션명(영문)": operation_name}
			operation = self.collection.find_one(query, {"operations.$": 1})

			if not operation:
				return JsonResponse({"error": "오퍼레이션을 찾을 수 없음"}, status=404)

			# 기존 response_fields 리스트 가져오기
			existing_fields = operation["operations"][0]["response_fields"]

			# 새로운 필드 리스트 생성 (기존 데이터 유지하면서 selected_for_use 추가)
			updated_fields = [
				{
					**field,  # 기존 필드 데이터 유지
					"selected_for_use": selected_fields.get(field["항목명(영문)"], field.get("selected_for_use", False))
					# 기본값 유지
				}
				for field in existing_fields
			]

			# MongoDB 업데이트 실행
			self.collection.update_one(
				query,
				{"$set": {f"operations.$.response_fields": updated_fields}}
			)

			return JsonResponse({"message": "✅ 필드 선택이 성공적으로 저장되었습니다."}, status=200)
		except Exception as e:
			return JsonResponse({"error": str(e)}, status=500)