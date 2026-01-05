"""
후처리 스크립트 패키지

동기화 완료 후 실행되는 UPDATE 쿼리 스크립트들입니다.
GENERATED 컬럼이 아닌, 다른 테이블 JOIN이 필요한 컬럼들을 계산합니다.

사용법:
    # 개별 실행
    python -m sync_data.postprocess.update_bid_rates
    python -m sync_data.postprocess.update_company_stats
    python -m sync_data.postprocess.update_notice_stats
    python -m sync_data.postprocess.update_industry_type_classification

    # 전체 실행
    python -m sync_data.postprocess.run_all
"""

from .update_bid_rates import update_bid_rates
from .update_company_stats import update_company_stats
from .update_notice_stats import update_notice_stats
from .update_industry_type_classification import update_classification_info

__all__ = [
    "update_bid_rates",
    "update_company_stats",
    "update_notice_stats",
    "update_classification_info",
]
