from rest_framework import serializers
from .models import Notice, Company, Bid


class NoticeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notice
		fields = "__all__"


class CompanySerializer(serializers.ModelSerializer):
	class Meta:
		model = Company
		fields = "__all__"


class BidSerializer(serializers.ModelSerializer):
	class Meta:
		model = Bid
		fields = "__all__"
