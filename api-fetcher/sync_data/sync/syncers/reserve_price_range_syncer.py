"""
ReservePriceRangeSyncer - ReservePriceRange 테이블 동기화

낙찰정보서비스.개찰결과공사예비가격상세목록조회 컬렉션을
reserve_price_range 테이블로 동기화합니다.

특징:
- 필드명 매핑 (range_no ← compnoRsrvtnPrceSno)
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import SingleProcessSyncStrategy


class ReservePriceRangeSyncer(BaseSyncer):
    """
    ReservePriceRange 테이블 동기화 클래스

    예비가격 범위 정보를 동기화합니다.
    """

    def __init__(self, schema: str = None, test_limit: int = None):
        super().__init__("reserve_price_range", schema=schema, test_limit=test_limit)
        self.strategy = SingleProcessSyncStrategy()

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()
        self.strategy.execute(self)
        self.print_summary()
