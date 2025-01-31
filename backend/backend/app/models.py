from django.db import models

class Notice(models.Model):
    공고번호 = models.CharField(max_length=50, unique=True)
    입찰년도 = models.DecimalField(max_digits=6, decimal_places=0)  # 정수형 처리
    공고제목 = models.TextField()
    발주처 = models.TextField()
    지역제한 = models.CharField(max_length=50)
    기초금액 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    예정가격 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    예가범위 = models.CharField(max_length=50, null=True, blank=True)
    A값 = models.DecimalField(max_digits=15, decimal_places=2)
    투찰률 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    참여업체수 = models.IntegerField()
    공고구분표시 = models.CharField(max_length=100, null=True, blank=True)
    정답사정률 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)

    def __str__(self):
        return f"{self.공고번호} - {self.공고제목}"


class Company(models.Model):
    사업자등록번호 = models.CharField(max_length=20, unique=True)
    업체명 = models.CharField(max_length=255)
    대표명 = models.CharField(max_length=30, null=True, blank=True)

    def __str__(self):
        return f"{self.사업자등록번호} - {self.업체명}"


class Bid(models.Model):
    notice = models.ForeignKey(Notice, on_delete=models.CASCADE)  # 공고번호 참조
    company = models.ForeignKey(Company, on_delete=models.CASCADE)  # 업체정보 참조
    순위 = models.IntegerField()
    투찰금액 = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    가격점수 = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    예가대비투찰률 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    기초대비투찰률 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    기초대비사정률 = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    추첨번호 = models.CharField(max_length=30, null=True, blank=True)
    낙찰여부 = models.BooleanField(default=False)
    투찰일시 = models.DateTimeField(null=True, blank=True)
    비고 = models.CharField(max_length=100, null=True, blank=True)

    def __str__(self):
        return f"{self.company} - {self.순위}위"