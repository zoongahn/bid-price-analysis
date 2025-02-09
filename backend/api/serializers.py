import decimal
import math
from rest_framework import serializers
from .models import Notice, Company, Bid


class NaNSafeFloatField(serializers.FloatField):
	def to_representation(self, value):
		# 값이 None이면 None 반환
		if value is None:
			return None
		# 값이 float 타입이고 NaN이면 None 반환
		if isinstance(value, float) and math.isnan(value):
			return None
		# 값이 Decimal 타입이면서 NaN이면 None 반환
		if isinstance(value, decimal.Decimal) and value.is_nan():
			return None
		return super().to_representation(value)


class NoticeSerializer(serializers.ModelSerializer):
	class Meta:
		model = Notice
		fields = "__all__"


class CompanySerializer(serializers.ModelSerializer):
	투찰횟수 = serializers.IntegerField(read_only=True)

	class Meta:
		model = Company
		fields = ('사업자등록번호', '업체명', '대표명', '투찰횟수')


class BidSerializer(serializers.ModelSerializer):
	가격점수 = NaNSafeFloatField()
	예가대비투찰률 = NaNSafeFloatField()
	기초대비투찰률 = NaNSafeFloatField()
	기초대비사정률 = NaNSafeFloatField()

	notice = NoticeSerializer(read_only=True)
	company = CompanySerializer(read_only=True)

	class Meta:
		model = Bid
		fields = "__all__"
