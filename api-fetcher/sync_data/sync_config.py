"""
동기화 설정 파일

각 PostgreSQL 테이블별로 병합할 MongoDB 컬렉션과 동기화 옵션을 정의합니다.
"""

# ============================================================
# 공통 필드 정의
# ============================================================

# 개찰결과 API (오퍼레이션 5,6,7,8) 필드 매핑
# MongoDB 필드명 → PostgreSQL 컬럼명
OPENG_RESULT_FIELD_MAPPING = {
    "opengDt": "actual_opengdt",  # 실제 개찰일시 (입찰공고의 opengDt는 예정 개찰일시)
    "inptDt": "openg_result_inptdt",  # 개찰결과 입력일시 (기초금액의 inptDt는 inptdt)
}

# 개찰결과 API 동기화 대상 필드
OPENG_RESULT_FIELDS = [
    "opengDt",  # → actual_opengdt로 매핑됨
    "inptDt",  # → openg_result_inptdt로 매핑됨
    "bidClsfcNo",
    "rbidNo",
    "prtcptCnum",
    "opengCorpInfo",
    "progrsDivCdNm",
    "rsrvtnPrceFileExistnceYn",
    "opengRsltNtcCntnts",
]

# Notice 테이블에서 병합할 낙찰정보 필드 (레거시 - 더 이상 사용 안함)
# 개찰결과 API (낙찰정보서비스 오퍼레이션 5,6,7,8)로 대체됨
# NOTICE_WIN_FIELDS = [
#     "opengDate",
#     "opengTm",
#     "opengRsltDivNm",
#     "fnlSucsfAmt",
#     "fnlSucsfRt",
#     "fnlSucsfDate",
#     "fnlSucsfCorpNm",
#     "fnlSucsfCorpCeoNm",
#     "fnlSucsfCorpOfclNm",
#     "fnlSucsfCorpBizrno",
#     "fnlSucsfCorpAdrs",
#     "fnlSucsfCorpContactTel",
#     "cntrctCnclsSttusNm",
#     "bidwinrDcsnMthdNm",
# ]

SYNC_CONFIGS = {
    # ============================================================
    # notice (통합 - 공사/물품/외자/용역)
    # 4개 카테고리를 순차적으로 동기화
    # ============================================================
    "notice": {
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
                        "collection_name": "낙찰정보서비스.개찰결과공사목록조회",
                        "is_primary": False,
                        "sync_flag": "is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in OPENG_RESULT_FIELDS},
                        "field_mapping": OPENG_RESULT_FIELD_MAPPING,
                        "synced_at_column": "openg_result_synced_at",
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
                        "collection_name": "낙찰정보서비스.개찰결과물품목록조회",
                        "is_primary": False,
                        "sync_flag": "is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in OPENG_RESULT_FIELDS},
                        "field_mapping": OPENG_RESULT_FIELD_MAPPING,
                        "synced_at_column": "openg_result_synced_at",
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
                        "collection_name": "낙찰정보서비스.개찰결과외자목록조회",
                        "is_primary": False,
                        "sync_flag": "is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in OPENG_RESULT_FIELDS},
                        "field_mapping": OPENG_RESULT_FIELD_MAPPING,
                        "synced_at_column": "openg_result_synced_at",
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
                        "collection_name": "낙찰정보서비스.개찰결과용역목록조회",
                        "is_primary": False,
                        "sync_flag": "is_synced",
                        "join_keys": ("bidNtceNo", "bidNtceOrd"),
                        "projection": {f: 1 for f in OPENG_RESULT_FIELDS},
                        "field_mapping": OPENG_RESULT_FIELD_MAPPING,
                        "synced_at_column": "openg_result_synced_at",
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
            {
                "collection_name": "사업자등록정보진위확인및상태조회서비스.상태조회",
                "is_primary": False,
                "sync_flag": "is_synced",
                "join_keys": ("bizno", "b_no"),  # (primary 필드, secondary 필드)
                "projection": {
                    "b_stt": 1,
                    "b_stt_cd": 1,
                    "tax_type": 1,
                    "tax_type_cd": 1,
                    "end_dt": 1,
                    "utcc_yn": 1,
                    "tax_type_change_dt": 1,
                    "invoice_apply_dt": 1,
                    "rbf_tax_type": 1,
                    "rbf_tax_type_cd": 1,
                },
                "field_mapping": {
                    # API 필드 → PostgreSQL 필드
                    "b_stt": "bizstt_b_stt",
                    "b_stt_cd": "bizstt_b_stt_cd",
                    "tax_type": "bizstt_tax_type",
                    "tax_type_cd": "bizstt_tax_type_cd",
                    "end_dt": "bizstt_end_dt",
                    "utcc_yn": "bizstt_utcc_yn",
                    "tax_type_change_dt": "bizstt_tax_type_change_dt",
                    "invoice_apply_dt": "bizstt_invoice_apply_dt",
                    "rbf_tax_type": "bizstt_rbf_tax_type",
                    "rbf_tax_type_cd": "bizstt_rbf_tax_type_cd",
                },
                "synced_at_column": "bizstt_status_updated_at",
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
        "total_workers": 32,  # 총 워커 수 (건수 비율에 따라 카테고리별 동적 배분)
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
        "multi_source": True,  # 다중 primary 소스 모드 (공사/물품/용역/외자)
        "categories": [
            # === 공사 ===
            {
                "bsns_div": "공사",
                "merge_sources": [
                    {
                        "collection_name": "낙찰정보서비스.개찰결과공사예비가격상세목록조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            # === 물품 ===
            {
                "bsns_div": "물품",
                "merge_sources": [
                    {
                        "collection_name": "낙찰정보서비스.개찰결과물품예비가격상세목록조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            # === 용역 ===
            {
                "bsns_div": "용역",
                "merge_sources": [
                    {
                        "collection_name": "낙찰정보서비스.개찰결과용역예비가격상세목록조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            # === 외자 ===
            {
                "bsns_div": "외자",
                "merge_sources": [
                    {
                        "collection_name": "낙찰정보서비스.개찰결과외자예비가격상세목록조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
        ],
        "batch_size": 10000,
        "parallel": True,  # 4개 카테고리 병렬 처리
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
    # ============================================================
    # bid (개찰결과 - 개찰완료/유찰/재입찰 통합)
    # 3개 컬렉션을 순차적으로 동기화
    # ============================================================
    "bid": {
        "psql_table": "bid",
        "psql_pk": ("bidntceno", "bidntceord", "bidclsfcno", "rbidno", "prcbdrbizno"),
        "multi_source": True,
        "categories": [
            {
                "name": "개찰완료",
                "merge_sources": [
                    {
                        "collection_name": "낙찰정보서비스.개찰결과개찰완료목록조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            {
                "name": "유찰",
                "merge_sources": [
                    {
                        "collection_name": "낙찰정보서비스.개찰결과유찰목록조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
            },
            {
                "name": "재입찰",
                "merge_sources": [
                    {
                        "collection_name": "낙찰정보서비스.개찰결과재입찰목록조회",
                        "is_primary": True,
                        "sync_flag": "is_synced",
                        "join_keys": None,
                        "projection": None,
                    },
                ],
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
