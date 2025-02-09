from rest_framework.viewsets import ModelViewSet
from rest_framework.response import Response
from rest_framework import status
from django.db.models import F
from ...models import Bid
from ...serializers import BidSerializer


class ByCompanyViewSet(ModelViewSet):
	queryset = Bid.objects.all()
	serializer_class = BidSerializer

	def get_queryset(self):

		option = self.request.query_params.get("option")
		query = self.request.query_params.get("query")
		selected_fields = self.request.query_params.get("selectedColumns").split(",")

		print(option, query, selected_fields)

		# option이나 query가 없으면 빈 쿼리셋 반환
		if not option or not query:
			return Bid.objects.none()

		# 모든 조건에 대해 queryset을 미리 초기화
		queryset = Bid.objects.none()

		# 사업자등록번호 옵션일 경우, 관련 회사와 공고 데이터를 조인하여 필요한 필드를 aliasing합니다.
		if option == "사업자등록번호":
			queryset = (
				Bid.objects.select_related("company", "notice")

				.filter(company__사업자등록번호=query)
				.annotate(
					공고번호=F("notice__공고번호"),
					공고제목=F("notice__공고제목"),
					업체명=F("company__업체명"),
					예가범위=F("notice__예가범위")
				)
				.values(*selected_fields)

			)
		elif option == "업체명":
			# 업체명의 경우에도 동일하게 select_related를 사용하여 조인한 후 필터 적용
			queryset = (
				Bid.objects.select_related("company", "notice")
				.filter(company__업체명__icontains=query)
				.annotate(
					공고번호=F("notice__공고번호"),
					공고제목=F("notice__공고제목"),
					업체명=F("company__업체명"),
					예가범위=F("notice__예가범위")

				)
				.values(*selected_fields)

			)

		return queryset

	def list(self, request, *args, **kwargs):
		# get_queryset()가 딕셔너리 QuerySet을 반환하는 경우 직접 리스트로 만들어 Response에 전달
		queryset = self.get_queryset()
		option = self.request.query_params.get("option")
		if option in ["사업자등록번호", "업체명"]:
			return Response(list(queryset))
		else:
			serializer = self.get_serializer(queryset, many=True)
			return Response(serializer.data)
