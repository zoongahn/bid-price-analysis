import json

from django.db.models.fields.related import ForeignKey
from django.db.models.query_utils import Q
from rest_framework.viewsets import ModelViewSet
from ..models import Notice, Company, Bid
from ..serializers import NoticeSerializer, CompanySerializer, BidSerializer
from .pagination import BidsPagination
import math
from django.db import connection


def transform_field(field, model):
	"""
    만약 field에 '.'이 포함되어 있다면 앞부분을 가져와서 해당 필드가 model의 외래키인지 확인하고,
    외래키면 Django ORM lookup 형식인 '__'로 변환하여 반환합니다.
    """
	if '.' in field:
		relation_field, remote_field = field.split('.', 1)
		try:
			field_obj = model._meta.get_field(relation_field)
			if isinstance(field_obj, ForeignKey):
				return f"{relation_field}__{remote_field}"
		except Exception:
			# 예외 발생 시 원래 필드명을 그대로 반환
			return field
	return field


class BidViewSet(ModelViewSet):
	serializer_class = BidSerializer
	pagination_class = BidsPagination

	def get_queryset(self):
		qs = Bid.objects.select_related('notice', 'company').all()

		# 정렬 처리
		sort_param = self.request.query_params.get("sort", None)
		foreign_key_mapping = {
			"공고번호": "notice__공고번호",
			"업체명": "company__업체명",
		}
		if sort_param:
			try:
				sort_model = json.loads(sort_param)
				# sort_model은 리스트 형태입니다. 각 객체는 {colId, sort} 형태
				ordering = []
				for sort_item in sort_model:
					field = sort_item.get("colId")
					direction = sort_item.get("sort")

					field = transform_field(field, Bid)

					if direction == "desc":
						ordering.append(f"-{field}")
					else:
						ordering.append(field)
				if ordering:
					qs = qs.order_by(*ordering)
					print(ordering)

					# 정렬된 queryset에서 예가대비투찰률 컬럼이 None 인 행을 제외
					qs = qs.exclude(**{f"{field}__isnull": True})

					qs = qs.order_by(*ordering)

			except Exception as e:
				print("정렬 파라미터 파싱 에러:", e)

		# ------------------------------------------------------------------------

		# 필터링 처리 (filter 파라미터)
		filter_param = self.request.query_params.get("filter", None)
		if filter_param:
			try:
				filter_model = json.loads(filter_param)
				filter_conditions = Q()
				for col, filter_info in filter_model.items():
					search_field = transform_field(col, Bid)
					# conditions 배열이 있는 경우 (여러 조건 전달)
					if "conditions" in filter_info:
						operator = filter_info.get("operator").upper()
						conditions = filter_info.get("conditions", [])
						q_list = []
						for cond in conditions:
							q_obj = self.build_filter_condition(search_field, cond)
							if q_obj:
								q_list.append(q_obj)
						if q_list:
							# 조건들을 operator에 따라 결합
							if operator == "OR":
								col_q = Q()
								for q in q_list:
									col_q |= q
							else:  # 기본값은 AND
								col_q = Q()
								for q in q_list:
									col_q &= q
							filter_conditions &= col_q
					else:
						# 단일 조건 처리
						q_obj = self.build_filter_condition(search_field, filter_info)
						if q_obj:
							filter_conditions &= q_obj
				qs = qs.filter(filter_conditions)
			except Exception as e:
				print("필터 파라미터 파싱 에러:", e)
		return qs

	def build_filter_condition(self, field, filter_dict):
		"""
        filter_dict에 담긴 정보에 따라 Q 객체를 반환합니다.
        숫자 필터와 텍스트 필터 모두를 지원합니다.
        """
		filter_type = filter_dict.get("filterType")
		compare = filter_dict.get("type")
		filter_value = filter_dict.get("filter")
		if filter_value is None:
			return None

		# 숫자 필터의 경우
		if filter_type == "number":
			try:
				numeric_value = float(filter_value)
			except Exception:
				return None

			if compare in ("equals", "equal"):
				return Q(**{f"{field}": numeric_value})
			elif compare in ("notEqual", "notEquals"):
				return ~Q(**{f"{field}": numeric_value})
			elif compare == "greaterThan":
				return Q(**{f"{field}__gt": numeric_value})
			elif compare == "greaterThanOrEqual":
				return Q(**{f"{field}__gte": numeric_value})
			elif compare == "lessThan":
				return Q(**{f"{field}__lt": numeric_value})
			elif compare == "lessThanOrEqual":
				return Q(**{f"{field}__lte": numeric_value})

		# 텍스트 필터의 경우
		elif filter_type == "text":
			filter_value_str = str(filter_value)
			if compare == "contains":
				return Q(**{f"{field}__icontains": filter_value_str})
			elif compare == "notContains":
				return ~Q(**{f"{field}__icontains": filter_value_str})
			elif compare in ("equals", "equal"):
				return Q(**{f"{field}__iexact": filter_value_str})
			elif compare in ("notEqual", "notEquals"):
				return ~Q(**{f"{field}__iexact": filter_value_str})
			elif compare == "startsWith":
				return Q(**{f"{field}__istartswith": filter_value_str})
			elif compare == "endsWith":
				return Q(**{f"{field}__iendswith": filter_value_str})

		return None
