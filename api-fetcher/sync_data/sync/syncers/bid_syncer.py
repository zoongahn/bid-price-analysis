"""
BidSyncer - Bid 테이블 동기화

4개 사업구분별(공사/물품/외자/용역) MongoDB 컬렉션을
bid 테이블로 이중 병렬 처리하여 동기화합니다.

이중 병렬화:
- Level 1: 4개 카테고리 병렬 (공사/물품/외자/용역)
- Level 2: 각 카테고리 내 ObjectId 범위 분할 병렬

특징:
- 대용량 데이터 병렬 처리
- notice 테이블 외래키 체크
- bizrno 기본값 처리
"""

import multiprocessing
import time
from collections import defaultdict
from datetime import datetime, timezone, timedelta
from multiprocessing import Process, Value, Manager

from bson import ObjectId
from psycopg2.extras import execute_values
from tqdm import tqdm

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.sync_strategies import ParallelSyncStrategy
from sync_data.sync.transform_document import transform_document
from sync_data.sync_config import get_config

# 한국 표준시 (UTC+9)
KST = timezone(timedelta(hours=9))


class BidSyncer(BaseSyncer):
    """
    Bid 테이블 동기화 클래스

    4개 카테고리(공사/물품/외자/용역)를 이중 병렬로 동기화합니다.
    - Level 1: 카테고리 병렬 (4개 프로세스)
    - Level 2: ObjectId 범위 분할 병렬 (N개 워커/카테고리)
    """

    def __init__(
        self,
        total_workers: int = 32,
        schema: str = None,
        test_limit: int = None,
        categories: list = None,
    ):
        """
        Args:
            total_workers: 총 워커 수 (기본값: 32, 건수 비율에 따라 카테고리별 동적 배분)
            schema: PostgreSQL 스키마명
            test_limit: 테스트 모드 시 카테고리당 최대 동기화 건수 (None = 제한 없음)
            categories: 동기화할 카테고리 목록 (None = 전체, 예: ["공사"], ["물품", "용역"])
        """
        super().__init__("bid", schema=schema, test_limit=test_limit)
        self.total_workers = int(total_workers)
        self.category_filter = categories  # None이면 전체

        self.multi_source = self.config.get("multi_source", False)
        self.category_stats = {}
        self.test_limit = test_limit  # 테스트 모드 제한

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()

        if self.multi_source:
            self._sync_multi_source()
        else:
            # 기존 방식 (하위 호환)
            strategy = ParallelSyncStrategy(self.total_workers)
            strategy.execute(self)

        self.print_summary()

    def _sync_multi_source(self):
        """4개 카테고리 이중 병렬화 동기화"""
        all_categories = self.config.get("categories", [])

        # 카테고리 필터링 적용
        if self.category_filter:
            categories = [
                cat for cat in all_categories
                if cat["name"] in self.category_filter
            ]
            if not categories:
                print(f"⚠️ 지정된 카테고리가 없습니다: {self.category_filter}")
                print(f"   사용 가능한 카테고리: {', '.join(cat['name'] for cat in all_categories)}")
                return
        else:
            categories = all_categories

        filter_msg = f" (필터: {', '.join(self.category_filter)})" if self.category_filter else " (전체)"

        print(f"\n{'=' * 80}")
        print(f"📊 Bid 이중 병렬 동기화 시작 ({len(categories)}개 카테고리){filter_msg}")
        print(f"   카테고리: {', '.join(cat['name'] for cat in categories)}")
        print(f"   총 워커 수: {self.total_workers}개 (건수 비율에 따라 동적 배분)")
        if self.test_limit:
            print(f"   ⚠️  테스트 모드: 카테고리당 {self.test_limit:,}건 제한")
        print(f"{'=' * 80}\n")

        # 1) notice_keys 사전 로드
        print("   - notice_keys 로드 중...")
        self.psql_cur.execute(
            f"SELECT bidntceno, bidntceord FROM {self.schema}.notice;"
        )
        notice_keys_list = self.psql_cur.fetchall()
        notice_keys = set(notice_keys_list)
        print(f"   - notice_keys 로드 완료: {len(notice_keys):,}건")

        # 2) 각 카테고리별 문서 수 확인
        category_totals = {}
        for category in categories:
            cat_name = category["name"]
            primary_source = self._get_primary_source_from_category(category)
            coll = self.mongo_db[primary_source["collection_name"]]
            total = coll.count_documents({primary_source["sync_flag"]: {"$ne": True}})
            category_totals[cat_name] = total
            print(f"   📋 {cat_name}: {total:,}건 동기화 대상")

        total_docs = sum(category_totals.values())
        print(f"\n   📊 총 동기화 대상: {total_docs:,}건\n")

        if total_docs == 0:
            print("✅ 동기화할 데이터가 없습니다.")
            return

        # 3) 건수 비율에 따른 워커 수 동적 배분
        category_workers = self._allocate_workers(category_totals, self.total_workers)
        print("   📊 워커 배분:")
        for cat_name, num_workers in category_workers.items():
            ratio = category_totals[cat_name] / total_docs * 100 if total_docs > 0 else 0
            print(f"      - {cat_name}: {num_workers}개 워커 ({ratio:.1f}%)")
        print()

        # 4) 공유 상태
        manager = Manager()
        results = manager.dict()
        progress_counters = {cat["name"]: Value("i", 0) for cat in categories}

        # 5) 카테고리별 split points 미리 계산 (메인 프로세스에서)
        print("\n   📊 Split points 계산 중...")
        category_split_points = {}
        for category in categories:
            cat_name = category["name"]
            total = category_totals[cat_name]
            num_workers = category_workers.get(cat_name, 1)

            if total == 0 or self.test_limit:
                # 동기화 대상 없거나 테스트 모드면 split points 불필요
                category_split_points[cat_name] = None
                continue

            # 문서가 적으면 워커 수 조정
            effective_workers = min(num_workers, max(1, total // 100))

            if effective_workers <= 1:
                category_split_points[cat_name] = None
                continue

            primary_source = self._get_primary_source_from_category(category)
            coll = self.mongo_db[primary_source["collection_name"]]
            query = {primary_source["sync_flag"]: {"$ne": True}}

            print(f"   [{cat_name}] split points 계산 시작 ({effective_workers}개 워커, {total:,}건)")
            split_points = _get_split_points(coll, query, total, effective_workers)
            category_split_points[cat_name] = split_points
            print(f"   [{cat_name}] split points 계산 완료: {len(split_points)}개")

        print()

        # 6) 카테고리별 프로세스 생성
        processes = []
        start_time = time.time()

        for category in categories:
            cat_name = category["name"]
            num_workers = category_workers.get(cat_name, 1)
            split_points = category_split_points.get(cat_name)

            p = Process(
                target=_bid_category_worker,
                args=(
                    cat_name,
                    category["merge_sources"],
                    self.schema,
                    self.config["batch_size"],
                    num_workers,  # 동적 배분된 워커 수
                    notice_keys_list,  # list로 전달 (pickle 가능)
                    self.config.get("foreign_key_check"),
                    self.config.get("default_bizrno", "__DEFAULT__"),
                    progress_counters[cat_name],
                    results,
                    self.test_limit,  # 테스트 모드 제한
                    split_points,  # 미리 계산된 split points
                )
            )
            p.start()
            processes.append((cat_name, p))
            self.loggers["application"].info(f"[{cat_name}] 카테고리 워커 시작 ({num_workers}개 워커)")
            print(f"   🚀 [{cat_name}] 카테고리 워커 시작 (PID: {p.pid}, 워커: {num_workers}개)")

        # 7) 진행률 모니터링
        pbar = tqdm(total=total_docs, desc="전체 진행")
        prev_total = 0

        try:
            while any(p.is_alive() for _, p in processes):
                time.sleep(0.5)
                curr_total = sum(c.value for c in progress_counters.values())
                pbar.update(curr_total - prev_total)
                prev_total = curr_total
        finally:
            # 최종 업데이트
            curr_total = sum(c.value for c in progress_counters.values())
            pbar.update(curr_total - prev_total)
            pbar.close()

            # 모든 워커 종료 대기
            for cat_name, p in processes:
                p.join()

        # 7) 결과 집계
        elapsed = time.time() - start_time
        print(f"\n⏱️  총 소요 시간: {elapsed:.1f}초")

        for cat_name in [cat["name"] for cat in categories]:
            if cat_name in results:
                stats = results[cat_name]
                self.category_stats[cat_name] = stats
                self.total_synced += stats.get("synced", 0)
                self.total_skip += stats.get("skipped", 0)

                self.loggers["application"].info(
                    f"[{cat_name}] 완료: {stats.get('synced', 0):,}건 동기화, "
                    f"{stats.get('skipped', 0):,}건 스킵"
                )

    def _allocate_workers(self, category_totals: dict, total_workers: int) -> dict:
        """
        건수 비율에 따라 워커 수를 동적으로 배분

        Args:
            category_totals: 카테고리별 동기화 대상 건수 {cat_name: count}
            total_workers: 총 워커 수

        Returns:
            카테고리별 워커 수 {cat_name: num_workers}
        """
        total_docs = sum(category_totals.values())
        if total_docs == 0:
            # 건수가 없으면 균등 배분
            num_categories = len(category_totals)
            per_category = max(1, total_workers // num_categories)
            return {cat: per_category for cat in category_totals}

        # 비율에 따라 배분
        category_workers = {}
        remaining_workers = total_workers

        # 1단계: 비율에 따른 초기 배분 (최소 1개 보장)
        for cat_name, count in category_totals.items():
            if count == 0:
                category_workers[cat_name] = 1
            else:
                ratio = count / total_docs
                workers = max(1, int(total_workers * ratio))
                category_workers[cat_name] = workers

        # 2단계: 남은 워커 재배분 (가장 건수 많은 카테고리에 추가)
        allocated = sum(category_workers.values())
        remaining = total_workers - allocated

        if remaining > 0:
            # 건수 기준 내림차순 정렬
            sorted_cats = sorted(category_totals.items(), key=lambda x: x[1], reverse=True)
            for cat_name, _ in sorted_cats:
                if remaining <= 0:
                    break
                category_workers[cat_name] += 1
                remaining -= 1

        return category_workers

    def _get_primary_source_from_category(self, category: dict) -> dict:
        """카테고리에서 primary source 반환"""
        for source in category["merge_sources"]:
            if source.get("is_primary"):
                return source
        raise ValueError(f"No primary source in category: {category.get('name')}")

    def print_sync_info(self):
        """동기화 시작 정보 출력"""
        if self.multi_source:
            all_categories = self.config.get("categories", [])
            if self.category_filter:
                categories = [cat for cat in all_categories if cat["name"] in self.category_filter]
                filter_info = f"필터: {', '.join(self.category_filter)}"
            else:
                categories = all_categories
                filter_info = "전체"

            info_lines = [
                f"동기화 정보:",
                f"  - 대상 스키마: {self.schema}",
                f"  - 대상 테이블: {self.config['psql_table']}",
                f"  - Full Name: {self.qualified_table_name}",
                f"  - 모드: 이중 병렬 (multi_source)",
                f"  - 카테고리: {', '.join(cat['name'] for cat in categories)} ({filter_info})",
                f"  - 총 워커 수: {self.total_workers}개 (건수 비율 동적 배분)",
                f"  - Batch Size: {self.config.get('batch_size', 1000):,}",
            ]
        else:
            info_lines = [
                f"동기화 정보:",
                f"  - 대상 스키마: {self.schema}",
                f"  - 대상 테이블: {self.config['psql_table']}",
                f"  - 모드: 단일 컬렉션 병렬",
                f"  - 워커 수: {self.total_workers}개",
            ]

        for line in info_lines:
            self.loggers["application"].info(line)

        print(f"\n{'=' * 80}")
        print(f"📊 동기화 정보 (Bid)")
        print(f"{'=' * 80}")
        for line in info_lines[1:]:
            print(f"  {line}")
        print(f"{'=' * 80}\n")

    def print_summary(self):
        """동기화 결과 요약 출력"""
        print(f"\n{'=' * 80}")
        print(f"✅ [{self.schema}.bid] 동기화 완료")
        print(f"{'=' * 80}")

        if self.multi_source and self.category_stats:
            print(f"   카테고리별 결과:")
            for cat_name, stats in self.category_stats.items():
                synced = stats.get('synced', 0)
                skipped = stats.get('skipped', 0)
                print(f"     - {cat_name}: {synced:,}건 동기화, {skipped:,}건 스킵")
            print(f"   {'─' * 40}")

        print(f"   📊 총 동기화: {self.total_synced:,}건")
        if self.total_skip > 0:
            print(f"   ⚠️  notice 테이블에 없는 공고: {self.total_skip:,}건 skip됨")
        print(f"{'=' * 80}\n")

        self.loggers["application"].info(
            f"동기화 완료 - 총 동기화: {self.total_synced:,}건, 스킵: {self.total_skip:,}건"
        )


def _bid_category_worker(
    cat_name: str,
    merge_sources: list,
    schema: str,
    batch_size: int,
    num_workers: int,
    notice_keys_list: list,
    fk_config: dict,
    default_bizrno: str,
    progress_counter: Value,
    results: dict,
    test_limit: int = None,
    split_points: list = None,
):
    """
    카테고리별 워커 (Level 1)

    각 카테고리 내에서 ObjectId 범위 분할 병렬화 수행 (Level 2)

    Args:
        cat_name: 카테고리 이름 (공사/물품/외자/용역)
        merge_sources: merge_sources 설정
        schema: PostgreSQL 스키마명
        batch_size: 배치 크기
        num_workers: 카테고리 내 워커 수
        notice_keys_list: notice 테이블의 (bidntceno, bidntceord) 튜플 리스트
        fk_config: 외래키 체크 설정
        default_bizrno: 기본 bizrno 값
        progress_counter: 진행률 카운터
        results: 결과 저장 딕셔너리 (Manager.dict)
        test_limit: 테스트 모드 시 최대 동기화 건수 (None = 제한 없음)
        split_points: 미리 계산된 split points (None이면 단일 워커로 처리)
    """
    import os

    worker_start = time.time()
    pid = os.getpid()
    tag = f"[{cat_name}]"

    print(f"{tag} 카테고리 워커 시작 (PID: {pid})")

    # DB 연결
    from common.init_mongodb import init_mongodb
    from common.init_psql import init_psql

    mongo_server, mongo_client = init_mongodb()
    mongo_db = mongo_client.get_database("gfcon_raw")

    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    # Primary source 찾기
    primary_source = None
    for source in merge_sources:
        if source.get("is_primary"):
            primary_source = source
            break

    if not primary_source:
        print(f"{tag} ❌ primary source가 정의되지 않음")
        results[cat_name] = {"synced": 0, "skipped": 0, "error": "No primary source"}
        mongo_client.close()
        psql_cur.close()
        psql_conn.close()
        return

    collection = mongo_db[primary_source["collection_name"]]
    sync_flag = primary_source["sync_flag"]

    # 미동기화 문서 수
    query = {sync_flag: {"$ne": True}}
    total = collection.count_documents(query)

    # 테스트 모드: 제한 적용
    effective_total = min(total, test_limit) if test_limit else total

    if test_limit and total > test_limit:
        print(f"{tag} 동기화 대상: {total:,}건 중 {effective_total:,}건만 처리 (테스트 모드)")
    else:
        print(f"{tag} 동기화 대상: {total:,}건, 내부 워커: {num_workers}개")

    if total == 0:
        results[cat_name] = {"synced": 0, "skipped": 0}
        mongo_client.close()
        psql_cur.close()
        psql_conn.close()
        return

    # notice_keys를 set으로 변환
    notice_keys = set(notice_keys_list)

    # split_points가 없으면 단일 워커로 처리 (테스트 모드 또는 문서가 적은 경우)
    if not split_points or len(split_points) <= 1:
        # 단일 워커로 직접 처리
        synced, skipped = _process_bid_range(
            cat_name,
            merge_sources,
            schema,
            batch_size,
            None,  # start_id
            None,  # end_id
            query,
            notice_keys,
            fk_config,
            default_bizrno,
            progress_counter,
            test_limit=test_limit,  # 테스트 모드 제한
        )
        results[cat_name] = {"synced": synced, "skipped": skipped}
    else:
        # 미리 계산된 split_points 사용
        effective_workers = len(split_points)

        # Level 2: 카테고리 내 병렬 워커 생성
        inner_processes = []
        inner_synced = Value("i", 0)
        inner_skipped = Value("i", 0)

        for i in range(effective_workers):
            start_id = split_points[i]
            end_id = split_points[i + 1] if i + 1 < len(split_points) else None

            p = Process(
                target=_bid_inner_worker,
                args=(
                    cat_name,
                    merge_sources,
                    schema,
                    batch_size,
                    start_id,
                    end_id,
                    notice_keys_list,
                    fk_config,
                    default_bizrno,
                    progress_counter,
                    inner_synced,
                    inner_skipped,
                    i + 1,
                    effective_workers,
                )
            )
            p.start()
            inner_processes.append(p)

        # 내부 워커 종료 대기
        for p in inner_processes:
            p.join()

        results[cat_name] = {
            "synced": inner_synced.value,
            "skipped": inner_skipped.value,
        }

    elapsed = time.time() - worker_start
    final_stats = results.get(cat_name, {})
    print(
        f"{tag} ✅ 완료: {final_stats.get('synced', 0):,}건 동기화, "
        f"{final_stats.get('skipped', 0):,}건 스킵 ({elapsed:.1f}초)"
    )

    # 정리
    psql_cur.close()
    psql_conn.close()
    mongo_client.close()


def _bid_inner_worker(
    cat_name: str,
    merge_sources: list,
    schema: str,
    batch_size: int,
    start_id: ObjectId,
    end_id: ObjectId,
    notice_keys_list: list,
    fk_config: dict,
    default_bizrno: str,
    progress_counter: Value,
    synced_counter: Value,
    skipped_counter: Value,
    worker_id: int,
    total_workers: int,
):
    """
    ObjectId 범위별 워커 (Level 2)

    Args:
        cat_name: 카테고리 이름
        merge_sources: merge_sources 설정
        schema: PostgreSQL 스키마명
        batch_size: 배치 크기
        start_id: 시작 ObjectId
        end_id: 종료 ObjectId (None이면 끝까지)
        notice_keys_list: notice 테이블의 (bidntceno, bidntceord) 튜플 리스트
        fk_config: 외래키 체크 설정
        default_bizrno: 기본 bizrno 값
        progress_counter: 전체 진행률 카운터
        synced_counter: 동기화 건수 카운터
        skipped_counter: 스킵 건수 카운터
        worker_id: 워커 ID
        total_workers: 전체 워커 수
    """
    tag = f"[{cat_name}-W{worker_id}]"

    # Primary source 찾기
    primary_source = None
    for source in merge_sources:
        if source.get("is_primary"):
            primary_source = source
            break

    if not primary_source:
        return

    sync_flag = primary_source["sync_flag"]

    # 범위 쿼리 구성
    query = {sync_flag: {"$ne": True}}
    if start_id:
        query["_id"] = {"$gte": start_id}
        if end_id:
            query["_id"]["$lt"] = end_id
    elif end_id:
        query["_id"] = {"$lt": end_id}

    synced, skipped = _process_bid_range(
        cat_name,
        merge_sources,
        schema,
        batch_size,
        start_id,
        end_id,
        query,
        set(notice_keys_list),
        fk_config,
        default_bizrno,
        progress_counter,
        worker_id,
        total_workers,
    )

    with synced_counter.get_lock():
        synced_counter.value += synced
    with skipped_counter.get_lock():
        skipped_counter.value += skipped


def _process_bid_range(
    cat_name: str,
    merge_sources: list,
    schema: str,
    batch_size: int,
    start_id: ObjectId,
    end_id: ObjectId,
    query: dict,
    notice_keys: set,
    fk_config: dict,
    default_bizrno: str,
    progress_counter: Value,
    worker_id: int = 1,
    total_workers: int = 1,
    test_limit: int = None,
) -> tuple[int, int]:
    """
    ObjectId 범위 내 데이터 처리

    Args:
        test_limit: 테스트 모드 시 최대 동기화 건수 (None = 제한 없음)

    Returns:
        tuple: (동기화 건수, 스킵 건수)
    """
    import os
    from sync_data.sync.utils.postgres_meta import PostgresMeta

    tag = f"[{cat_name}-W{worker_id}]" if total_workers > 1 else f"[{cat_name}]"

    # DB 연결
    from common.init_mongodb import init_mongodb
    from common.init_psql import init_psql

    mongo_server, mongo_client = init_mongodb()
    mongo_db = mongo_client.get_database("gfcon_raw")

    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    # Primary source
    primary_source = None
    for source in merge_sources:
        if source.get("is_primary"):
            primary_source = source
            break

    collection = mongo_db[primary_source["collection_name"]]
    sync_flag = primary_source["sync_flag"]

    # PostgreSQL 메타데이터
    config = get_config("bid")
    psql_meta = PostgresMeta(psql_conn, schema=schema).get_column_types(config["psql_table"])
    psql_columns = list(psql_meta.keys())
    field_aliases = config.get("field_aliases")

    qualified_table_name = f"{schema}.{config['psql_table']}"
    placeholder = "(" + ",".join(["%s"] * len(psql_columns)) + ")"
    pk_conflict = f"({', '.join(config['psql_pk'])})"
    pk_cols = set(config['psql_pk'])
    update_cols = [col for col in psql_columns if col not in pk_cols]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])

    # FK 체크 설정
    notice_key_fields = fk_config.get("notice_keys", ()) if fk_config else ()
    bizrno_field = fk_config.get("company_key", "bidprccorpbizrno") if fk_config else "bidprccorpbizrno"

    # 버퍼
    buffer = []
    synced_ids = []
    synced_count = 0
    skip_count = 0
    batch_count = 0
    doc_count = 0

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    # 테스트 모드: limit 적용
    cursor = collection.find(query).batch_size(1000)
    if test_limit:
        cursor = cursor.limit(test_limit)

    for doc in cursor:
        doc_count += 1

        # PostgreSQL row 변환
        row_dict = transform_document(psql_meta, doc, field_aliases)
        row_dict.pop("_id", None)

        # FK 체크: notice 테이블에 존재하는지
        if notice_key_fields and notice_keys:
            fk_key = tuple(row_dict.get(field) for field in notice_key_fields)
            if fk_key not in notice_keys:
                skip_count += 1
                continue

        # bizrno 기본값 처리
        if not row_dict.get(bizrno_field):
            row_dict[bizrno_field] = default_bizrno

        # synced_at 설정
        if "synced_at" in psql_columns:
            row_dict["synced_at"] = now

        # 버퍼에 추가
        buffer.append(tuple(row_dict.get(col) for col in psql_columns))
        synced_ids.append(doc["_id"])

        # 배치 flush
        if len(buffer) >= batch_size:
            # PostgreSQL Upsert
            sql = f"""
                INSERT INTO {qualified_table_name} ({', '.join(psql_columns)})
                VALUES %s
                ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
            """
            execute_values(psql_cur, sql, buffer, template=placeholder)
            psql_conn.commit()

            # MongoDB 마킹
            collection.update_many(
                {"_id": {"$in": synced_ids}},
                {"$set": {sync_flag: True}}
            )

            # 진행률 업데이트
            with progress_counter.get_lock():
                progress_counter.value += len(buffer)

            synced_count += len(buffer)
            batch_count += 1

            # 10배치마다 로그
            if batch_count % 10 == 0:
                print(f"{tag} 배치 {batch_count}: {synced_count:,}건 처리")

            buffer = []
            synced_ids = []

        # 100,000건마다 연결 재생성
        if doc_count > 0 and doc_count % 100000 == 0:
            psql_cur.close()
            psql_conn.close()
            psql_server, psql_conn = init_psql()
            psql_cur = psql_conn.cursor()

    # 남은 버퍼 처리
    if buffer:
        sql = f"""
            INSERT INTO {qualified_table_name} ({', '.join(psql_columns)})
            VALUES %s
            ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
        """
        execute_values(psql_cur, sql, buffer, template=placeholder)
        psql_conn.commit()

        collection.update_many(
            {"_id": {"$in": synced_ids}},
            {"$set": {sync_flag: True}}
        )

        with progress_counter.get_lock():
            progress_counter.value += len(buffer)

        synced_count += len(buffer)

    # 정리
    psql_cur.close()
    psql_conn.close()
    mongo_client.close()

    return synced_count, skip_count


def _get_split_points(collection, query: dict, total: int, num_workers: int) -> list:
    """
    ObjectId 범위를 워커 수만큼 분할 (스트리밍 방식 - 메모리 효율적)

    Args:
        collection: MongoDB 컬렉션
        query: 조회 쿼리
        total: 전체 문서 수
        num_workers: 워커 수

    Returns:
        분할 포인트 ObjectId 리스트
    """
    if total == 0 or num_workers <= 1:
        return [None, None]

    step = max(1, total // num_workers)
    split_points = []

    print(f"[split_point] 스트리밍 방식으로 분할점 계산 시작 (total={total:,}, step={step:,})", flush=True)

    # 커서로 스트리밍하면서 분할점만 저장 (메모리 효율적)
    cursor = collection.find(query, {"_id": 1}).sort("_id", 1)

    # 진행률 로그 간격 (1000만건마다 또는 5%마다)
    log_interval = max(10_000_000, total // 20)
    last_log = 0

    for i, doc in enumerate(cursor):
        # 진행률 로그 (1000만건 또는 5%마다)
        if i - last_log >= log_interval:
            pct = (i / total) * 100
            print(f"[split_point] 진행중: {i:,}/{total:,} ({pct:.1f}%) - 분할점 {len(split_points)}/{num_workers}개", flush=True)
            last_log = i

        if i % step == 0 and len(split_points) < num_workers:
            oid = doc["_id"]
            split_points.append(oid)
            print(f"[split_point] ✓ {len(split_points)}/{num_workers} 분할점 확정 (idx={i:,}) → {oid}", flush=True)

        # 모든 분할점을 찾으면 조기 종료
        if len(split_points) >= num_workers:
            cursor.close()
            break

    print(f"[split_point] 분할점 {len(split_points)}개 확정 완료", flush=True)

    # 재사용 가능하도록 전체 split points 출력
    print(f"[split_point] === 재사용 가능한 split_points ===", flush=True)
    print(f"split_points = [", flush=True)
    for i, sp in enumerate(split_points):
        print(f"    ObjectId('{sp}'),  # {i+1}", flush=True)
    print(f"]", flush=True)

    return split_points
