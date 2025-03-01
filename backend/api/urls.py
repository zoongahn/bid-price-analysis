from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .view import *

router = DefaultRouter()
router.register(r'notices', NoticeViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'bids', BidViewSet, basename='bid')
router.register(r'by-notice', ByNoticeViewSet, basename='by-notice')
router.register(r'by-company', ByCompanyViewSet, basename='by-company')
router.register(r'api-info', ApiInfoViewSet, basename='api-info')


urlpatterns = [
	path('', include(router.urls)),
]


