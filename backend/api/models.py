from django.db import models

class Notice(models.Model):
	공고번호 = models.CharField(max_length=50, unique=True)
	입찰년도 = models.IntegerField()
	공고제목 = models.TextField()
	발주처 = models.TextField()
	지역제한 = models.CharField(max_length=50)
	기초금액 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
	예정가격 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
	예가범위 = models.CharField(max_length=50, null=True, blank=True)
	A값 = models.DecimalField(max_digits=15, decimal_places=2)
	투찰률 = models.DecimalField(max_digits=5, decimal_places=3, null=True, blank=True)
	참여업체수 = models.IntegerField()
	공고구분표시 = models.CharField(max_length=100, null=True, blank=True)
	정답사정률 = models.DecimalField(max_digits=10, decimal_places=5, null=True, blank=True)

	class Meta:
		db_table = "notices"  # 실제 데이터가 존재하는 테이블명으로 변경

	def __str__(self):
		return f"{self.공고번호} - {self.공고제목}"

class Company(models.Model):
	사업자등록번호 = models.CharField(max_length=20, unique=True)
	업체명 = models.CharField(max_length=255, unique=True)
	대표명 = models.CharField(max_length=30, null=True, blank=True)

	class Meta:
		db_table = "companies"  # 실제 데이터가 존재하는 테이블명으로 변경

	def __str__(self):
		return self.업체명

class Bid(models.Model):
	notice = models.ForeignKey(Notice, on_delete=models.CASCADE)
	company = models.ForeignKey(Company, on_delete=models.CASCADE)
	순위 = models.IntegerField()
	투찰금액 = models.DecimalField(max_digits=20, decimal_places=2, null=True)
	가격점수 = models.DecimalField(max_digits=5, decimal_places=2, null=True)
	예가대비투찰률 = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	기초대비투찰률 = models.DecimalField(max_digits=20, decimal_places=4, null=True)
	기초대비사정률 = models.DecimalField(max_digits=13, decimal_places=5, null=True)
	추첨번호 = models.CharField(max_length=30, null=True)
	낙찰여부 = models.BooleanField(default=False)
	투찰일시 = models.DateTimeField(null=True)
	비고 = models.CharField(max_length=100, null=True, blank=True)

	class Meta:
		db_table = "bids"  # 실제 데이터가 존재하는 테이블명으로 변경

	def __str__(self):
		return f"{self.notice.공고번호} - {self.company.업체명} ({self.순위}위)"
