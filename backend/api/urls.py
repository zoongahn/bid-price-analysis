from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NoticeViewSet, CompanyViewSet, BidViewSet

router = DefaultRouter()
router.register(r'notices', NoticeViewSet)
router.register(r'companies', CompanyViewSet)
router.register(r'bids', BidViewSet)

urlpatterns = [
	path('', include(router.urls)),
]
