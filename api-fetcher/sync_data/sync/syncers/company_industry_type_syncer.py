"""
CompanyIndustryTypeSyncer - CompanyIndustryType 테이블 동기화

사용자정보서비스.조달업체업종정보조회 컬렉션을
company_industry_type 테이블로 동기화합니다.

특징:
- 업체별 업종 정보 (복수 업종 가능)
- 대표업종 여부 포함
- company 테이블 FK 체크 (존재하는 업체만 동기화)
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import SingleProcessSyncStrategy


class CompanyIndustryTypeSyncer(BaseSyncer):
    """
    CompanyIndustryType 테이블 동기화 클래스

    업체별 업종 정보를 동기화합니다.
    company 테이블에 존재하는 업체만 동기화합니다.
    """

    def __init__(self, schema: str = None, test_limit: int = None):
        super().__init__("company_industry_type", schema=schema, test_limit=test_limit)
        self.strategy = SingleProcessSyncStrategy()
        self.company_biznos = self._load_company_biznos()

    def _load_company_biznos(self) -> set:
        """company 테이블의 bizno 목록 로드"""
        self.psql_cur.execute(f"SELECT bizno FROM {self.schema}.company;")
        biznos = set(row[0] for row in self.psql_cur.fetchall())
        print(f"📋 company 테이블에서 {len(biznos):,}개 업체 로드 완료")
        return biznos

    def validate_row(self, row_dict: dict) -> bool:
        """company 테이블에 존재하는 업체인지 검증"""
        bizno = row_dict.get("bizno")
        return bizno in self.company_biznos

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()
        self.strategy.execute(self)
        self.print_summary()

    def print_summary(self):
        """동기화 결과 요약 출력"""
        print(f"\n{'=' * 80}")
        print(f"✅ [{self.schema}.company_industry_type] 동기화 완료")
        print(f"   - 총 동기화: {self.total_synced:,}건")
        if self.total_skip > 0:
            print(f"   - ⚠️  company 테이블에 없는 업체: {self.total_skip:,}건 skip")
        print(f"{'=' * 80}\n")
