"""
동기화 플래그 초기화 스크립트 (통합)

sync_config.py에서 설정을 읽어 MongoDB 컬렉션의 동기화 플래그를 제거합니다.
PostgreSQL 테이블 기준으로 관련 컬렉션의 플래그를 초기화합니다.

사용법:
    # 특정 테이블 관련 플래그 초기화
    python -m sync_data.scripts.reset_sync_flags notice
    python -m sync_data.scripts.reset_sync_flags bid
    python -m sync_data.scripts.reset_sync_flags company institution

    # 모든 플래그 초기화
    python -m sync_data.scripts.reset_sync_flags all

    # 확인만 (실제 초기화 없이)
    python -m sync_data.scripts.reset_sync_flags notice --dry-run

    # 현재 플래그 상태 확인
    python -m sync_data.scripts.reset_sync_flags --verify

    # 확인 없이 바로 실행
    python -m sync_data.scripts.reset_sync_flags all --force
"""

import sys
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from common.init_mongodb import init_mongodb
from sync_data.sync_config import SYNC_CONFIGS


def get_collection_flag_map() -> dict:
    """
    sync_config.py에서 테이블별 컬렉션-플래그 매핑 생성

    multi_source (categories) 구조도 지원합니다.

    Returns:
        dict: {table_name: [(collection_name, flag_name), ...]}
    """
    mapping = {}

    for table_name, config in SYNC_CONFIGS.items():
        mapping[table_name] = []

        # multi_source 모드 (notice_unified, bid)
        if config.get("multi_source") and config.get("categories"):
            for category in config["categories"]:
                for source in category.get("merge_sources", []):
                    collection_name = source["collection_name"]
                    sync_flag = source.get("sync_flag", "is_synced")
                    pair = (collection_name, sync_flag)
                    if pair not in mapping[table_name]:
                        mapping[table_name].append(pair)
        # 일반 모드
        elif config.get("merge_sources"):
            for source in config["merge_sources"]:
                collection_name = source["collection_name"]
                sync_flag = source.get("sync_flag", "is_synced")
                mapping[table_name].append((collection_name, sync_flag))

    return mapping


def get_all_collections() -> list:
    """
    모든 고유한 (컬렉션, 플래그) 쌍 반환

    Returns:
        list: [(collection_name, flag_name), ...]
    """
    mapping = get_collection_flag_map()
    all_pairs = set()

    for pairs in mapping.values():
        all_pairs.update(pairs)

    return sorted(all_pairs, key=lambda x: x[0])


def _reset_single_collection(db, collection_name: str, flag_name: str, dry_run: bool = False) -> tuple:
    """
    단일 컬렉션의 플래그 초기화 (병렬 처리용)

    Returns:
        tuple: (collection_name, flag_name, count, is_dry_run)
    """
    coll = db[collection_name]

    # 인덱스 힌트 (flag_name 인덱스 사용)
    index_hint = [(flag_name, 1)]

    if dry_run:
        # dry-run: count만 확인 (인덱스 활용)
        count = coll.count_documents({flag_name: True}, hint=index_hint)
        return (collection_name, flag_name, count, True)
    else:
        # 실제 초기화: count 확인 없이 바로 update_many (인덱스 힌트 사용)
        result = coll.update_many(
            {flag_name: True},
            {"$unset": {flag_name: ""}},
            hint=index_hint
        )
        return (collection_name, flag_name, result.modified_count, False)


def reset_flags_for_table(db, table_name: str, dry_run: bool = False) -> dict:
    """
    특정 테이블 관련 컬렉션의 플래그 초기화 (병렬 처리)

    Args:
        db: MongoDB 데이터베이스 객체
        table_name: 테이블명
        dry_run: True면 실제 초기화 없이 카운트만 확인

    Returns:
        dict: {collection_name: {flag: count}}
    """
    mapping = get_collection_flag_map()

    if table_name not in mapping:
        print(f"  [X] 알 수 없는 테이블: {table_name}")
        return {}

    results = {}
    sources = mapping[table_name]

    # 병렬 처리
    with ThreadPoolExecutor(max_workers=min(len(sources), 8)) as executor:
        futures = {
            executor.submit(_reset_single_collection, db, coll_name, flag_name, dry_run): (coll_name, flag_name)
            for coll_name, flag_name in sources
        }

        for future in as_completed(futures):
            coll_name, flag_name, count, is_dry = future.result()
            results.setdefault(coll_name, {})[flag_name] = count

            if is_dry:
                print(f"  [i] {coll_name}")
                print(f"      - {flag_name}: {count:,}건 (초기화 대상)")
            elif count > 0:
                print(f"  [v] {coll_name}")
                print(f"      - {flag_name} 제거: {count:,}건")
            else:
                print(f"  [-] {coll_name}")
                print(f"      - {flag_name}: 이미 없음")

    return results


def reset_all_flags(db, dry_run: bool = False) -> dict:
    """
    모든 컬렉션의 동기화 플래그 초기화 (병렬 처리)

    Args:
        db: MongoDB 데이터베이스 객체
        dry_run: True면 실제 초기화 없이 카운트만 확인

    Returns:
        dict: {collection_name: {flag: count}}
    """
    all_pairs = get_all_collections()
    results = {}

    # 병렬 처리 (최대 16개 워커)
    with ThreadPoolExecutor(max_workers=min(len(all_pairs), 16)) as executor:
        futures = {
            executor.submit(_reset_single_collection, db, coll_name, flag_name, dry_run): (coll_name, flag_name)
            for coll_name, flag_name in all_pairs
        }

        for future in as_completed(futures):
            coll_name, flag_name, count, is_dry = future.result()
            results.setdefault(coll_name, {})[flag_name] = count

            if is_dry:
                print(f"  [i] {coll_name}")
                print(f"      - {flag_name}: {count:,}건 (초기화 대상)")
            elif count > 0:
                print(f"  [v] {coll_name}")
                print(f"      - {flag_name} 제거: {count:,}건")
            else:
                print(f"  [-] {coll_name}")
                print(f"      - {flag_name}: 이미 없음")

    return results


def _verify_single_collection(db, collection_name: str, flag_name: str) -> tuple:
    """
    단일 컬렉션의 플래그 상태 확인 (병렬 처리용)

    Returns:
        tuple: (collection_name, flag_name, synced_count, total)
    """
    coll = db[collection_name]
    # 인덱스 힌트 사용
    index_hint = [(flag_name, 1)]
    synced_count = coll.count_documents({flag_name: True}, hint=index_hint)
    total = coll.estimated_document_count()
    return (collection_name, flag_name, synced_count, total)


def verify_all_flags():
    """모든 컬렉션의 플래그 상태 확인 (병렬 처리, 인덱스 활용)"""
    server, client = init_mongodb()
    db = client.get_database("gfcon_raw")

    mapping = get_collection_flag_map()

    print(f"\n{'=' * 80}")
    print("플래그 상태 확인")
    print(f"{'=' * 80}\n")

    # 모든 (collection, flag) 쌍 수집
    all_tasks = []
    for table_name, sources in mapping.items():
        for coll_name, flag_name in sources:
            all_tasks.append((table_name, coll_name, flag_name))

    # 병렬로 카운트 조회 (최대 16개 워커)
    results_map = {}
    with ThreadPoolExecutor(max_workers=min(len(all_tasks), 16)) as executor:
        futures = {
            executor.submit(_verify_single_collection, db, coll_name, flag_name): (table_name, coll_name, flag_name)
            for table_name, coll_name, flag_name in all_tasks
        }

        for future in as_completed(futures):
            coll_name, flag_name, synced_count, total = future.result()
            results_map[(coll_name, flag_name)] = (synced_count, total)

    # 테이블별로 정리하여 출력
    for table_name, sources in mapping.items():
        print(f"[{table_name}]")
        for collection_name, flag_name in sources:
            synced_count, total = results_map[(collection_name, flag_name)]

            if synced_count == 0:
                status = "[_] 모두 미동기화"
            elif synced_count == total:
                status = "[=] 모두 동기화됨"
            else:
                pct = synced_count / total * 100 if total > 0 else 0
                status = f"[~] {pct:.1f}% 동기화됨"

            print(f"  - {collection_name}")
            print(f"    {flag_name}: {synced_count:,}/{total:,} {status}")
        print()

    client.close()
    if server:
        server.stop()


def run_reset(tables: list = None, dry_run: bool = False):
    """
    플래그 초기화 실행

    Args:
        tables: 초기화할 테이블 목록 (None이면 전체)
        dry_run: True면 실제 초기화 없이 카운트만 확인
    """
    server, client = init_mongodb()
    db = client.get_database("gfcon_raw")

    mode = "[DRY-RUN] " if dry_run else ""

    if tables is None:
        # 모든 컬렉션 초기화
        print(f"\n{'=' * 80}")
        print(f"{mode}모든 컬렉션 동기화 플래그 초기화")
        print(f"{'=' * 80}\n")

        results = reset_all_flags(db, dry_run)

        # 요약
        print(f"\n{'=' * 80}")
        print(f"{mode}초기화 요약")
        print(f"{'=' * 80}")

        total_count = sum(
            sum(flags.values())
            for flags in results.values()
        )
        print(f"  총 {total_count:,}건 {'초기화 대상' if dry_run else '초기화 완료'}")

    else:
        # 특정 테이블만 초기화
        print(f"\n{'=' * 80}")
        print(f"{mode}동기화 플래그 초기화")
        print(f"대상 테이블: {', '.join(tables)}")
        print(f"{'=' * 80}\n")

        all_results = {}

        for table_name in tables:
            print(f"\n[{table_name}]")
            print("-" * 40)
            results = reset_flags_for_table(db, table_name, dry_run)
            all_results[table_name] = results

        # 요약
        print(f"\n{'=' * 80}")
        print(f"{mode}초기화 요약")
        print(f"{'=' * 80}")

        total_count = 0
        for table_name, collections in all_results.items():
            table_count = sum(
                sum(flags.values())
                for flags in collections.values()
            )
            total_count += table_count
            print(f"  - {table_name}: {table_count:,}건")

        print(f"\n  총 {total_count:,}건 {'초기화 대상' if dry_run else '초기화 완료'}")

    client.close()
    if server:
        server.stop()


def main():
    # 사용 가능한 테이블 목록
    available_tables = list(SYNC_CONFIGS.keys())

    parser = argparse.ArgumentParser(
        description="동기화 플래그 초기화 스크립트",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
사용 예시:
  python -m sync_data.scripts.reset_sync_flags notice          # notice 관련 플래그 초기화
  python -m sync_data.scripts.reset_sync_flags bid company     # bid, company 관련 플래그 초기화
  python -m sync_data.scripts.reset_sync_flags all             # 모든 플래그 초기화
  python -m sync_data.scripts.reset_sync_flags all --dry-run   # 실제 초기화 없이 확인
  python -m sync_data.scripts.reset_sync_flags --verify        # 현재 플래그 상태 확인

사용 가능한 테이블:
  {', '.join(available_tables)}
        """
    )
    parser.add_argument(
        "tables",
        nargs="*",
        help="초기화할 테이블 목록 또는 'all' (--verify 시 생략 가능)",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 초기화 없이 대상만 확인",
    )
    parser.add_argument(
        "--verify",
        action="store_true",
        help="현재 플래그 상태만 확인",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="확인 없이 바로 실행",
    )

    args = parser.parse_args()

    # --verify 모드
    if args.verify:
        verify_all_flags()
        return

    # 테이블 인자 확인
    if not args.tables:
        parser.print_help()
        return

    # 'all' 처리
    if args.tables == ["all"]:
        tables = None  # 모든 컬렉션
        table_desc = "모든 컬렉션"
    else:
        # 유효한 테이블인지 확인
        invalid_tables = [t for t in args.tables if t not in available_tables]
        if invalid_tables:
            print(f"\n[X] 알 수 없는 테이블: {', '.join(invalid_tables)}")
            print(f"사용 가능한 테이블: {', '.join(available_tables)}")
            return
        tables = args.tables
        table_desc = ", ".join(tables)

    # dry-run 모드
    if args.dry_run:
        run_reset(tables=tables, dry_run=True)
        return

    # 확인 프롬프트
    if not args.force:
        print(f"\n[!] 동기화 플래그 초기화")
        print(f"    대상: {table_desc}")
        print(f"\n[!] 이 작업은 MongoDB의 is_synced 플래그를 제거합니다.")
        print(f"[!] 다음 동기화 시 모든 데이터가 다시 처리됩니다.\n")

        response = input("계속하시겠습니까? (yes/no): ")
        if response.lower() not in ["yes", "y"]:
            print("[X] 작업이 취소되었습니다.")
            return

    # 실행
    run_reset(tables=tables, dry_run=False)

    print(f"\n{'=' * 80}")
    print("[v] 플래그 초기화 완료!")
    print(f"{'=' * 80}")
    print("\n다음 단계:")
    print("  python -m sync_data.main_sync <table> --schema <schema>")
    print("  python -m sync_data.main_sync all --schema data")


if __name__ == "__main__":
    main()
