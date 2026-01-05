"""
입찰공고 면허제한정보 동기화 예시

MongoDB: 입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회
PostgreSQL: notice_industry_type
PK: bidntceno, bidntceord, lmtgrpno, lmtsno (4개 컬럼)

특징:
- lcnsLmtNm 필드를 "/" 기준으로 분리
  예: "도장공사업/0010" → lcnslmtnm_name="도장공사업", lcnslmtnm_code="0010"
"""

import sys
from pathlib import Path

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from sync_data.sync.simple_sync import sync_collection_to_table
from sync_data.sync.preprocessors import preprocess_notice_industry_type


def sync_notice_industry_type():
    """
    입찰공고 면허제한정보(업종) 동기화

    4개 컬럼으로 구성된 복합 Primary Key 사용
    lcnsLmtNm 필드 전처리 적용
    """
    print("\n" + "=" * 80)
    print("입찰공고 면허제한정보(업종) 동기화")
    print("=" * 80)
    print("MongoDB 컬렉션: 입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회")
    print("PostgreSQL 테이블: notice_industry_type")
    print("Primary Key: (bidntceno, bidntceord, lmtgrpno, lmtsno)")
    print("전처리: lcnsLmtNm → lcnslmtnm_name, lcnslmtnm_code 분리")
    print("=" * 80 + "\n")

    sync_collection_to_table(
        mongo_collection_name="입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회",
        psql_table_name="notice_industry_type",
        psql_pk=("bidntceno", "bidntceord", "lmtgrpno", "lmtsno"),
        batch_size=100000,
        sync_flag="is_synced",
        preprocess_func=preprocess_notice_industry_type,  # 전처리 함수 추가
    )


if __name__ == "__main__":
    sync_notice_industry_type()
