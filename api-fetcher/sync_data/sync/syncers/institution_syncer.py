"""
InstitutionSyncer - Institution 테이블 동기화

사용자정보서비스.수요기관정보조회 컬렉션을 institution 테이블로 동기화합니다.
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import SingleProcessSyncStrategy


class InstitutionSyncer(BaseSyncer):
    """
    Institution 테이블 동기화 클래스

    단일 컬렉션을 수요기관 정보 테이블로 동기화합니다.
    """

    def __init__(self, schema: str = None, test_limit: int = None):
        super().__init__("institution", schema=schema, test_limit=test_limit)
        self.strategy = SingleProcessSyncStrategy()

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()
        self.strategy.execute(self)
        self.print_summary()
