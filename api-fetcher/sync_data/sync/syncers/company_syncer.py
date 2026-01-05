"""
CompanySyncer - Company 테이블 동기화

사용자정보서비스.조달업체기본정보 컬렉션을 company 테이블로 동기화합니다.
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import SingleProcessSyncStrategy


class CompanySyncer(BaseSyncer):
    """
    Company 테이블 동기화 클래스

    단일 컬렉션을 조달업체 정보 테이블로 동기화합니다.
    """

    def __init__(self, schema: str = None, test_limit: int = None):
        super().__init__("company", schema=schema, test_limit=test_limit)
        self.strategy = SingleProcessSyncStrategy()

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()
        self.strategy.execute(self)
        self.print_summary()
