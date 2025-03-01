# views.py 예시
import math

from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.viewsets import ModelViewSet

from api.view.refer.pagination import NoticesPagination
from api.models import Notice
from api.serializers import NoticeSerializer
from decimal import Decimal
from django.db.models import Q

# 허용할 컬럼 목록 (모델 필드명과 정확히 일치해야 함)
allowed_columns = [
	"id", "공고번호", "입찰년도", "공고제목",
	"발주처", "지역제한", "기초금액",
	"예정가격", "예가범위", "A값",
	"투찰률", "참여업체수", "공고구분표시",
	"정답사정률",
]


def replace_nan(data):
	if isinstance(data, float):
		# float NaN, Inf 처리
		if math.isnan(data) or math.isinf(data):
			return None
	elif isinstance(data, Decimal):
		# Decimal NaN, Inf 처리
		if data.is_nan() or data.is_infinite():
			return None
		# 그 외의 경우, 필요하면 float이나 str로 변환
		return float(data)
	elif isinstance(data, dict):
		return {k: replace_nan(v) for k, v in data.items()}
	elif isinstance(data, list):
		return [replace_nan(v) for v in data]
	return data


def apply_filters_and_sort(queryset, request, allowed_columns):
	filter_conditions = Q()
	# 1) 필터
	for key, value in request.query_params.items():
		if key.startswith("filter[") and key.endswith("]"):
			field_name = key[7:-1]  # '공고번호', '입찰년도__gte', ...
			# base_field: '__' 이전까지의 진짜 컬럼명 추출 (ex: '공고번호')
			# 만약 '__'가 없으면 그대로 field_name
			split_parts = field_name.split("__", 1)  # 최대 1회만 자름
			base_field = split_parts[0]

			if base_field not in allowed_columns:
				# 허용되지 않은 컬럼이면 무시
				continue

			# (A-1) 연산자 / lookup 구문 추출
			# ex) '공고번호__icontains' -> lookup='icontains'
			#     '입찰년도__gte'       -> lookup='gte'
			#     '발주처'             -> lookup='exact'
			lookup = "exact"  # 기본값
			if len(split_parts) > 1:
				lookup = split_parts[1]  # 'gte', 'icontains' 등

			# (A-2) Q 필터 구성
			# ex) Q(공고번호__icontains="경기도")
			# ex) Q(입찰년도__gte=2010)
			# ex) Q(발주처__exact="서울시설공단")
			django_field_lookup = f"{base_field}__{lookup}"
			filter_conditions &= Q(**{django_field_lookup: value})

	queryset = queryset.filter(filter_conditions)

	# 2) 정렬
	# 예: ?sort[공고번호]=asc, ?sort[기초금액]=desc
	sort_fields = []
	for key, value in request.query_params.items():
		if key.startswith("sort[") and key.endswith("]"):
			field_name = key[5:-1]  # e.g. '공고번호'
			if field_name in allowed_columns:
				# asc 또는 desc
				direction = value.lower()
				if direction == "desc":
					sort_fields.append(f"-{field_name}")
				else:
					# 기본 asc
					sort_fields.append(field_name)

	if sort_fields:
		queryset = queryset.order_by(*sort_fields)

	return queryset


class NoticeViewSet(ModelViewSet):
	queryset = Notice.objects.all()
	serializer_class = NoticeSerializer
	pagination_class = NoticesPagination  # ← 페이지네이션 클래스 지정

	def list(self, request, *args, **kwargs):
		# 1) columns 파라미터로 DB에서 가져올 필드만 제한
		selected_columns = request.query_params.getlist("columns", [])
		# ❗ rownum처럼 DB에 없는 것은 자동 필터링되어 제거
		safe_columns = [col for col in selected_columns if col in allowed_columns]
		if not safe_columns:
			# 컬럼이 전혀 없다면 기본 컬럼 모두 주거나, 400 에러를 내도 됨
			safe_columns = allowed_columns

		queryset = Notice.objects.values(*safe_columns)

		# 2) 필터/정렬
		queryset = apply_filters_and_sort(queryset, request, allowed_columns)

		# 3) DRF 페이지네이션
		page = self.paginate_queryset(queryset)
		if page is not None:
			cleaned_data = replace_nan(list(page))
			return self.get_paginated_response(cleaned_data)

		cleaned_list = replace_nan(list(queryset))
		return Response(cleaned_list)

	@action(detail=False, methods=["post"])
	def get_filter_columns(self, request):
		"""
		body로 넘어온 columns 배열에 포함된 필드만 선택하여 DB에서 꺼내고 반환.
		"""
		try:
			data = request.data

			# 🔹 선택된 컬럼만 가져오기
			selected_columns = data.get("columns", [])

			# 그중 허용된 컬럼에 있는 컬럼만
			safe_columns = [col for col in selected_columns if col in allowed_columns]

			if not safe_columns:
				return Response({"detail": "선택된 컬럼이 없습니다."}, status=400)

			# DB에서 selected_columns에 해당하는 컬럼들만 꺼내오기
			queryset = Notice.objects.values(*safe_columns)

			# 별도 함수로 필터/정렬 적용
			queryset = apply_filters_and_sort(queryset, request, allowed_columns)

			# 페이지네이션 적용
			page = self.paginate_queryset(queryset)  # 내부적으로 NoticePagination + page_size=500 사용
			if page is not None:
				cleaned_data = replace_nan(list(page))
				# 2) get_paginated_response() 호출:
				#    DRF가 { "count": 총개수, "next": 다음페이지URL, "previous": 이전페이지URL, "results": [...]} 형태로 감싸서 반환
				return self.get_paginated_response(cleaned_data)

			# 만약 페이지네이션이 적용되지 않았다면(기본 DRF 설정에서 무조건 적용되긴 합니다)
			cleaned_list = replace_nan(list(queryset))

			return Response(cleaned_list, status=200)

		except Exception as e:
			return Response({"error": str(e)}, status=500)
