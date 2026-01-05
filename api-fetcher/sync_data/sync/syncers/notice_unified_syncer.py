"""
NoticeUnifiedSyncer - Notice 통합 테이블 동기화

4개 대분류(공사/물품/외자/용역)의 MongoDB 컬렉션을 병합하여
단일 notice 테이블로 동기화합니다.

4개 카테고리를 병렬로 처리하여 성능을 최적화합니다.
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


class NoticeUnifiedSyncer(BaseSyncer):
    """
    Notice 통합 테이블 동기화 클래스

    4개 카테고리(공사/물품/외자/용역)를 병렬로 동기화합니다.
    """

    def __init__(self, schema: str = None, parallel: bool = True, test_limit: int = None):
        """
        Args:
            schema: PostgreSQL 스키마명
            parallel: 병렬 처리 여부 (기본: True)
            test_limit: 테스트 모드 시 카테고리당 최대 동기화 건수 (기본값: None = 제한 없음)
        """
        # notice_unified config 사용
        super().__init__("notice_unified", schema=schema, test_limit=test_limit)

        self.parallel = parallel
        # 카테고리별 통계
        self.category_stats = {}

    def _verify_table_exists(self):
        """
        테이블 존재 여부 확인 및 자동 생성
        notice_unified는 notice_v2_unified.sql 파일 사용
        """
        import os

        self.psql_cur.execute(
            """
            SELECT EXISTS (
                SELECT FROM information_schema.tables
                WHERE table_schema = %s
                AND table_name = %s
            );
            """,
            (self.schema, self.config["psql_table"])
        )
        exists = self.psql_cur.fetchone()[0]

        if not exists:
            self.loggers["application"].warning(
                f"테이블 {self.schema}.{self.config['psql_table']} 없음 - 생성 시작"
            )
            self._create_unified_table()
        else:
            self.loggers["application"].info(
                f"테이블 {self.schema}.{self.config['psql_table']} 확인됨"
            )

    def _create_unified_table(self):
        """
        notice_v2_unified.sql 파일을 사용하여 테이블 생성
        """
        import os

        # notice_v2_unified.sql 파일 경로
        sql_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "..",
            "create",
            "notice_v2_unified.sql"
        )

        if not os.path.exists(sql_file):
            error_msg = f"SQL 파일이 존재하지 않습니다: {sql_file}"
            self.loggers["error"].error(error_msg)
            raise FileNotFoundError(f"❌ {error_msg}")

        self.loggers["application"].info(
            f"테이블 생성 중: {self.schema}.{self.config['psql_table']}"
        )

        # 스키마 생성 (없으면)
        self.psql_cur.execute(f"CREATE SCHEMA IF NOT EXISTS {self.schema};")

        with open(sql_file, "r", encoding="utf-8") as f:
            sql_content = f.read()

        # 스키마 지정: 테이블명 앞에 스키마 추가
        sql_content = sql_content.replace(
            "DROP TABLE IF EXISTS notice",
            f"DROP TABLE IF EXISTS {self.schema}.notice"
        )
        sql_content = sql_content.replace(
            "CREATE TABLE IF NOT EXISTS notice",
            f"CREATE TABLE IF NOT EXISTS {self.schema}.notice"
        )
        sql_content = sql_content.replace(
            " ON notice ",
            f" ON {self.schema}.notice "
        )
        sql_content = sql_content.replace(
            " ON notice(",
            f" ON {self.schema}.notice("
        )
        sql_content = sql_content.replace(
            "COMMENT ON TABLE notice",
            f"COMMENT ON TABLE {self.schema}.notice"
        )

        try:
            self.psql_cur.execute(sql_content)
            self.psql_conn.commit()
            self.loggers["application"].info(
                f"테이블 생성 완료: {self.schema}.{self.config['psql_table']}"
            )
        except Exception as e:
            self.psql_conn.rollback()
            error_msg = f"테이블 생성 실패: {self.schema}.{self.config['psql_table']} - {e}"
            self.loggers["error"].error(error_msg, exc_info=True)
            raise RuntimeError(f"❌ {error_msg}")

    def sync(self):
        """
        동기화 실행

        4개 카테고리를 병렬로 동기화합니다.
        """
        self.print_sync_info()

        categories = self.config.get("categories", [])

        print(f"\n{'=' * 80}")
        print(f"📊 Notice 통합 동기화 시작 ({len(categories)}개 카테고리)")
        print(f"   카테고리: {', '.join(cat['bsns_div'] for cat in categories)}")
        print(f"   처리 방식: {'병렬' if self.parallel else '순차'}")
        print(f"{'=' * 80}\n")

        if self.parallel:
            self._sync_parallel(categories)
        else:
            self._sync_sequential(categories)

        self.print_summary()

    def _sync_parallel(self, categories: list):
        """
        4개 카테고리 병렬 동기화

        Args:
            categories: 카테고리 설정 리스트
        """
        # 공유 카운터 (카테고리별)
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
            # 최종 업데이트
            curr_total = sum(c.value for c in progress_counters.values())
            pbar.update(curr_total - prev_total)
            pbar.close()

            # 모든 워커 종료 대기
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
        """
        4개 카테고리 순차 동기화 (기존 방식)

        Args:
            categories: 카테고리 설정 리스트
        """
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
        """
        단일 카테고리 동기화 (순차 모드용)

        Args:
            bsns_div: 업종구분 (공사/물품/외자/용역)
            merge_sources: 해당 카테고리의 merge_sources 설정

        Returns:
            tuple: (동기화 건수, 스킵 건수)
        """
        # Primary source 찾기
        primary_source = None
        for source in merge_sources:
            if source.get("is_primary"):
                primary_source = source
                break

        if not primary_source:
            raise ValueError(f"{bsns_div}: primary source가 정의되지 않음")

        primary_collection = self.mongo_db[primary_source["collection_name"]]
        sync_flag = primary_source["sync_flag"]

        # 미동기화 문서 조회
        query = {sync_flag: {"$ne": True}}
        total = primary_collection.count_documents(query)

        self.loggers["application"].info(
            f"[{bsns_div}] 총 {total:,}건 동기화 대상"
        )
        print(f"   📋 {bsns_div}: {total:,}건 동기화 대상")

        if total == 0:
            return 0, 0

        cursor = primary_collection.find(query).batch_size(1000)

        # 버퍼
        buffer = []
        synced_ids_map = defaultdict(list)
        synced_count = 0
        skip_count = 0

        # SQL 템플릿
        placeholder = "(" + ",".join(["%s"] * len(self.psql_columns)) + ")"
        pk_conflict = f"({', '.join(self.config['psql_pk'])})"
        batch_size = self.config.get("batch_size", 10000)

        now = datetime.now(KST)
        doc_count = 0

        for doc in tqdm(cursor, total=total, desc=f"{bsns_div}"):
            # 100,000건마다 PostgreSQL 연결 재생성
            if doc_count > 0 and doc_count % 100000 == 0:
                self.reconnect_postgres()

            # 다중 컬렉션 병합
            merged_doc, source_synced_columns = self._merge_documents(
                doc, merge_sources
            )

            # bsns_div 필드 추가
            merged_doc["bsns_div"] = bsns_div

            # 전처리
            processed_doc = self.preprocess_document(merged_doc)
            if not processed_doc:
                skip_count += 1
                continue

            # PostgreSQL row 변환
            row_dict = self._transform_to_psql_row(processed_doc, source_synced_columns, now)
            if not row_dict:
                skip_count += 1
                continue

            # 유효성 검증
            if not self.validate_row(row_dict):
                skip_count += 1
                continue

            # 버퍼에 추가
            buffer.append(tuple(row_dict.get(col) for col in self.psql_columns))

            # 동기화된 문서 ID 추적
            synced_ids_map[primary_source["collection_name"]].append(doc["_id"])

            # 배치 flush
            if len(buffer) >= batch_size:
                self._flush_to_postgres(buffer, placeholder, pk_conflict)
                self._mark_synced(synced_ids_map, merge_sources)
                synced_count += len(buffer)

                self.loggers["batch"].info(
                    f"[{bsns_div}] {synced_count:,}건 처리 완료"
                )

                buffer = []
                synced_ids_map = defaultdict(list)

            doc_count += 1

        # 남은 버퍼 flush
        if buffer:
            self._flush_to_postgres(buffer, placeholder, pk_conflict)
            self._mark_synced(synced_ids_map, merge_sources)
            synced_count += len(buffer)

            self.loggers["batch"].info(
                f"[{bsns_div}] Final batch: {len(buffer):,}건 처리 (총: {synced_count:,}건)"
            )

        return synced_count, skip_count

    def _merge_documents(self, primary_doc: dict, merge_sources: list) -> tuple[dict, list]:
        """
        여러 컬렉션에서 문서를 조회하여 병합

        Args:
            primary_doc: Primary 컬렉션의 문서
            merge_sources: merge_sources 설정

        Returns:
            tuple: (병합된 문서, 데이터가 있는 소스의 synced_at_column 목록)
        """
        merged = primary_doc.copy()
        source_synced_columns = []

        for source in merge_sources:
            if source.get("is_primary"):
                continue

            collection = self.mongo_db[source["collection_name"]]
            join_keys = source.get("join_keys", ())

            # 조인 쿼리 생성
            join_query = {key: primary_doc.get(key) for key in join_keys}

            projection = source.get("projection") or {"_id": 0}
            doc = collection.find_one(join_query, projection) or {}

            if doc:
                merged.update(doc)
                if source.get("synced_at_column"):
                    source_synced_columns.append(source["synced_at_column"])

        return merged, source_synced_columns

    def _transform_to_psql_row(self, doc: dict, source_synced_columns: list, now: datetime) -> dict:
        """
        MongoDB 문서를 PostgreSQL row로 변환

        Args:
            doc: MongoDB 문서
            source_synced_columns: 설정할 소스별 synced_at 컬럼 목록
            now: 현재 시간

        Returns:
            PostgreSQL row 딕셔너리
        """
        field_aliases = self.config.get("field_aliases")
        row_dict = transform_document(self.psql_meta, doc, field_aliases)
        row_dict.pop("_id", None)

        # synced_at 컬럼 설정
        if "synced_at" in self.psql_columns:
            row_dict["synced_at"] = now

        # 소스별 synced_at 컬럼 설정 (bssamt_synced_at, win_synced_at 등)
        for col in source_synced_columns:
            if col in self.psql_columns:
                row_dict[col] = now

        return row_dict

    def _flush_to_postgres(self, rows: list, placeholder: str, pk_conflict: str):
        """PostgreSQL에 배치 Upsert"""
        if not rows:
            return

        # PK 컬럼 제외한 업데이트 대상 컬럼
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

    def _mark_synced(self, synced_ids_map: dict, merge_sources: list):
        """모든 관련 컬렉션에 is_synced 마킹"""
        for source in merge_sources:
            collection_name = source["collection_name"]
            sync_flag = source["sync_flag"]
            ids = synced_ids_map.get(collection_name, [])

            if ids:
                collection = self.mongo_db[collection_name]
                collection.update_many(
                    {"_id": {"$in": ids}},
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
        print(f"📊 동기화 정보 (Notice Unified)")
        print(f"{'=' * 80}")
        for line in info_lines[1:]:
            print(f"  {line}")
        print(f"{'=' * 80}\n")

    def print_summary(self):
        """동기화 결과 요약 출력"""
        print(f"\n{'=' * 80}")
        print(f"✅ [{self.schema}.notice] 통합 동기화 완료")
        print(f"{'=' * 80}")
        print(f"   카테고리별 결과:")
        for cat, stats in self.category_stats.items():
            synced = stats.get('synced', 0) if isinstance(stats, dict) else stats['synced']
            skipped = stats.get('skipped', 0) if isinstance(stats, dict) else stats['skipped']
            print(f"     - {cat}: {synced:,}건 동기화, {skipped:,}건 스킵")
        print(f"   {'─' * 40}")
        print(f"   📊 총 동기화: {self.total_synced:,}건")
        if self.total_skip > 0:
            print(f"   📊 총 스킵: {self.total_skip:,}건")
        print(f"{'=' * 80}\n")

        self.loggers["application"].info(
            f"통합 동기화 완료 - 총 동기화: {self.total_synced:,}건, 스킵: {self.total_skip:,}건"
        )


def _category_worker(
    bsns_div: str,
    merge_sources: list,
    schema: str,
    batch_size: int,
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
    config = get_config("notice_unified")
    psql_meta = PostgresMeta(psql_conn, schema=schema).get_column_types(config["psql_table"])
    psql_columns = list(psql_meta.keys())
    field_aliases = config.get("field_aliases")

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
    synced_ids_map = defaultdict(list)
    synced_count = 0
    skip_count = 0
    batch_count = 0

    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    for doc in cursor:
        # 다중 컬렉션 병합
        merged_doc = doc.copy()
        source_synced_columns = []

        for source in merge_sources:
            if source.get("is_primary"):
                continue

            coll = mongo_db[source["collection_name"]]
            join_keys = source.get("join_keys", ())
            join_query = {key: doc.get(key) for key in join_keys}

            projection = source.get("projection") or {"_id": 0}
            sub_doc = coll.find_one(join_query, projection) or {}

            if sub_doc:
                merged_doc.update(sub_doc)
                if source.get("synced_at_column"):
                    source_synced_columns.append(source["synced_at_column"])

        # bsns_div 필드 추가
        merged_doc["bsns_div"] = bsns_div

        # PostgreSQL row 변환
        row_dict = transform_document(psql_meta, merged_doc, field_aliases)
        row_dict.pop("_id", None)

        # synced_at 컬럼 설정
        if "synced_at" in psql_columns:
            row_dict["synced_at"] = now

        for col in source_synced_columns:
            if col in psql_columns:
                row_dict[col] = now

        # 버퍼에 추가
        buffer.append(tuple(row_dict.get(col) for col in psql_columns))
        synced_ids_map[primary_source["collection_name"]].append(doc["_id"])

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
            for source in merge_sources:
                coll_name = source["collection_name"]
                sf = source["sync_flag"]
                ids = synced_ids_map.get(coll_name, [])
                if ids:
                    mongo_db[coll_name].update_many(
                        {"_id": {"$in": ids}},
                        {"$set": {sf: True}}
                    )

            # 진행률 업데이트
            with progress_counter.get_lock():
                progress_counter.value += len(buffer)

            synced_count += len(buffer)
            batch_count += 1

            # 10배치마다 로그
            if batch_count % 10 == 0:
                elapsed = time.time() - worker_start
                rate = synced_count / elapsed if elapsed > 0 else 0
                print(f"{tag} 배치 {batch_count}: {synced_count:,}건 처리 ({rate:.0f}건/초)")

            buffer = []
            synced_ids_map = defaultdict(list)

    # 남은 버퍼 처리
    if buffer:
        sql = f"""
            INSERT INTO {qualified_table_name} ({', '.join(psql_columns)})
            VALUES %s
            ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
        """
        execute_values(psql_cur, sql, buffer, template=placeholder)
        psql_conn.commit()

        for source in merge_sources:
            coll_name = source["collection_name"]
            sf = source["sync_flag"]
            ids = synced_ids_map.get(coll_name, [])
            if ids:
                mongo_db[coll_name].update_many(
                    {"_id": {"$in": ids}},
                    {"$set": {sf: True}}
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
