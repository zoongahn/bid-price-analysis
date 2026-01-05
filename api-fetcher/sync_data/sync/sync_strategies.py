"""
동기화 전략 클래스들

Strategy Pattern을 사용하여 동기화 방식을 캡슐화합니다.
- SingleProcessSyncStrategy: 단일 프로세스 동기화 (다중 컬렉션 병합)
- ParallelSyncStrategy: 병렬 처리 동기화
"""

from abc import ABC, abstractmethod
from collections import defaultdict
from typing import TYPE_CHECKING
from datetime import datetime, timezone, timedelta

# 한국 표준시 (UTC+9)
KST = timezone(timedelta(hours=9))
from bson import ObjectId
from tqdm import tqdm
from psycopg2.extras import execute_values
from multiprocessing import Process, Value
import time

from sync_data.sync.transform_document import transform_document

if TYPE_CHECKING:
    from sync_data.sync.base_syncer import BaseSyncer


class SyncStrategy(ABC):
    """동기화 전략 추상 클래스"""

    @abstractmethod
    def execute(self, syncer: 'BaseSyncer'):
        """
        동기화 실행

        Args:
            syncer: BaseSyncer 인스턴스
        """
        pass


class SingleProcessSyncStrategy(SyncStrategy):
    """
    단일 프로세스 동기화 전략

    다중 MongoDB 컬렉션을 병합하여 단일 PostgreSQL 테이블로 동기화합니다.
    """

    def execute(self, syncer: 'BaseSyncer'):
        """단일 프로세스로 동기화 실행"""
        from sync_data.sync_config import get_primary_source

        primary_source = get_primary_source(syncer.config)
        primary_collection = syncer.mongo_db[primary_source["collection_name"]]

        # 미동기화 문서 조회
        query = syncer.build_unsynced_query()
        total = primary_collection.count_documents(query)

        syncer.loggers["application"].info(
            f"[{syncer.table_name}] 총 {total:,}건 동기화 시작 (batch={syncer.config['batch_size']})"
        )
        print(f"🔄 [{syncer.table_name}] 총 {total:,}건 동기화 시작 (batch={syncer.config['batch_size']})")

        if total == 0:
            syncer.loggers["application"].info(f"[{syncer.table_name}] 동기화할 데이터가 없습니다.")
            print(f"✅ [{syncer.table_name}] 동기화할 데이터가 없습니다.")
            return

        # test_limit 적용
        if syncer.test_limit:
            total = min(total, syncer.test_limit)
            print(f"⚠️  테스트 모드: {syncer.test_limit:,}건으로 제한")

        cursor = primary_collection.find(query).batch_size(1000)
        if syncer.test_limit:
            cursor = cursor.limit(syncer.test_limit)

        # 버퍼
        buffer = []
        synced_ids_map = defaultdict(list)

        # SQL 템플릿
        placeholder = "(" + ",".join(["%s"] * len(syncer.psql_columns)) + ")"
        pk_conflict = f"({', '.join(syncer.config['psql_pk'])})"

        doc_count = 0
        for doc in tqdm(cursor, total=total, desc=f"Syncing {syncer.table_name}"):
            # 100,000건마다 PostgreSQL 연결 재생성
            if doc_count > 0 and doc_count % 100000 == 0:
                syncer.reconnect_postgres()

            # 다중 컬렉션 병합
            merged_doc, source_synced_columns = self._merge_documents(syncer, doc)

            # 전처리
            processed_doc = syncer.preprocess_document(merged_doc)
            if not processed_doc:
                continue

            # PostgreSQL row 변환
            row_dict = self._transform_to_psql_row(syncer, processed_doc, source_synced_columns)
            if not row_dict:
                continue

            # 유효성 검증
            if not syncer.validate_row(row_dict):
                syncer.total_skip += 1
                continue

            # 버퍼에 추가
            buffer.append(tuple(row_dict.get(col) for col in syncer.psql_columns))

            # 동기화된 문서 ID 추적
            synced_ids_map[primary_source["collection_name"]].append(doc["_id"])

            # 병합된 컬렉션들의 ID 추적
            for source in syncer.config["merge_sources"]:
                if source["is_primary"]:
                    continue

                collection_name = source["collection_name"]
                join_query = self._build_join_query(doc, source["join_keys"])

                merged_coll = syncer.mongo_db[collection_name]
                merged_doc_id = merged_coll.find_one(join_query, {"_id": 1})

                if merged_doc_id:
                    synced_ids_map[collection_name].append(merged_doc_id["_id"])

            doc_count += 1

            # 배치 사이즈 도달 시 flush
            if len(buffer) >= syncer.config["batch_size"]:
                self._flush_to_postgres(syncer, buffer, placeholder, pk_conflict)
                self._mark_all_synced(syncer, synced_ids_map)
                syncer.total_synced += len(buffer)

                # 배치 로깅
                syncer.loggers["batch"].info(
                    f"Batch flush: {len(buffer):,}건 처리 (누적: {syncer.total_synced:,}건)"
                )

                buffer.clear()
                synced_ids_map.clear()

        # 남은 버퍼 처리
        if buffer:
            self._flush_to_postgres(syncer, buffer, placeholder, pk_conflict)
            self._mark_all_synced(syncer, synced_ids_map)
            syncer.total_synced += len(buffer)

            syncer.loggers["batch"].info(
                f"Final batch: {len(buffer):,}건 처리 (총: {syncer.total_synced:,}건)"
            )

    def _merge_documents(self, syncer: 'BaseSyncer', primary_doc: dict) -> tuple[dict, list]:
        """여러 컬렉션에서 문서를 조회하여 병합

        Returns:
            tuple: (병합된 문서, 데이터가 있는 소스의 synced_at_column 목록)
        """
        merged = primary_doc.copy()
        source_synced_columns = []

        for source in syncer.config["merge_sources"]:
            if source["is_primary"]:
                continue

            collection = syncer.mongo_db[source["collection_name"]]
            join_query = self._build_join_query(primary_doc, source["join_keys"])

            projection = source.get("projection") or {"_id": 0}
            doc = collection.find_one(join_query, projection) or {}

            if doc:  # 데이터가 있는 경우에만 synced_at_column 추가
                merged.update(doc)
                if source.get("synced_at_column"):
                    source_synced_columns.append(source["synced_at_column"])

        return merged, source_synced_columns

    def _build_join_query(self, primary_doc: dict, join_keys: tuple) -> dict:
        """조인 쿼리 생성"""
        return {key: primary_doc[key] for key in join_keys}

    def _transform_to_psql_row(self, syncer: 'BaseSyncer', doc: dict, source_synced_columns: list = None) -> dict:
        """MongoDB 문서를 PostgreSQL row로 변환

        Args:
            syncer: BaseSyncer 인스턴스
            doc: MongoDB 문서
            source_synced_columns: 설정할 소스별 synced_at 컬럼 목록
        """
        field_aliases = syncer.config.get("field_aliases")
        row_dict = transform_document(syncer.psql_meta, doc, field_aliases)
        row_dict.pop("_id", None)

        # synced_at 컬럼 설정 (현재 시간, KST)
        now = datetime.now(KST)
        if "synced_at" in syncer.psql_columns:
            row_dict["synced_at"] = now

        # 소스별 synced_at 컬럼 설정 (bssamt_synced_at, win_synced_at 등)
        if source_synced_columns:
            for col in source_synced_columns:
                if col in syncer.psql_columns:
                    row_dict[col] = now

        return row_dict

    def _flush_to_postgres(self, syncer: 'BaseSyncer', rows: list, placeholder: str, pk_conflict: str):
        """PostgreSQL에 배치 Upsert (INSERT ... ON CONFLICT DO UPDATE)"""
        if not rows:
            return

        # PK 컬럼 제외한 업데이트 대상 컬럼
        pk_cols = set(syncer.config['psql_pk'])
        update_cols = [col for col in syncer.psql_columns if col not in pk_cols]
        update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])

        sql = f"""
            INSERT INTO {syncer.qualified_table_name} ({', '.join(syncer.psql_columns)})
            VALUES %s
            ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
        """
        execute_values(syncer.psql_cur, sql, rows, template=placeholder)
        syncer.psql_conn.commit()

    def _mark_all_synced(self, syncer: 'BaseSyncer', synced_ids_map: dict):
        """모든 관련 컬렉션에 is_synced 마킹"""
        for source in syncer.config["merge_sources"]:
            collection_name = source["collection_name"]
            sync_flag = source["sync_flag"]
            ids = synced_ids_map.get(collection_name, [])

            if ids:
                collection = syncer.mongo_db[collection_name]
                collection.update_many(
                    {"_id": {"$in": ids}},
                    {"$set": {sync_flag: True}}
                )


class ParallelSyncStrategy(SyncStrategy):
    """
    병렬 처리 동기화 전략

    대용량 데이터를 ObjectId 범위로 분할하여 멀티프로세싱으로 처리합니다.
    """

    def __init__(self, num_workers: int | str = "auto"):
        """
        Args:
            num_workers: 워커 프로세스 수 ("auto" = CPU_COUNT * 2)
        """
        if num_workers == "auto":
            import multiprocessing
            self.num_workers = multiprocessing.cpu_count() * 2
        else:
            self.num_workers = num_workers

    def execute(self, syncer: 'BaseSyncer'):
        """병렬 처리로 동기화 실행"""
        from sync_data.sync_config import get_primary_source

        primary_source = get_primary_source(syncer.config)
        collection = syncer.mongo_db[primary_source["collection_name"]]
        sync_flag = primary_source["sync_flag"]

        # 전체 문서 수
        query = {sync_flag: {"$ne": True}}
        total_docs = collection.count_documents(query)

        syncer.loggers["application"].info(
            f"[{syncer.table_name}] 병렬 동기화 시작 - 총 {total_docs:,}건, 워커 {self.num_workers}개"
        )
        print(f"🚀 [{syncer.table_name}] 병렬 동기화 시작")
        print(f"   - 총 문서 수: {total_docs:,}건")
        print(f"   - 워커 수: {self.num_workers}개")

        if total_docs == 0:
            syncer.loggers["application"].info(f"[{syncer.table_name}] 동기화할 데이터가 없습니다.")
            print(f"✅ [{syncer.table_name}] 동기화할 데이터가 없습니다.")
            return

        # test_limit 적용
        if syncer.test_limit:
            total_docs = min(total_docs, syncer.test_limit)
            print(f"   ⚠️  테스트 모드: {syncer.test_limit:,}건으로 제한")

        # split points 계산
        print(f"   - split points 계산 중...")
        split_start = time.time()
        points = self._get_split_points(collection, query, total_docs, syncer.test_limit)
        split_elapsed = time.time() - split_start
        syncer.loggers["application"].info(f"split points 계산 완료: {split_elapsed:.1f}초 소요")
        print(f"   - split points 계산 완료: {split_elapsed:.1f}초 소요")

        # 추가 데이터 준비 (테이블별 특수 처리)
        extra_data = self._prepare_extra_data(syncer)

        # 공유 카운터
        progress_counter = Value("i", 0)
        processes = []

        # 워커 생성
        syncer.loggers["application"].info(f"워커 {self.num_workers}개 생성 시작")
        for i in range(self.num_workers):
            start_id, end_id = points[i], points[i + 1]
            p = Process(
                target=_worker_process,
                args=(
                    syncer.table_name,
                    start_id,
                    end_id,
                    extra_data,
                    progress_counter,
                    syncer.schema,  # 스키마 전달
                    i + 1,  # worker_id 추가
                    self.num_workers,  # total_workers 추가
                )
            )
            p.start()
            processes.append(p)
            syncer.loggers["batch"].info(f"Worker {i + 1}/{self.num_workers} 시작 - 범위: {start_id} ~ {end_id}")
            print(f"   - Worker {i + 1}/{self.num_workers} 시작: {start_id} ~ {end_id}")

        # 진행률 모니터링
        pbar = tqdm(total=total_docs, desc=f"전체 진행")
        prev = 0

        try:
            while any(p.is_alive() for p in processes):
                time.sleep(0.5)
                curr = progress_counter.value
                pbar.update(curr - prev)
                prev = curr
        finally:
            # 최종 업데이트
            curr = progress_counter.value
            pbar.update(curr - prev)
            pbar.close()

            # 모든 워커 종료 대기
            for p in processes:
                p.join()

        syncer.total_synced = progress_counter.value
        syncer.loggers["application"].info(
            f"[{syncer.table_name}] 병렬 동기화 완료: {progress_counter.value:,}건 처리"
        )
        print(f"✅ [{syncer.table_name}] 병렬 동기화 완료: {progress_counter.value:,}건 처리")

    def _get_split_points(self, collection, query: dict, total: int, test_limit: int = None) -> list[ObjectId]:
        """
        ObjectId 범위를 워커 수만큼 분할 (최적화 버전)

        기존 skip() 방식 대신 _id 목록을 한번에 가져와서 메모리에서 분할.
        - 기존: skip(N) × num_workers 번 → O(N × workers) 스캔
        - 개선: 전체 _id 1번 스캔 → O(N) 스캔, 메모리에서 분할
        """
        num = self.num_workers

        print(f"   - split points 계산 중 (_id 목록 로드)...")

        # 1단계: _id만 가져오기 (인덱스 스캔, 빠름)
        cursor = collection.find(query, {"_id": 1}).sort("_id", 1)
        if test_limit:
            cursor = cursor.limit(test_limit)
        all_ids = [doc["_id"] for doc in cursor]

        actual_total = len(all_ids)
        print(f"   - 미동기화 문서 수: {actual_total:,}건")

        if actual_total == 0:
            return [ObjectId()]

        # 2단계: 메모리에서 균등 분할
        step = actual_total // num

        split_points = []
        for i in range(num):
            idx = i * step
            if idx < actual_total:
                split_points.append(all_ids[idx])

        # sentinel (마지막 경계)
        split_points.append(ObjectId())

        print(f"   - split points 계산 완료: {len(split_points) - 1}개 범위")

        return split_points

    def _prepare_extra_data(self, syncer: 'BaseSyncer') -> dict:
        """
        병렬 처리에 필요한 추가 데이터 준비 (테이블별 특수 처리)

        Returns:
            워커에 전달할 추가 데이터 딕셔너리
        """
        # bid 테이블의 경우 notice_keys 로드
        if syncer.table_name == "bid":
            print(f"   - notice_keys 로드 중...")
            syncer.psql_cur.execute(f"SELECT bidntceno, bidntceord FROM {syncer.schema}.notice;")
            notice_keys = set(syncer.psql_cur.fetchall())
            print(f"   - notice_keys 로드 완료: {len(notice_keys):,}건")
            syncer.loggers["application"].info(f"notice_keys 로드 완료: {len(notice_keys):,}건")
            return {"notice_keys": notice_keys}

        return {}


def _merge_documents_worker(mongo_db, config: dict, primary_doc: dict) -> tuple[dict, list]:
    """
    워커에서 사용할 다중 컬렉션 병합 함수

    Args:
        mongo_db: MongoDB 데이터베이스 객체
        config: 테이블 설정
        primary_doc: 메인 컬렉션 문서

    Returns:
        tuple: (병합된 문서, 데이터가 있는 소스의 synced_at_column 목록)
    """
    merged = primary_doc.copy()
    source_synced_columns = []

    for source in config.get("merge_sources", []):
        if source.get("is_primary"):
            continue

        collection = mongo_db[source["collection_name"]]
        join_keys = source.get("join_keys", ())

        # 조인 쿼리 생성
        join_query = {key: primary_doc.get(key) for key in join_keys}

        projection = source.get("projection") or {"_id": 0}
        doc = collection.find_one(join_query, projection) or {}

        if doc:  # 데이터가 있는 경우에만 synced_at_column 추가
            merged.update(doc)
            if source.get("synced_at_column"):
                source_synced_columns.append(source["synced_at_column"])

    return merged, source_synced_columns


def _worker_process(
    table_name: str,
    start_id: ObjectId,
    end_id: ObjectId,
    extra_data: dict,
    progress_counter: Value,
    schema: str = "data",
    worker_id: int = 0,
    total_workers: int = 1
):
    """
    워커 프로세스 함수 (병렬 처리용)

    Args:
        table_name: 테이블명
        start_id: 처리 시작 ObjectId
        end_id: 처리 종료 ObjectId
        extra_data: 추가 데이터 (notice_keys 등)
        progress_counter: 공유 카운터
        schema: PostgreSQL 스키마명
        worker_id: 워커 번호 (1부터 시작)
        total_workers: 전체 워커 수
    """
    import os
    from collections import defaultdict
    worker_start_time = time.time()
    worker_tag = f"[Worker {worker_id}/{total_workers}]"
    pid = os.getpid()

    print(f"{worker_tag} 프로세스 시작 (PID: {pid})")

    from common.init_mongodb import init_mongodb
    from common.init_psql import init_psql
    from sync_data.sync_config import get_config, get_primary_source
    from sync_data.sync.utils.postgres_meta import PostgresMeta

    # 각 프로세스는 독립적인 DB 연결 생성
    mongo_server, mongo_client = init_mongodb()
    mongo_db = mongo_client.get_database("gfcon_raw")

    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    config = get_config(table_name)
    primary_source = get_primary_source(config)

    collection = mongo_db[primary_source["collection_name"]]
    sync_flag = primary_source["sync_flag"]

    # merge_sources 여부 확인
    has_merge_sources = len(config.get("merge_sources", [])) > 1

    # 쿼리: is_synced != True AND _id 범위
    query = {
        sync_flag: {"$ne": True},
        "_id": {"$gte": start_id, "$lt": end_id}
    }

    # 해당 범위의 문서 수 카운트
    range_count = collection.count_documents(query)
    print(f"{worker_tag} 담당 문서 수: {range_count:,}건" + (" (다중 컬렉션 병합)" if has_merge_sources else ""))

    cursor = collection.find(query).batch_size(1000)

    # PostgreSQL 메타데이터 (스키마 지정)
    psql_meta = PostgresMeta(psql_conn, schema=schema).get_column_types(config["psql_table"])
    psql_columns = list(psql_meta.keys())
    placeholder = "(" + ",".join(["%s"] * len(psql_columns)) + ")"
    pk_conflict = f"({', '.join(config['psql_pk'])})"

    # 버퍼
    buffer = []
    synced_ids_map = defaultdict(list)  # 다중 컬렉션용
    batch_size = config["batch_size"]
    batch_count = 0
    processed_count = 0
    skipped_count = 0

    field_aliases = config.get("field_aliases")
    notice_keys = extra_data.get("notice_keys")

    # 현재 시간 (synced_at용, KST)
    # 멀티프로세싱에서 전역 상수 접근 문제 방지를 위해 내부 정의
    kst = timezone(timedelta(hours=9))
    now = datetime.now(kst)

    for doc in cursor:
        # 다중 컬렉션 병합
        source_synced_columns = []
        if has_merge_sources:
            merged_doc, source_synced_columns = _merge_documents_worker(mongo_db, config, doc)
        else:
            merged_doc = doc

        # 변환
        row_dict = transform_document(psql_meta, merged_doc, field_aliases)
        row_dict.pop("_id", None)

        # synced_at 컬럼 설정
        if "synced_at" in psql_columns:
            row_dict["synced_at"] = now

        # 소스별 synced_at 컬럼 설정 (bssamt_synced_at, win_synced_at 등)
        for col in source_synced_columns:
            if col in psql_columns:
                row_dict[col] = now

        # bid 테이블 외래키 체크
        if table_name == "bid" and notice_keys is not None:
            fk_config = config.get("foreign_key_check")
            notice_key_fields = fk_config["notice_keys"]
            fk_key = tuple(row_dict.get(field) for field in notice_key_fields)

            if fk_key not in notice_keys:
                skipped_count += 1
                continue  # skip

            # bizrno 기본값 처리
            bizrno_field = fk_config["company_key"]
            if not row_dict.get(bizrno_field):
                row_dict[bizrno_field] = config.get("default_bizrno", "__DEFAULT__")

        buffer.append(tuple(row_dict.get(col) for col in psql_columns))

        # 동기화된 문서 ID 추적 (다중 컬렉션)
        synced_ids_map[primary_source["collection_name"]].append(doc["_id"])

        if has_merge_sources:
            for source in config["merge_sources"]:
                if source.get("is_primary"):
                    continue
                coll_name = source["collection_name"]
                join_keys = source.get("join_keys", ())
                join_query = {key: doc.get(key) for key in join_keys}

                merged_coll = mongo_db[coll_name]
                merged_doc_id = merged_coll.find_one(join_query, {"_id": 1})
                if merged_doc_id:
                    synced_ids_map[coll_name].append(merged_doc_id["_id"])

        # 배치 flush
        if len(buffer) >= batch_size:
            _flush_worker_batch_multi(
                psql_cur, psql_conn, mongo_db, config,
                config["psql_table"], psql_columns,
                placeholder, pk_conflict,
                buffer, synced_ids_map,
                progress_counter,
                schema,
                pk_cols=config["psql_pk"]
            )
            batch_count += 1
            processed_count += len(buffer)

            # 10배치마다 진행 상황 출력
            if batch_count % 10 == 0:
                elapsed = time.time() - worker_start_time
                rate = processed_count / elapsed if elapsed > 0 else 0
                print(f"{worker_tag} 배치 {batch_count} 완료 - 처리: {processed_count:,}건, 스킵: {skipped_count:,}건, 속도: {rate:.0f}건/초")

            buffer.clear()
            synced_ids_map.clear()

    # 남은 버퍼 처리
    if buffer:
        _flush_worker_batch_multi(
            psql_cur, psql_conn, mongo_db, config,
            config["psql_table"], psql_columns,
            placeholder, pk_conflict,
            buffer, synced_ids_map,
            progress_counter,
            schema,
            pk_cols=config["psql_pk"]
        )
        batch_count += 1
        processed_count += len(buffer)

    # 워커 완료 로그
    worker_elapsed = time.time() - worker_start_time
    rate = processed_count / worker_elapsed if worker_elapsed > 0 else 0
    print(f"{worker_tag} ✅ 완료 - 처리: {processed_count:,}건, 스킵: {skipped_count:,}건, 배치: {batch_count}개, 소요: {worker_elapsed:.1f}초, 평균: {rate:.0f}건/초")

    # 정리
    psql_cur.close()
    psql_conn.close()
    mongo_client.close()


def _flush_worker_batch_multi(
    psql_cur, psql_conn, mongo_db, config,
    psql_table, psql_columns,
    placeholder, pk_conflict,
    buffer, synced_ids_map,
    progress_counter,
    schema,
    pk_cols=None
):
    """워커의 배치를 PostgreSQL에 Upsert하고 다중 MongoDB 컬렉션 마킹"""
    if not buffer:
        return

    # PostgreSQL Upsert (스키마 포함)
    qualified_table_name = f"{schema}.{psql_table}"

    # PK 컬럼 제외한 업데이트 대상 컬럼
    pk_set = set(pk_cols) if pk_cols else set()
    update_cols = [col for col in psql_columns if col not in pk_set]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])

    sql = f"""
        INSERT INTO {qualified_table_name} ({', '.join(psql_columns)})
        VALUES %s
        ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
    """
    execute_values(psql_cur, sql, buffer, template=placeholder)
    psql_conn.commit()

    # 다중 MongoDB 컬렉션 마킹
    for source in config.get("merge_sources", []):
        coll_name = source["collection_name"]
        sync_flag = source["sync_flag"]
        ids = synced_ids_map.get(coll_name, [])

        if ids:
            collection = mongo_db[coll_name]
            collection.update_many(
                {"_id": {"$in": ids}},
                {"$set": {sync_flag: True}}
            )

    # 진행률 카운터 업데이트
    if progress_counter:
        with progress_counter.get_lock():
            progress_counter.value += len(buffer)


def _flush_worker_batch(
    psql_cur, psql_conn, mongo_collection,
    psql_table, psql_columns,
    placeholder, pk_conflict,
    buffer, synced_ids, sync_flag,
    progress_counter,
    schema,
    pk_cols=None
):
    """워커의 배치를 PostgreSQL에 Upsert하고 MongoDB 마킹 (단일 컬렉션용, 하위 호환)"""
    if not buffer:
        return

    # PostgreSQL Upsert (스키마 포함)
    qualified_table_name = f"{schema}.{psql_table}"

    # PK 컬럼 제외한 업데이트 대상 컬럼
    pk_set = set(pk_cols) if pk_cols else set()
    update_cols = [col for col in psql_columns if col not in pk_set]
    update_set = ', '.join([f"{col} = EXCLUDED.{col}" for col in update_cols])

    sql = f"""
        INSERT INTO {qualified_table_name} ({', '.join(psql_columns)})
        VALUES %s
        ON CONFLICT {pk_conflict} DO UPDATE SET {update_set};
    """
    execute_values(psql_cur, sql, buffer, template=placeholder)
    psql_conn.commit()

    # MongoDB 마킹
    if synced_ids:
        mongo_collection.update_many(
            {"_id": {"$in": synced_ids}},
            {"$set": {sync_flag: True}}
        )

    # 진행률 카운터 업데이트
    if progress_counter:
        with progress_counter.get_lock():
            progress_counter.value += len(buffer)
