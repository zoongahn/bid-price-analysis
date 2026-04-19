"""
SyncerFactory - Syncer 생성 팩토리

Factory Pattern을 사용하여 테이블명에 따라 적절한 Syncer 인스턴스를 생성합니다.
"""

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.syncers import (
    NoticeSyncer,
    NoticeUnifiedSyncer,
    CompanySyncer,
    BidSyncer,
    ReservePriceRangeSyncer,
    NoticeIndustryTypeSyncer,
    NoticeRegionSyncer,
    CompanyIndustryTypeSyncer,
    InstitutionSyncer,
)


class SyncerFactory:
    """
    Syncer 생성 팩토리 클래스

    테이블명을 받아서 해당하는 Syncer 인스턴스를 생성합니다.
    """

    # 테이블명 -> Syncer 클래스 매핑
    _SYNCER_MAP = {
        "notice": NoticeUnifiedSyncer,  # multi_source 구조 지원
        "company": CompanySyncer,
        "bid": BidSyncer,
        "reserve_price_range": ReservePriceRangeSyncer,
        "notice_industry_type": NoticeIndustryTypeSyncer,
        "notice_region": NoticeRegionSyncer,
        "company_industry_type": CompanyIndustryTypeSyncer,
        "institution": InstitutionSyncer,
    }

    @classmethod
    def create(cls, table_name: str, schema: str = None, **kwargs) -> BaseSyncer:
        """
        테이블명으로 Syncer 인스턴스 생성

        Args:
            table_name: PostgreSQL 테이블명
            schema: PostgreSQL 스키마명 (기본값: 'data')
            **kwargs: Syncer 생성자에 전달할 추가 인자
                      예: BidSyncer의 경우 num_workers 전달 가능

        Returns:
            BaseSyncer 인스턴스

        Raises:
            ValueError: 지원하지 않는 테이블명

        Examples:
            >>> syncer = SyncerFactory.create("notice")
            >>> syncer.sync()

            >>> syncer = SyncerFactory.create("notice", schema="data")
            >>> syncer.sync()

            >>> bid_syncer = SyncerFactory.create("bid", num_workers=16, schema="data")
            >>> bid_syncer.sync()
        """
        syncer_class = cls._SYNCER_MAP.get(table_name)

        if syncer_class is None:
            available_tables = ", ".join(cls._SYNCER_MAP.keys())
            raise ValueError(
                f"지원하지 않는 테이블명: {table_name}\n"
                f"사용 가능한 테이블: {available_tables}"
            )

        return syncer_class(schema=schema, **kwargs)

    @classmethod
    def get_available_tables(cls) -> list[str]:
        """
        동기화 가능한 테이블 목록 반환

        Returns:
            테이블명 리스트
        """
        return list(cls._SYNCER_MAP.keys())

    @classmethod
    def is_supported(cls, table_name: str) -> bool:
        """
        지원하는 테이블인지 확인

        Args:
            table_name: 테이블명

        Returns:
            지원하면 True, 아니면 False
        """
        return table_name in cls._SYNCER_MAP


def create_syncer(table_name: str, schema: str = None, **kwargs) -> BaseSyncer:
    """
    Syncer 생성 헬퍼 함수

    SyncerFactory.create()의 간편 래퍼 함수입니다.

    Args:
        table_name: PostgreSQL 테이블명
        schema: PostgreSQL 스키마명 (기본값: 'data')
        **kwargs: Syncer 생성자에 전달할 추가 인자

    Returns:
        BaseSyncer 인스턴스

    Examples:
        >>> syncer = create_syncer("notice")
        >>> syncer.sync()

        >>> syncer = create_syncer("notice", schema="data")
        >>> syncer.sync()
    """
    return SyncerFactory.create(table_name, schema=schema, **kwargs)
