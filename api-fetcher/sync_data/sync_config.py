"""
동기화 설정 파일

각 PostgreSQL 테이블별로 병합할 MongoDB 컬렉션과 동기화 옵션을 정의합니다.
"""

# ============================================================
# 공통 필드 정의
# ============================================================

# Notice 테이블에서 병합할 낙찰정보 필드
NOTICE_WIN_FIELDS = [
    "opengDate",
    "opengTm",
    "opengRsltDivNm",
    "fnlSucsfAmt",
    "fnlSucsfRt",
    "fnlSucsfDate",
    "fnlSucsfCorpNm",
    "fnlSucsfCorpCeoNm",
    "fnlSucsfCorpOfclNm",
    "fnlSucsfCorpBizrno",
    "fnlSucsfCorpAdrs",
    "fnlSucsfCorpContactTel",
    "cntrctCnclsSttusNm",
    "bidwinrDcsnMthdNm",
]

SYNC_CONFIGS = {
    # ============================================================
    # notice (기존 - 공사만)
    # ============================================================
    "notice": {
        "psql_table": "notice",
        "psql_pk": ("bidntceno", "bidntceord"),
        "merge_sources": [
            {
                "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한공사조회",
                "is_primary": True,  # 메인 컬렉션 (이 컬렉션의 is_synced 기준으로 동기화)
                "sync_flag": "is_synced",
                "join_keys": None,  # 메인이므로 join 불필요
                "projection": None,  # 전체 필드
            },
            {
                "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회",
                "is_primary": False,
                "sync_flag": "is_synced",
                "join_keys": ("bidNtceNo", "bidNtceOrd"),
                "projection": {"_id": 0},  # _id 제외하고 전체
                "synced_at_column": "bssamt_synced_at",  # 이 소스 데이터가 있으면 설정
            },
            {
                "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사",
                "is_primary": False,
                "sync_flag": "notice_is_synced",  # bid와 구분하기 위한 별도 플래그
                "join_keys": ("bidNtceNo", "bidNtceOrd"),
                "projection": {f: 1 for f in NOTICE_WIN_FIELDS},  # 특정 필드만
                "synced_at_column": "win_synced_at",  # 이 소스 데이터가 있으면 설정
            },
        ],
        "batch_size": 10000,
        "parallel": False,
    },

    # ============================================================
    # notice_unified (통합 - 공사/물품/외자/용역)
    # 4개 카테고리를 순차적으로 동기화
    # ============================================================
    "notice_unified": {
        "psql_table": "notice",
        "psql_pk": ("bidntceno", "bidntceord"),
        "multi_source": True,  # 다중 primary 소스 모드
        "categories": [
            # === 공사 ===
            {
                "bsns_div": "공사",
                "merge_sources": [
                    {
                        "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한공사조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                    {
                        "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회",
                        "is_primary": False,
                        "sync_flag": "is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {"_id": 0},
                        "synced_at_column": "bssamt_synced_at",
                    },
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사",
                        "is_primary": False,
                        "sync_flag": "notice_is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in NOTICE_WIN_FIELDS},
                        "synced_at_column": "win_synced_at",
                    },
                ],
            },
            # === 물품 ===
            {
                "bsns_div": "물품",
                "merge_sources": [
                    {
                        "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한물품조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                    {
                        "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한물품기초금액조회",
                        "is_primary": False,
                        "sync_flag": "is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {"_id": 0},
                        "synced_at_column": "bssamt_synced_at",
                    },
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품",
                        "is_primary": False,
                        "sync_flag": "notice_is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in NOTICE_WIN_FIELDS},
                        "synced_at_column": "win_synced_at",
                    },
                ],
            },
            # === 외자 ===
            {
                "bsns_div": "외자",
                "merge_sources": [
                    {
                        "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한외자조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자",
                        "is_primary": False,
                        "sync_flag": "notice_is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in NOTICE_WIN_FIELDS},
                        "synced_at_column": "win_synced_at",
                    },
                ],
            },
            # === 용역 ===
            {
                "bsns_div": "용역",
                "merge_sources": [
                    {
                        "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한용역조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                    {
                        "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한용역기초금액조회",
                        "is_primary": False,
                        "sync_flag": "is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {"_id": 0},
                        "synced_at_column": "bssamt_synced_at",
                    },
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역",
                        "is_primary": False,
                        "sync_flag": "notice_is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in NOTICE_WIN_FIELDS},
                        "synced_at_column": "win_synced_at",
                    },
                ],
            },
        ],
        "batch_size": 10000,
        "parallel": False,
    },
    "company": {
        "psql_table": "company",
        "psql_pk": ("bizno",),
        "merge_sources": [
            {
                "collection_name": "사용자정보서비스.조달업체기본정보",
                "is_primary": True,
                "sync_flag": "is_synced",
                "join_keys": None,
                "projection": None,
            },
        ],
        "batch_size": 10000,
        "parallel": False,
    },
    "bid": {
        "psql_table": "bid",
        "psql_pk": ("bidntceno", "bidntceord", "bidprccorpbizrno"),
        "multi_source": True,  # 다중 카테고리 모드 활성화
        "categories": [
            # === 공사 ===
            {
                "name": "공사",
                "merge_sources": [
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            # === 물품 ===
            {
                "name": "물품",
                "merge_sources": [
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            # === 외자 ===
            {
                "name": "외자",
                "merge_sources": [
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            # === 용역 ===
            {
                "name": "용역",
                "merge_sources": [
                    {
                        "collection_name": "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
        ],
        "batch_size": 1000,
        "parallel": True,  # 병렬 처리 활성화
        "num_workers": "auto",  # 카테고리 내 ObjectId 분할 워커 수
        "foreign_key_check": {
            # 외래키 존재 여부 체크 (notice 테이블)
            "notice_keys": ("bidntceno", "bidntceord"),
            "company_key": "bidprccorpbizrno",
        },
        "default_bizrno": "__DEFAULT__",  # bizrno가 없을 때 기본값
    },
    "reserve_price_range": {
        "psql_table": "reserve_price_range",
        "psql_pk": ("bidntceno", "bidntceord", "range_no"),
        "merge_sources": [
            {
                "collection_name": "낙찰정보서비스.개찰결과공사예비가격상세목록조회",
                "is_primary": True,
                "sync_flag": "is_synced",
                "join_keys": None,
                "projection": None,
            },
        ],
        "batch_size": 10000,
        "parallel": False,
        "field_aliases": [
            # (PostgreSQL 필드명, MongoDB 필드명)
            ("range_no", "compnoRsrvtnPrceSno"),
        ],
    },
    "notice_industry_type": {
        "psql_table": "notice_industry_type",
        "psql_pk": ("bidntceno", "bidntceord", "lmtgrpno", "lmtsno"),
        "merge_sources": [
            {
                "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회",
                "is_primary": True,
                "sync_flag": "is_synced",
                "join_keys": None,
                "projection": None,
            },
        ],
        "batch_size": 10000,
        "parallel": False,
        "preprocess": "notice_industry_type",  # 전처리 함수 이름
    },
    "company_industry_type": {
        "psql_table": "company_industry_type",
        "psql_pk": ("bizno", "indstrytycd"),
        "merge_sources": [
            {
                "collection_name": "사용자정보서비스.조달업체업종정보조회",
                "is_primary": True,
                "sync_flag": "is_synced",
                "join_keys": None,
                "projection": None,
            },
        ],
        "batch_size": 10000,
        "parallel": False,
    },
    "institution": {
        "psql_table": "institution",
        "psql_pk": ("dminsttcd",),
        "merge_sources": [
            {
                "collection_name": "사용자정보서비스.수요기관정보조회",
                "is_primary": True,
                "sync_flag": "is_synced",
                "join_keys": None,
                "projection": None,
            },
        ],
        "batch_size": 10000,
        "parallel": False,
    },
    "notice_region": {
        "psql_table": "notice_region",
        "psql_pk": ("bidntceno", "bidntceord", "lmtsno"),
        "merge_sources": [
            {
                "collection_name": "입찰공고정보서비스.입찰공고목록정보에대한참가가능지역정보조회",
                "is_primary": True,
                "sync_flag": "is_synced",
                "join_keys": None,
                "projection": None,
            },
        ],
        "batch_size": 10000,
        "parallel": False,
    },
}


def get_config(table_name: str) -> dict:
    """
    테이블명으로 동기화 설정 반환

    Args:
        table_name: PostgreSQL 테이블명 (notice, company, bid, reserve_price_range)

    Returns:
        해당 테이블의 동기화 설정 딕셔너리

    Raises:
        ValueError: 유효하지 않은 테이블명
    """
    if table_name not in SYNC_CONFIGS:
        raise ValueError(
            f"Invalid table name: {table_name}. "
            f"Available: {', '.join(SYNC_CONFIGS.keys())}"
        )
    return SYNC_CONFIGS[table_name]


def get_primary_source(config: dict) -> dict:
    """
    설정에서 메인 컬렉션 정보 반환

    Args:
        config: SYNC_CONFIGS에서 가져온 테이블 설정

    Returns:
        is_primary=True인 merge_source 딕셔너리

    Raises:
        ValueError: 메인 컬렉션이 정의되지 않음
    """
    for source in config["merge_sources"]:
        if source.get("is_primary"):
            return source
    raise ValueError("No primary source defined in config")
