# pagination.py (예: api/pagination.py)
from rest_framework.pagination import PageNumberPagination


class NoticesPagination(PageNumberPagination):
	page_size = 500  # 기본 페이지 크기 (500개씩)
	page_size_query_param = "page_size"  # URL에서 ?page_size=100 식으로 변경 가능


class CompaniesPagination(PageNumberPagination):
	page_size = 500  # 기본 페이지 크기 (500개씩)
	page_size_query_param = "page_size"  # URL에서 ?page_size=100 식으로 변경 가능


class BidsPagination(PageNumberPagination):
	page_size = 500  # 기본 페이지 크기 (500개씩)
	page_size_query_param = "page_size"  # URL에서 ?page_size=100 식으로 변경 가능
	max_page_size = 1000
