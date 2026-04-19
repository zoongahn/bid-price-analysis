"""
보조 컬렉션 전용 동기화 (Secondary Source Syncer)

메인 공고가 먼저 동기화된 후, 보조 데이터(기초금액, 낙찰정보, 사업자상태 등)가
나중에 수집된 경우를 처리합니다.

sync_config.py의 설정을 기반으로 모든 보조 컬렉션을 자동으로 처리합니다.
"""

from datetime import datetime, timezone, timedelta
from collections import defaultdict
from tqdm import tqdm

from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
from common.logger import setup_loggers

from sync_data.sync_config import SYNC_CONFIGS
from sync_data.sync.transform_document import transform_document
from sync_data.sync.utils.postgres_meta import PostgresMeta

# 한국 표준시 (UTC+9)
KST = timezone(timedelta(hours=9))


def extract_secondary_sources():
    """
    sync_config.py에서 모든 보조 컬렉션 정보 추출

    Returns:
        list: [
            {
                "table_name": "notice",
                "psql_pk": ("bidntceno", "bidntceord"),
                "collection_name": "...",
                "sync_flag": "is_synced",
                "join_keys": ("bidNtceNo", "bidNtceOrd"),
                "projection": {...},
                "field_mapping": {...},
                "synced_at_column": "bssamt_synced_at",
                "bsns_div": "공사",  # multi_source인 경우
                "one_per_join_key": False,  # 낙찰정보처럼 join_key당 1건만 동기화
            },
            ...
        ]
    """
    secondary_sources = []

    for table_name, config in SYNC_CONFIGS.items():
        psql_pk = config.get("psql_pk", ())

        # multi_source 모드 (notice_unified, bid, reserve_price_range)
        if config.get("multi_source") or config.get("categories"):
            categories = config.get("categories", [])
            for category in categories:
                bsns_div = category.get("bsns_div") or category.get("name")
                for source in category.get("merge_sources", []):
                    if source.get("is_primary"):
                        continue

                    secondary_sources.append({
                        "table_name": config["psql_table"],
                        "psql_pk": psql_pk,
                        "collection_name": source["collection_name"],
                        "sync_flag": source.get("sync_flag", "is_synced"),
                        "join_keys": source.get("join_keys", ()),
                        "projection": source.get("projection"),
                        "field_mapping": source.get("field_mapping"),
                        "synced_at_column": source.get("synced_at_column"),
                        "bsns_div": bsns_div,
                        "one_per_join_key": source.get("one_per_join_key", False),
                    })
        else:
            # 단일 소스 모드 (notice, company, institution 등)
            for source in config.get("merge_sources", []):
                if source.get("is_primary"):
                    continue

                secondary_sources.append({
                    "table_name": config["psql_table"],
                    "psql_pk": psql_pk,
                    "collection_name": source["collection_name"],
                    "sync_flag": source.get("sync_flag", "is_synced"),
                    "join_keys": source.get("join_keys", ()),
                    "projection": source.get("projection"),
                    "field_mapping": source.get("field_mapping"),
                    "synced_at_column": source.get("synced_at_column"),
                    "bsns_div": None,
                    "one_per_join_key": source.get("one_per_join_key", False),
                })

    return secondary_sources


class SecondarySyncer:
    """보조 컬렉션 전용 동기화 클래스"""

    def __init__(self, schema: str = "data", batch_size: int = 1000):
        self.schema = schema
        self.batch_size = batch_size

        # DB 연결
        self.mongo_server, self.mongo_client = init_mongodb()
        self.mongo_db = self.mongo_client.get_database("gfcon_raw")

        self.psql_server, self.psql_conn = init_psql()
        self.psql_cur = self.psql_conn.cursor()

        # PostgreSQL 메타데이터 캐시
        self._psql_meta_cache = {}

        # 로거
        log_result = setup_loggers(
            service_name="sync_data",
            operation_name="secondary_sync",
        )
        self.loggers = log_result["loggers"]

        # 보조 컬렉션 목록
        self.secondary_sources = extract_secondary_sources()

        # 통계
        self.stats = defaultdict(lambda: {"updated": 0, "skipped": 0, "not_found": 0})

    def get_psql_meta(self, table_name: str) -> dict:
        """PostgreSQL 테이블 메타데이터 (캐싱)"""
        if table_name not in self._psql_meta_cache:
            meta = PostgresMeta(self.psql_conn, schema=self.schema)
            self._psql_meta_cache[table_name] = meta.get_column_types(table_name)
        return self._psql_meta_cache[table_name]

    def sync_all(self):
        """모든 보조 컬렉션 동기화"""
        print("=" * 70)
        print("보조 컬렉션 전용 동기화 시작")
        print(f"대상: {len(self.secondary_sources)}개 보조 컬렉션")
        print("=" * 70)

        for source in self.secondary_sources:
            self._sync_source(source)

        # 최종 통계
        print("\n" + "=" * 70)
        print("전체 완료 통계:")
        total_updated = sum(s["updated"] for s in self.stats.values())
        total_skipped = sum(s["skipped"] for s in self.stats.values())
        total_not_found = sum(s["not_found"] for s in self.stats.values())
        print(f"  업데이트: {total_updated:,}건")
        print(f"  스킵: {total_skipped:,}건")
        print(f"  미존재: {total_not_found:,}건")
        print("=" * 70)

        self.loggers["application"].info(
            f"보조 동기화 완료: 업데이트 {total_updated:,}, "
            f"스킵 {total_skipped:,}, 미존재 {total_not_found:,}"
        )

    def sync_table(self, table_name: str):
        """특정 테이블의 보조 컬렉션만 동기화"""
        sources = [s for s in self.secondary_sources if s["table_name"] == table_name]
        if not sources:
            print(f"테이블 '{table_name}'의 보조 컬렉션이 없습니다.")
            return

        print(f"테이블 '{table_name}'의 {len(sources)}개 보조 컬렉션 동기화")
        for source in sources:
            self._sync_source(source)

    def sync_collection(self, collection_name: str):
        """특정 컬렉션만 동기화"""
        source = next(
            (s for s in self.secondary_sources if s["collection_name"] == collection_name),
            None
        )
        if not source:
            print(f"컬렉션 '{collection_name}'을 찾을 수 없습니다.")
            available = [s["collection_name"] for s in self.secondary_sources]
            print(f"사용 가능: {available}")
            return

        self._sync_source(source)

    def _sync_source(self, source: dict):
        """단일 보조 컬렉션 동기화"""
        collection_name = source["collection_name"]
        table_name = source["table_name"]
        sync_flag = source["sync_flag"]
        bsns_div = source.get("bsns_div", "")
        one_per_join_key = source.get("one_per_join_key", False)

        # 컬렉션명 축약 (출력용)
        short_name = collection_name.split(".")[-1][:40]
        if bsns_div:
            short_name = f"[{bsns_div}] {short_name}"

        collection = self.mongo_db[collection_name]

        print(f"\n{'─' * 60}")
        print(f"📦 {short_name}")

        # one_per_join_key 모드: 낙찰정보처럼 join_key당 1건만 동기화
        if one_per_join_key:
            self._sync_source_one_per_key(source, collection, short_name)
            return

        # 일반 모드: 모든 미동기화 문서 처리
        query = {sync_flag: {"$ne": True}}
        total = collection.count_documents(query)

        print(f"   → {table_name} 테이블, {total:,}건 대상")

        if total == 0:
            print(f"   ✓ 동기화할 데이터 없음")
            return

        self.loggers["application"].info(
            f"[{short_name}] {total:,}건 동기화 시작 → {table_name}"
        )

        # PostgreSQL 메타데이터
        psql_meta = self.get_psql_meta(table_name)
        psql_columns = list(psql_meta.keys())

        cursor = collection.find(query).batch_size(self.batch_size)

        synced_ids = []
        stat_key = f"{table_name}:{collection_name}"
        now = datetime.now(KST)

        for doc in tqdm(cursor, total=total, desc=f"   동기화"):
            result = self._update_record(
                source, doc, table_name, psql_meta, psql_columns, now
            )

            self.stats[stat_key][result] += 1

            # 처리 완료된 문서 ID 추가 (not_found도 마킹)
            if result in ("updated", "not_found"):
                synced_ids.append(doc["_id"])

            # 배치 단위로 MongoDB 마킹
            if len(synced_ids) >= self.batch_size:
                self._mark_synced(collection, synced_ids, sync_flag)
                synced_ids.clear()

        # 남은 문서 마킹
        if synced_ids:
            self._mark_synced(collection, synced_ids, sync_flag)

        stats = self.stats[stat_key]
        print(f"   ✓ 완료: 업데이트 {stats['updated']:,}, "
              f"스킵 {stats['skipped']:,}, 미존재 {stats['not_found']:,}")

        self.loggers["application"].info(
            f"[{short_name}] 완료: 업데이트 {stats['updated']:,}, "
            f"스킵 {stats['skipped']:,}, 미존재 {stats['not_found']:,}"
        )

    def _sync_source_one_per_key(self, source: dict, collection, short_name: str):
        """
        join_key당 1건만 동기화 (낙찰정보용)

        낙찰정보는 공고당 여러 입찰이 있지만, notice 테이블에는 1건만 병합됨.
        이미 sync_flag=True인 레코드가 있는 공고는 스킵하고,
        sync_flag=True인 레코드가 없는 공고만 1건씩 동기화.
        """
        table_name = source["table_name"]
        sync_flag = source["sync_flag"]
        join_keys = source.get("join_keys", ())

        if not join_keys:
            print(f"   ⚠️ join_keys 없음, 스킵")
            return

        # 1. 이미 동기화된 join_key 조합 조회
        print(f"   → 이미 동기화된 공고 조회 중...")
        synced_keys_pipeline = [
            {"$match": {sync_flag: True}},
            {"$group": {"_id": {k: f"${k}" for k in join_keys}}},
        ]
        synced_keys = set()
        for doc in collection.aggregate(synced_keys_pipeline, allowDiskUse=True):
            key_tuple = tuple(doc["_id"].get(k) for k in join_keys)
            synced_keys.add(key_tuple)
        print(f"   → 이미 동기화된 공고: {len(synced_keys):,}건")

        # 2. 미동기화 공고 중 고유 join_key별 1건씩 조회
        print(f"   → 미동기화 공고 조회 중...")
        unsynced_pipeline = [
            {"$match": {sync_flag: {"$ne": True}}},
            {"$group": {
                "_id": {k: f"${k}" for k in join_keys},
                "doc_id": {"$first": "$_id"},
                "doc": {"$first": "$$ROOT"},
            }},
        ]

        # PostgreSQL 메타데이터
        psql_meta = self.get_psql_meta(table_name)
        psql_columns = list(psql_meta.keys())

        synced_ids = []
        stat_key = f"{table_name}:{source['collection_name']}"
        now = datetime.now(KST)

        # 미동기화 공고 처리
        unsynced_docs = list(collection.aggregate(unsynced_pipeline, allowDiskUse=True))

        # 이미 동기화된 공고 필터링
        docs_to_sync = []
        for item in unsynced_docs:
            key_tuple = tuple(item["_id"].get(k) for k in join_keys)
            if key_tuple not in synced_keys:
                docs_to_sync.append(item)

        total = len(docs_to_sync)
        print(f"   → {table_name} 테이블, {total:,}건 대상 (공고당 1건)")

        if total == 0:
            print(f"   ✓ 동기화할 데이터 없음")
            return

        self.loggers["application"].info(
            f"[{short_name}] {total:,}건 동기화 시작 → {table_name} (one_per_join_key)"
        )

        for item in tqdm(docs_to_sync, desc=f"   동기화"):
            doc = item["doc"]
            result = self._update_record(
                source, doc, table_name, psql_meta, psql_columns, now
            )

            self.stats[stat_key][result] += 1

            # 처리 완료된 문서 ID 추가
            if result in ("updated", "not_found"):
                synced_ids.append(doc["_id"])

            # 배치 단위로 MongoDB 마킹
            if len(synced_ids) >= self.batch_size:
                self._mark_synced(collection, synced_ids, sync_flag)
                synced_ids.clear()

        # 남은 문서 마킹
        if synced_ids:
            self._mark_synced(collection, synced_ids, sync_flag)

        stats = self.stats[stat_key]
        print(f"   ✓ 완료: 업데이트 {stats['updated']:,}, "
              f"스킵 {stats['skipped']:,}, 미존재 {stats['not_found']:,}")

        self.loggers["application"].info(
            f"[{short_name}] 완료: 업데이트 {stats['updated']:,}, "
            f"스킵 {stats['skipped']:,}, 미존재 {stats['not_found']:,}"
        )

    def _update_record(self, source: dict, doc: dict, table_name: str,
                       psql_meta: dict, psql_columns: list, now: datetime) -> str:
        """PostgreSQL 레코드 UPDATE"""
        join_keys = source.get("join_keys", ())
        projection = source.get("projection")
        field_mapping = source.get("field_mapping")
        synced_at_column = source.get("synced_at_column")
        psql_pk = source.get("psql_pk", ())

        # join_keys 값 추출 (WHERE 조건용)
        if not join_keys:
            return "skipped"

        # WHERE 조건 구성
        where_parts = []
        where_values = []

        for i, key in enumerate(join_keys):
            # join_keys가 (mongo_field, psql_field) 형태인 경우 처리
            if len(join_keys) == 2 and i == 1 and key not in doc:
                # 이 경우 첫번째가 mongo 필드, 두번째가 psql 필드
                mongo_field = join_keys[0]
                psql_field = join_keys[1].lower()
                value = doc.get(mongo_field)
                if value is None:
                    return "skipped"
                where_parts.append(f"{psql_field} = %s")
                where_values.append(value)
                break
            else:
                value = doc.get(key)
                if value is None:
                    return "skipped"
                where_parts.append(f"{key.lower()} = %s")
                where_values.append(value)

        # UPDATE할 필드 결정
        # projection이 {"_id": 0} 형태이면 전체 필드 사용
        # projection에 특정 필드가 1로 지정되어 있으면 해당 필드만 사용
        exclude = {"_id", "is_synced", "collected_at", "inptDt"}
        exclude.update(join_keys)

        if projection:
            # projection 값이 1인 필드만 추출 (0인 건 제외 의미)
            include_fields = [k for k, v in projection.items() if v == 1]
            if include_fields:
                # 특정 필드만 포함
                update_fields = [k for k in include_fields if k not in exclude]
            else:
                # {"_id": 0} 같은 경우 → 전체 필드 사용
                update_fields = [k for k in doc.keys() if k not in exclude]
        else:
            # projection 없으면 전체 필드
            update_fields = [k for k in doc.keys() if k not in exclude]

        if not update_fields:
            return "skipped"

        # SET 절 구성
        set_parts = []
        set_values = []

        for mongo_field in update_fields:
            raw_value = doc.get(mongo_field)

            # field_mapping 적용
            if field_mapping and mongo_field in field_mapping:
                psql_field = field_mapping[mongo_field]
            else:
                psql_field = mongo_field.lower()

            # PostgreSQL 컬럼 존재 확인
            if psql_field not in psql_columns:
                continue

            # 타입 변환
            converted = self._convert_value(raw_value, psql_meta.get(psql_field))

            set_parts.append(f"{psql_field} = %s")
            set_values.append(converted)

        # synced_at_column 추가
        if synced_at_column and synced_at_column in psql_columns:
            set_parts.append(f"{synced_at_column} = %s")
            set_values.append(now)

        if not set_parts:
            return "skipped"

        # UPDATE 실행
        sql = f"""
            UPDATE {self.schema}.{table_name}
            SET {', '.join(set_parts)}
            WHERE {' AND '.join(where_parts)}
        """

        try:
            self.psql_cur.execute(sql, set_values + where_values)
            affected = self.psql_cur.rowcount
            self.psql_conn.commit()

            return "updated" if affected > 0 else "not_found"

        except Exception as e:
            self.psql_conn.rollback()
            self.loggers["error"].error(f"UPDATE 실패: {e}, doc_id={doc.get('_id')}")
            return "skipped"

    def _convert_value(self, value, pg_type: str):
        """MongoDB 값을 PostgreSQL 타입으로 변환"""
        if value is None or value == "":
            return None

        if pg_type is None:
            return value

        pg_type = pg_type.lower()

        try:
            if "int" in pg_type or pg_type == "bigint":
                return int(value) if value not in (None, "", "-") else None
            elif pg_type in ("numeric", "decimal", "real", "double precision"):
                return float(value) if value not in (None, "", "-") else None
            elif "timestamp" in pg_type:
                return value if isinstance(value, str) and len(value) >= 10 else None
            else:
                return str(value) if value is not None else None
        except (ValueError, TypeError):
            return None

    def _mark_synced(self, collection, doc_ids: list, sync_flag: str):
        """MongoDB 동기화 플래그 마킹"""
        if doc_ids:
            collection.update_many(
                {"_id": {"$in": doc_ids}},
                {"$set": {sync_flag: True}}
            )

    def close(self):
        """DB 연결 종료"""
        self.psql_cur.close()
        self.psql_conn.close()
        self.mongo_client.close()


def sync_secondary(schema: str = "data", table: str = None, collection: str = None):
    """
    보조 컬렉션 동기화 실행 함수

    Args:
        schema: PostgreSQL 스키마명
        table: 특정 테이블만 (notice, company 등)
        collection: 특정 컬렉션만
    """
    syncer = SecondarySyncer(schema=schema)

    try:
        if collection:
            syncer.sync_collection(collection)
        elif table:
            syncer.sync_table(table)
        else:
            syncer.sync_all()
    finally:
        syncer.close()


def list_secondary_sources():
    """보조 컬렉션 목록 출력"""
    sources = extract_secondary_sources()

    print("=" * 70)
    print("보조 컬렉션 목록")
    print("=" * 70)

    by_table = defaultdict(list)
    for s in sources:
        by_table[s["table_name"]].append(s)

    for table, items in by_table.items():
        print(f"\n📋 {table} 테이블:")
        for item in items:
            bsns = f"[{item['bsns_div']}] " if item.get("bsns_div") else ""
            short = item["collection_name"].split(".")[-1][:50]
            synced_col = item.get("synced_at_column", "-")
            print(f"   • {bsns}{short}")
            print(f"     synced_at: {synced_col}")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="보조 컬렉션 전용 동기화")
    parser.add_argument("--schema", default="data", help="PostgreSQL 스키마")
    parser.add_argument("--table", help="특정 테이블만 (notice, company 등)")
    parser.add_argument("--collection", help="특정 컬렉션명")
    parser.add_argument("--list", action="store_true", help="보조 컬렉션 목록 출력")

    args = parser.parse_args()

    if args.list:
        list_secondary_sources()
    else:
        sync_secondary(schema=args.schema, table=args.table, collection=args.collection)
