"""
NoticeRegionSyncer - 공고 참가가능지역 테이블 동기화

입찰공고정보서비스.입찰공고목록정보에대한참가가능지역정보조회 컬렉션을
notice_region 테이블로 동기화합니다.
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import SingleProcessSyncStrategy


class NoticeRegionSyncer(BaseSyncer):
    """
    NoticeRegion 테이블 동기화 클래스

    단일 컬렉션을 공고 참가가능지역 정보 테이블로 동기화합니다.
    """

    def __init__(self, schema: str = None, test_limit: int = None):
        super().__init__("notice_region", schema=schema, test_limit=test_limit)
        self.strategy = SingleProcessSyncStrategy()

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()
        self.strategy.execute(self)
        self.print_summary()
