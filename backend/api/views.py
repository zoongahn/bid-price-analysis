from rest_framework import viewsets
from .models import Notice, Company, Bid
from .serializers import NoticeSerializer, CompanySerializer, BidSerializer


class NoticeViewSet(viewsets.ModelViewSet):
	queryset = Notice.objects.all()
	serializer_class = NoticeSerializer


class CompanyViewSet(viewsets.ModelViewSet):
	queryset = Company.objects.all()
	serializer_class = CompanySerializer


class BidViewSet(viewsets.ModelViewSet):
	queryset = Bid.objects.all()
	serializer_class = BidSerializer
