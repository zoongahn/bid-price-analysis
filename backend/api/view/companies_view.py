from rest_framework.viewsets import ModelViewSet
from ..models import Notice, Company, Bid
from ..serializers import NoticeSerializer, CompanySerializer, BidSerializer
from django.db.models import Count
from .pagination import CompaniesPagination


class CompanyViewSet(ModelViewSet):
	# Company 모델에 대해 Bid 모델과의 ForeignKey 관계를 따라 Count를 수행합니다.
	queryset = Company.objects.annotate(투찰횟수=Count('bid'))
	serializer_class = CompanySerializer
	pagination_class = CompaniesPagination
