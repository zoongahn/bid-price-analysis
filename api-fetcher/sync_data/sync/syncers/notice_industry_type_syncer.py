"""
NoticeIndustryTypeSyncer - NoticeIndustryType 테이블 동기화

입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회 컬렉션을
notice_industry_type 테이블로 동기화합니다.

특징:
- lcnsLmtNm 필드 전처리 (name/code 분리)
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import SingleProcessSyncStrategy


class NoticeIndustryTypeSyncer(BaseSyncer):
    """
    NoticeIndustryType 테이블 동기화 클래스

    공고별 업종 제한 정보를 동기화합니다.
    """

    def __init__(self, schema: str = None, test_limit: int = None):
        super().__init__("notice_industry_type", schema=schema, test_limit=test_limit)
        self.strategy = SingleProcessSyncStrategy()

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()
        self.strategy.execute(self)
        self.print_summary()
