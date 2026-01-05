"""
NoticeSyncer - Notice 테이블 동기화

3개의 MongoDB 컬렉션을 병합하여 notice 테이블로 동기화합니다:
1. 입찰공고정보서비스.입찰공고목록정보에대한공사조회 (메인)
2. 입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회
3. 공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보 (일부 필드)
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import SingleProcessSyncStrategy, ParallelSyncStrategy


class NoticeSyncer(BaseSyncer):
    """
    Notice 테이블 동기화 클래스

    다중 컬렉션 병합을 통해 공고 정보를 동기화합니다.
    """

    def __init__(self, num_workers: int | str = None, schema: str = None, test_limit: int = None):
        """
        Args:
            num_workers: 병렬 처리 워커 수 (None=단일 프로세스, "auto"=CPU*2, 숫자=지정)
            schema: PostgreSQL 스키마명
            test_limit: 테스트 모드 시 최대 동기화 건수 (기본값: None = 제한 없음)
        """
        super().__init__("notice", schema=schema, test_limit=test_limit)

        # 병렬 모드 선택
        if num_workers is not None:
            self.strategy = ParallelSyncStrategy(num_workers)
            self._parallel_mode = True
        else:
            self.strategy = SingleProcessSyncStrategy()
            self._parallel_mode = False

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()
        self.strategy.execute(self)
        self.print_summary()

    def print_summary(self):
        """동기화 결과 요약 출력"""
        mode = "병렬" if self._parallel_mode else "단일 프로세스"
        print(f"\n{'=' * 80}")
        print(f"✅ [{self.schema}.notice] {mode} 동기화 완료")
        print(f"   - 총 동기화: {self.total_synced:,}건")
        if self.total_skip > 0:
            print(f"   - Skip: {self.total_skip:,}건")
        print(f"{'=' * 80}\n")
