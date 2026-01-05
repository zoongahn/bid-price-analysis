"""
동기화 전처리 함수 모음

특정 테이블에 대한 커스텀 데이터 전처리 로직을 정의합니다.
"""

from typing import Any


def preprocess_notice_industry_type(doc: dict[str, Any]) -> dict[str, Any]:
    """
    notice_industry_type 전처리

    lcnsLmtNm 필드를 '/' 기준으로 분리:
    - "도장공사업/0010" → lcnslmtnm_name="도장공사업", lcnslmtnm_code="0010"
    - "/" 가 없으면 전체를 name에 저장, code는 None

    Args:
        doc: MongoDB 문서

    Returns:
        전처리된 문서
    """
    processed_doc = doc.copy()

    lcns_lmt_nm = doc.get("lcnsLmtNm", "")

    if lcns_lmt_nm and "/" in lcns_lmt_nm:
        # "/" 기준으로 분리 (오른쪽부터 탐색)
        parts = lcns_lmt_nm.rsplit("/", 1)  # 오른쪽부터 최대 1번만 분리
        processed_doc["lcnslmtnm_name"] = parts[0].strip()
        processed_doc["lcnslmtnm_code"] = parts[1].strip() if len(parts) > 1 else None
    else:
        # "/" 가 없으면 전체를 name에
        processed_doc["lcnslmtnm_name"] = lcns_lmt_nm
        processed_doc["lcnslmtnm_code"] = None

    # 원본 필드 제거 (PostgreSQL에는 없음)
    processed_doc.pop("lcnsLmtNm", None)

    return processed_doc


# 다른 전처리 함수들 추가 가능
# def preprocess_other_table(doc: dict[str, Any]) -> dict[str, Any]:
#     ...
