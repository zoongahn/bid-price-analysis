"""
ReservePriceRangeSyncer - ReservePriceRange 통합 테이블 동기화

4개 대분류(공사/물품/외자/용역)의 MongoDB 컬렉션을 병합하여
단일 reserve_price_range 테이블로 동기화합니다.

특징:
- 4개 카테고리 병렬 처리 (notice_unified와 동일한 방식)
- 필드명 매핑 (range_no ← compnoRsrvtnPrceSno)
- notice 테이블에 없는 공고는 스킵 (FK 체크)
- bsns_div 컬럼으로 카테고리 구분
"""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from multiprocessing import Process, Value, Manager
import time
from tqdm import tqdm
from psycopg2.extras import execute_values

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.transform_document import transform_document
from sync_data.sync_config import get_config

# 한국 표준시 (UTC+9)
KST = timezone(timedelta(hours=9))


class ReservePriceRangeSyncer(BaseSyncer):
    """
    ReservePriceRange 통합 테이블 동기화 클래스

    4개 카테고리(공사/물품/외자/용역)를 병렬로 동기화합니다.
    """

    def __init__(self, schema: str = None, parallel: bool = True, test_limit: int = None):
        """
        Args:
            schema: PostgreSQL 스키마명
            parallel: 병렬 처리 여부 (기본: True)
            test_limit: 테스트 모드 시 카테고리당 최대 동기화 건수
        """
        super().__init__("reserve_price_range", schema=schema, test_limit=test_limit)
        self.parallel = parallel
        self.category_stats = {}
        self.notice_keys = None  # FK 체크용

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()

        # notice_keys 로드 (FK 체크용)
        print("   📋 notice_keys 로드 중...")
        self.psql_cur.execute(f"SELECT bidntceno, bidntceord FROM {self.schema}.notice;")
        notice_keys_list = self.psql_cur.fetchall()
        self.notice_keys = set(notice_keys_list)
        print(f"   ✅ notice_keys 로드 완료: {len(self.notice_keys):,}건")

        categories = self.config.get("categories", [])

        print(f"\n{'=' * 80}")
        print(f"📊 ReservePriceRange 통합 동기화 시작 ({len(categories)}개 카테고리)")
        print(f"   카테고리: {', '.join(cat['bsns_div'] for cat in categories)}")
        print(f"   처리 방식: {'병렬' if self.parallel else '순차'}")
        print(f"{'=' * 80}\n")

        if self.parallel:
            self._sync_parallel(categories, notice_keys_list)
        else:
            self._sync_sequential(categories)

        self.print_summary()

    def _sync_parallel(self, categories: list, notice_keys_list: list):
        """4개 카테고리 병렬 동기화"""
        manager = Manager()
        results = manager.dict()
        progress_counters = {cat["bsns_div"]: Value("i", 0) for cat in categories}

        # 각 카테고리별 총 문서 수 확인
        category_totals = {}
        for category in categories:
            bsns_div = category["bsns_div"]
            primary_source = None
            for source in category["merge_sources"]:
                if source.get("is_primary"):
                    primary_source = source
                    break

            if primary_source:
                coll = self.mongo_db[primary_source["collection_name"]]
                total = coll.count_documents({primary_source["sync_flag"]: {"$ne": True}})
                category_totals[bsns_div] = total
                print(f"   📋 {bsns_div}: {total:,}건 동기화 대상")

        total_docs = sum(category_totals.values())
        print(f"\n   📊 총 동기화 대상: {total_docs:,}건\n")

        if total_docs == 0:
            print("✅ 동기화할 데이터가 없습니다.")
            return

        # 워커 프로세스 시작
        processes = []
        start_time = time.time()

        for category in categories:
            bsns_div = category["bsns_div"]
            p = Process(
                target=_category_worker,
                args=(
                    bsns_div,
                    category["merge_sources"],
                    self.schema,
                    self.config["batch_size"],
                    self.config.get("field_aliases", []),
                    notice_keys_list,
                    progress_counters[bsns_div],
                    results,
                )
            )
            p.start()
            processes.append((bsns_div, p))
            self.loggers["application"].info(f"[{bsns_div}] 워커 시작")
            print(f"   🚀 [{bsns_div}] 워커 시작 (PID: {p.pid})")

        # 진행률 모니터링
        pbar = tqdm(total=total_docs, desc="전체 진행")
        prev_total = 0

        try:
            while any(p.is_alive() for _, p in processes):
                time.sleep(0.5)
                curr_total = sum(c.value for c in progress_counters.values())
                pbar.update(curr_total - prev_total)
                prev_total = curr_total
        finally:
            curr_total = sum(c.value for c in progress_counters.values())
            pbar.update(curr_total - prev_total)
            pbar.close()

            for bsns_div, p in processes:
                p.join()

        # 결과 집계
        elapsed = time.time() - start_time
        print(f"\n⏱️  총 소요 시간: {elapsed:.1f}초")

        for bsns_div in [cat["bsns_div"] for cat in categories]:
            if bsns_div in results:
                stats = results[bsns_div]
                self.category_stats[bsns_div] = stats
                self.total_synced += stats.get("synced", 0)
                self.total_skip += stats.get("skipped", 0)

                self.loggers["application"].info(
                    f"[{bsns_div}] 완료: {stats.get('synced', 0):,}건 동기화, "
                    f"{stats.get('skipped', 0):,}건 스킵"
                )

    def _sync_sequential(self, categories: list):
        """4개 카테고리 순차 동기화"""
        for idx, category in enumerate(categories, 1):
            bsns_div = category["bsns_div"]
            merge_sources = category["merge_sources"]

            print(f"\n[{idx}/{len(categories)}] {bsns_div} 동기화 시작...")
            self.loggers["application"].info(f"[{idx}/{len(categories)}] {bsns_div} 동기화 시작")

            try:
                synced, skipped = self._sync_category(bsns_div, merge_sources)
                self.category_stats[bsns_div] = {"synced": synced, "skipped": skipped}
                self.total_synced += synced
                self.total_skip += skipped

                print(f"   ✅ {bsns_div} 완료: {synced:,}건 동기화, {skipped:,}건 스킵")
                self.loggers["application"].info(
                    f"{bsns_div} 완료: {synced:,}건 동기화, {skipped:,}건 스킵"
                )

            except Exception as e:
                self._error_count += 1
                self.loggers["error"].error(f"{bsns_div} 동기화 실패: {e}", exc_info=True)
                print(f"   ❌ {bsns_div} 실패: {e}")
                raise

    def _sync_category(self, bsns_div: str, merge_sources: list) -> tuple[int, int]:
        """단일 카테고리 동기화 (순차 모드용)"""
        primary_source = None
        for source in merge_sources:
            if source.get("is_primary"):
                primary_source = source
                break

        if not primary_source:
            raise ValueError(f"{bsns_div}: primary source가 정의되지 않음")

        primary_collection = self.mongo_db[primary_source["collection_name"]]
        sync_flag = primary_source["sync_flag"]

        query = {sync_flag: {"$ne": True}}
        total = primary_collection.count_documents(query)

        self.loggers["application"].info(f"[{bsns_div}] 총 {total:,}건 동기화 대상")
        print(f"   📋 {bsns_div}: {total:,}건 동기화 대상")

        if total == 0:
            return 0, 0

        cursor = primary_collection.find(query).batch_size(1000)

        buffer = []
        synced_ids = []
        synced_count = 0
        skip_count = 0

        placeholder = "(" + ",".join(["%s"] * len(self.psql_columns)) + ")"
        pk_conflict = f"({', '.join(self.config['psql_pk'])})"
        batch_size = self.config.get("batch_size", 10000)

        now = datetime.now(KST)

        for doc in tqdm(cursor, total=total, desc=f"{bsns_div}"):
            # bsns_div 필드 추가
            doc["bsns_div"] = bsns_div

            # PostgreSQL row 변환
            field_aliases = self.config.get("field_aliases")
            row_dict = transform_document(self.psql_meta, doc, field_aliases)
            row_dict.pop("_id", None)

            # FK 체크
            fk_key = (row_dict.get("bidntceno"), row_dict.get("bidntceord"))
            if fk_key not in self.notice_keys:
                skip_count += 1
                continue

            # synced_at 설정
            if "synced_at" in self.psql_columns:
                row_dict["synced_at"] = now

            buffer.append(tuple(row_dict.get(col) for col in self.psql_columns))
            synced_ids.append(doc["_id"])

            if len(buffer) >= batch_size:
                self._flush_to_postgres(buffer, placeholder, pk_conflict)
                self._mark_synced(synced_ids, primary_collection, sync_flag)
                synced_count += len(buffer)

                buffer = []
                synced_ids = []

        if buffer:
            self._flush_to_postgres(buffer, placeholder, pk_conflict)
            self._mark_synced(synced_ids, primary_collection, sync_flag)
            synced_count += len(buffer)

        return synced_count, skip_count

    def _flush_to_postgres(self, rows: list, placeholder: str, pk_conflict: str):
        """PostgreSQL에 배치 Upsert"""
        if not rows:
            return

        pk_cols = set(self.config['psql_pk'])
        update_cols = [col for col in self.psql_columns if col not in pk_cols]
        update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])

        sql = f"""
            INSERT INTO {self.qualified_table_name} ({', '.join(self.psql_columns)})
            VALUES %s
            ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
        """
        execute_values(self.psql_cur, sql, rows, template=placeholder)
        self.psql_conn.commit()

    def _mark_synced(self, synced_ids: list, collection, sync_flag: str):
        """MongoDB에 is_synced 마킹"""
        if synced_ids:
            collection.update_many(
                {"_id": {"$in": synced_ids}},
                {"$set": {sync_flag: True}}
            )

    def print_sync_info(self):
        """동기화 시작 정보 출력"""
        categories = self.config.get("categories", [])
        info_lines = [
            f"동기화 정보:",
            f"  - 대상 스키마: {self.schema}",
            f"  - 대상 테이블: {self.config['psql_table']} (통합)",
            f"  - Full Name: {self.qualified_table_name}",
            f"  - 카테고리 수: {len(categories)}개",
            f"  - 카테고리: {', '.join(cat['bsns_div'] for cat in categories)}",
            f"  - 처리 방식: {'병렬 (4 프로세스)' if self.parallel else '순차'}",
            f"  - Batch Size: {self.config.get('batch_size', 10000):,}",
        ]
        for line in info_lines:
            self.loggers["application"].info(line)

        print(f"\n{'=' * 80}")
        print(f"📊 동기화 정보 (ReservePriceRange Unified)")
        print(f"{'=' * 80}")
        for line in info_lines[1:]:
            print(f"  {line}")
        print(f"{'=' * 80}\n")

    def print_summary(self):
        """동기화 결과 요약 출력"""
        print(f"\n{'=' * 80}")
        print(f"✅ [{self.schema}.reserve_price_range] 통합 동기화 완료")
        print(f"{'=' * 80}")
        print(f"   카테고리별 결과:")
        for cat, stats in self.category_stats.items():
            synced = stats.get('synced', 0) if isinstance(stats, dict) else stats['synced']
            skipped = stats.get('skipped', 0) if isinstance(stats, dict) else stats['skipped']
            print(f"     - {cat}: {synced:,}건 동기화, {skipped:,}건 스킵")
        print(f"   {'─' * 40}")
        print(f"   📊 총 동기화: {self.total_synced:,}건")
        if self.total_skip > 0:
            print(f"   ⚠️  FK 체크 스킵: {self.total_skip:,}건 (notice에 없는 공고)")
        print(f"{'=' * 80}\n")

        self.loggers["application"].info(
            f"통합 동기화 완료 - 총 동기화: {self.total_synced:,}건, 스킵: {self.total_skip:,}건"
        )


def _category_worker(
    bsns_div: str,
    merge_sources: list,
    schema: str,
    batch_size: int,
    field_aliases: list,
    notice_keys_list: list,
    progress_counter: Value,
    results: dict,
):
    """
    카테고리별 워커 프로세스

    Args:
        bsns_div: 업종구분 (공사/물품/외자/용역)
        merge_sources: merge_sources 설정
        schema: PostgreSQL 스키마명
        batch_size: 배치 크기
        field_aliases: 필드 별칭 목록
        notice_keys_list: notice 테이블의 (bidntceno, bidntceord) 튜플 리스트
        progress_counter: 진행률 카운터
        results: 결과 저장 딕셔너리 (Manager.dict)
    """
    import os
    from collections import defaultdict

    worker_start = time.time()
    pid = os.getpid()
    tag = f"[{bsns_div}]"

    print(f"{tag} 워커 시작 (PID: {pid})")

    # DB 연결
    from common.init_mongodb import init_mongodb
    from common.init_psql import init_psql
    from sync_data.sync.utils.postgres_meta import PostgresMeta

    mongo_server, mongo_client = init_mongodb()
    mongo_db = mongo_client.get_database("gfcon_raw")

    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    # notice_keys를 set으로 변환
    notice_keys = set(notice_keys_list)

    # Primary source 찾기
    primary_source = None
    for source in merge_sources:
        if source.get("is_primary"):
            primary_source = source
            break

    if not primary_source:
        print(f"{tag} ❌ primary source가 정의되지 않음")
        results[bsns_div] = {"synced": 0, "skipped": 0, "error": "No primary source"}
        return

    primary_collection = mongo_db[primary_source["collection_name"]]
    sync_flag = primary_source["sync_flag"]

    # PostgreSQL 메타데이터
    config = get_config("reserve_price_range")
    psql_meta = PostgresMeta(psql_conn, schema=schema).get_column_types(config["psql_table"])
    psql_columns = list(psql_meta.keys())

    qualified_table_name = f"{schema}.{config['psql_table']}"
    placeholder = "(" + ",".join(["%s"] * len(psql_columns)) + ")"
    pk_conflict = f"({', '.join(config['psql_pk'])})"
    pk_cols = set(config['psql_pk'])
    update_cols = [col for col in psql_columns if col not in pk_cols]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])

    # 미동기화 문서 조회
    query = {sync_flag: {"$ne": True}}
    total = primary_collection.count_documents(query)

    print(f"{tag} 동기화 대상: {total:,}건")

    if total == 0:
        results[bsns_div] = {"synced": 0, "skipped": 0}
        mongo_client.close()
        psql_cur.close()
        psql_conn.close()
        return

    cursor = primary_collection.find(query).batch_size(1000)

    # 버퍼
    buffer = []
    synced_ids = []
    synced_count = 0
    skip_count = 0
    batch_count = 0

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    for doc in cursor:
        # bsns_div 필드 추가
        doc["bsns_div"] = bsns_div

        # PostgreSQL row 변환
        row_dict = transform_document(psql_meta, doc, field_aliases)
        row_dict.pop("_id", None)

        # FK 체크
        fk_key = (row_dict.get("bidntceno"), row_dict.get("bidntceord"))
        if fk_key not in notice_keys:
            skip_count += 1
            continue

        # synced_at 설정
        if "synced_at" in psql_columns:
            row_dict["synced_at"] = now

        buffer.append(tuple(row_dict.get(col) for col in psql_columns))
        synced_ids.append(doc["_id"])

        # 배치 flush
        if len(buffer) >= batch_size:
            sql = f"""
                INSERT INTO {qualified_table_name} ({', '.join(psql_columns)})
                VALUES %s
                ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
            """
            execute_values(psql_cur, sql, buffer, template=placeholder)
            psql_conn.commit()

            # MongoDB 마킹
            primary_collection.update_many(
                {"_id": {"$in": synced_ids}},
                {"$set": {sync_flag: True}}
            )

            # 진행률 업데이트
            with progress_counter.get_lock():
                progress_counter.value += len(buffer)

            synced_count += len(buffer)
            batch_count += 1

            if batch_count % 10 == 0:
                elapsed = time.time() - worker_start
                rate = synced_count / elapsed if elapsed > 0 else 0
                print(f"{tag} 배치 {batch_count}: {synced_count:,}건 처리, {skip_count:,}건 스킵 ({rate:.0f}건/초)")

            buffer = []
            synced_ids = []

    # 남은 버퍼 처리
    if buffer:
        sql = f"""
            INSERT INTO {qualified_table_name} ({', '.join(psql_columns)})
            VALUES %s
            ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
        """
        execute_values(psql_cur, sql, buffer, template=placeholder)
        psql_conn.commit()

        primary_collection.update_many(
            {"_id": {"$in": synced_ids}},
            {"$set": {sync_flag: True}}
        )

        with progress_counter.get_lock():
            progress_counter.value += len(buffer)

        synced_count += len(buffer)

    # 완료
    elapsed = time.time() - worker_start
    rate = synced_count / elapsed if elapsed > 0 else 0
    print(f"{tag} ✅ 완료: {synced_count:,}건 동기화, {skip_count:,}건 스킵 ({elapsed:.1f}초, {rate:.0f}건/초)")

    results[bsns_div] = {"synced": synced_count, "skipped": skip_count}

    # 정리
    psql_cur.close()
    psql_conn.close()
    mongo_client.close()
