"""
통합 동기화 실행 스크립트 (객체지향 리팩토링 버전)

Usage:
    # 단일 테이블 동기화
    python -m sync_data.main_sync notice
    python -m sync_data.main_sync company
    python -m sync_data.main_sync bid
    python -m sync_data.main_sync reserve_price_range

    # 모든 테이블 동기화 (순서대로)
    python -m sync_data.main_sync all
"""

import sys
import os
import argparse

# Python 경로에 프로젝트 루트 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from sync_data.sync.syncer_factory import create_syncer


def sync_table(table_name: str, schema: str = None, test_limit: int = None):
    """
    단일 테이블 동기화

    Args:
        table_name: 테이블명
        schema: PostgreSQL 스키마명 (기본값: None = public)
        test_limit: 테스트 모드 시 카테고리당 최대 동기화 건수 (기본값: None = 제한 없음)
    """
    schema_info = f" (schema: {schema})" if schema else ""
    test_info = f" [TEST: {test_limit:,}건/카테고리]" if test_limit else ""
    print(f"\n{'=' * 80}")
    print(f"📊 {table_name.upper()} 테이블 동기화 시작{schema_info}{test_info}")
    print(f"{'=' * 80}\n")

    syncer = None
    try:
        # SyncerFactory를 통해 적절한 Syncer 생성
        kwargs = {}
        if test_limit is not None:
            kwargs["test_limit"] = test_limit
        syncer = create_syncer(table_name, schema=schema, **kwargs)
        syncer.sync()

    except Exception as e:
        print(f"\n❌ [{table_name}] 동기화 실패: {e}")
        raise
    finally:
        if syncer is not None:
            syncer.close()


def sync_all(schema: str = None, test_limit: int = None):
    """
    모든 테이블을 올바른 순서로 동기화

    Args:
        schema: PostgreSQL 스키마명 (기본값: None = public)
        test_limit: 테스트 모드 시 카테고리당 최대 동기화 건수 (기본값: None = 제한 없음)

    순서:
    1. notice (공고 - FK 참조됨)
    2. company (업체 - FK 참조됨)
    3. institution (수요기관)
    4. bid (투찰 - notice, company 참조)
    5. reserve_price_range (예비가격 - notice 참조)
    6. notice_industry_type (공고 면허제한정보 - notice 참조)
    7. notice_region (공고 참가가능지역 - notice 참조)
    8. company_industry_type (업체 업종정보 - company 참조)
    """
    tables = ["notice", "company", "institution", "bid", "reserve_price_range", "notice_industry_type", "notice_region", "company_industry_type"]

    schema_info = f" (schema: {schema})" if schema else ""
    test_info = f" [TEST: {test_limit:,}건/카테고리]" if test_limit else ""

    print("\n" + "=" * 80)
    print(f"🚀 전체 테이블 동기화 시작{schema_info}{test_info}")
    print("=" * 80)
    print(f"동기화 순서: {' → '.join(tables)}")
    print("=" * 80 + "\n")

    for table in tables:
        try:
            sync_table(table, schema=schema, test_limit=test_limit)
        except Exception as e:
            print(f"\n❌ 전체 동기화 중단: {table} 테이블에서 오류 발생")
            print(f"   오류 내용: {e}")
            sys.exit(1)

    print("\n" + "=" * 80)
    print("🎉 모든 테이블 동기화 완료!")
    print("=" * 80 + "\n")


def main():
    parser = argparse.ArgumentParser(
        description="MongoDB → PostgreSQL 동기화 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python main_sync.py notice                  # notice 테이블만 (공사)
  python main_sync.py notice_unified          # notice 통합 (공사/물품/외자/용역)
  python main_sync.py company                 # company 테이블만
  python main_sync.py institution             # institution 테이블만
  python main_sync.py bid                     # bid 테이블만 (병렬 처리)
  python main_sync.py reserve_price_range     # reserve_price_range 테이블만
  python main_sync.py notice_industry_type    # notice_industry_type 테이블만
  python main_sync.py notice_region           # notice_region 테이블만
  python main_sync.py company_industry_type   # company_industry_type 테이블만
  python main_sync.py all                     # 모든 테이블 (순서대로)

주의사항:
  - bid, reserve_price_range, notice_industry_type, notice_region은 notice 동기화 후 실행하세요
  - bid, company_industry_type는 company 동기화 후 실행하세요
  - 'all' 명령은 올바른 순서로 자동 실행합니다
  - notice_unified는 4개 카테고리(공사/물품/외자/용역)를 순차 동기화합니다
        """
    )
    parser.add_argument(
        "table",
        choices=["notice", "notice_unified", "company", "institution", "bid", "reserve_price_range", "notice_industry_type", "notice_region", "company_industry_type", "all"],
        help="동기화할 테이블명 또는 'all'"
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="data",
        help="PostgreSQL 스키마명 (기본값: data)"
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="테스트 모드: 각 카테고리당 10,000건만 동기화"
    )
    parser.add_argument(
        "--test-limit",
        type=int,
        default=10000,
        help="테스트 모드 시 카테고리당 최대 건수 (기본값: 10000)"
    )

    args = parser.parse_args()

    # 테스트 모드 처리
    test_limit = args.test_limit if args.test else None

    if args.table == "all":
        sync_all(schema=args.schema, test_limit=test_limit)
    else:
        sync_table(args.table, schema=args.schema, test_limit=test_limit)


if __name__ == "__main__":
    main()
