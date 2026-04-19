"""
BidSyncer - 개찰결과 테이블 동기화

3개 MongoDB 컬렉션을 bid 테이블로 동기화합니다:
- 낙찰정보서비스.개찰결과개찰완료목록조회
- 낙찰정보서비스.개찰결과유찰목록조회
- 낙찰정보서비스.개찰결과재입찰목록조회

사용법:
    python -m sync_data.sync.syncers.bid_syncer --schema test
    python -m sync_data.sync.syncers.bid_syncer --schema test --types 개찰완료
    python -m sync_data.sync.syncers.bid_syncer --schema test --limit 1000
"""

from collections import defaultdict
from datetime import datetime, timezone, timedelta
from tqdm import tqdm
from psycopg2.extras import execute_values

from sync_data.sync.base_syncer import BaseSyncer
from sync_data.sync.transform_document import transform_document

# 한국 표준시 (UTC+9)
KST = timezone(timedelta(hours=9))


class BidSyncer(BaseSyncer):
    """
    개찰결과 동기화 클래스

    3개 카테고리(개찰완료/유찰/재입찰)를 순차적으로 동기화합니다.
    """

    def __init__(
        self,
        schema: str = None,
        types: list = None,
        test_limit: int = None,
    ):
        """
        Args:
            schema: PostgreSQL 스키마명
            types: 동기화할 타입 목록 (None=전체, ['개찰완료'], ['유찰', '재입찰'] 등)
            test_limit: 테스트 모드 시 타입별 최대 동기화 건수
        """
        super().__init__("bid", schema=schema, test_limit=test_limit)

        # 타입 필터링
        all_types = [cat["name"] for cat in self.config.get("categories", [])]
        if types:
            self.types = [t for t in types if t in all_types]
            if not self.types:
                raise ValueError(f"유효하지 않은 타입: {types}. 가능한 값: {all_types}")
        else:
            self.types = all_types

        # 카테고리별 통계
        self.category_stats = {}

    def sync(self):
        """동기화 실행"""
        self.print_sync_info()

        categories = [
            cat for cat in self.config.get("categories", [])
            if cat["name"] in self.types
        ]

        print(f"\n{'=' * 80}")
        print(f"📊 Bid 동기화 시작 ({len(categories)}개 타입)")
        print(f"   타입: {', '.join(cat['name'] for cat in categories)}")
        print(f"{'=' * 80}\n")

        for idx, category in enumerate(categories, 1):
            type_name = category["name"]
            merge_sources = category["merge_sources"]

            print(f"\n[{idx}/{len(categories)}] {type_name} 동기화 시작...")
            self.loggers["application"].info(f"[{idx}/{len(categories)}] {type_name} 동기화 시작")

            try:
                synced, skipped = self._sync_category(type_name, merge_sources)
                self.category_stats[type_name] = {"synced": synced, "skipped": skipped}
                self.total_synced += synced
                self.total_skip += skipped

                print(f"   ✅ {type_name} 완료: {synced:,}건 동기화, {skipped:,}건 스킵")
                self.loggers["application"].info(
                    f"{type_name} 완료: {synced:,}건 동기화, {skipped:,}건 스킵"
                )

            except Exception as e:
                self._error_count += 1
                self.loggers["error"].error(f"{type_name} 동기화 실패: {e}", exc_info=True)
                print(f"   ❌ {type_name} 실패: {e}")
                raise

        self.print_summary()

    def _sync_category(self, type_name: str, merge_sources: list) -> tuple[int, int]:
        """
        단일 카테고리 동기화

        Args:
            type_name: 타입명 (개찰완료/유찰/재입찰)
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
            raise ValueError(f"{type_name}: primary source가 정의되지 않음")

        primary_collection = self.mongo_db[primary_source["collection_name"]]
        sync_flag = primary_source["sync_flag"]

        # 미동기화 문서 조회
        query = {sync_flag: {"$ne": True}}
        total = primary_collection.count_documents(query)

        # test_limit 적용
        if self.test_limit:
            total = min(total, self.test_limit)

        self.loggers["application"].info(f"[{type_name}] 총 {total:,}건 동기화 대상")
        print(f"   📋 {type_name}: {total:,}건 동기화 대상")

        if total == 0:
            return 0, 0

        cursor = primary_collection.find(query).batch_size(1000)
        if self.test_limit:
            cursor = cursor.limit(self.test_limit)

        # 버퍼
        buffer = []
        synced_ids = []
        synced_count = 0
        skip_count = 0

        # SQL 템플릿
        placeholder = "(" + ",".join(["%s"] * len(self.psql_columns)) + ")"
        pk_conflict = f"({', '.join(self.config['psql_pk'])})"
        batch_size = self.config.get("batch_size", 5000)

        now = datetime.now(KST)
        doc_count = 0

        for doc in tqdm(cursor, total=total, desc=f"   {type_name}"):
            # 100,000건마다 PostgreSQL 연결 재생성
            if doc_count > 0 and doc_count % 100000 == 0:
                self.reconnect_postgres()

            # PostgreSQL row 변환
            row_dict = self._transform_to_psql_row(doc, now)
            if not row_dict:
                skip_count += 1
                continue

            # 유효성 검증
            if not self.validate_row(row_dict):
                skip_count += 1
                continue

            # 버퍼에 추가
            buffer.append(tuple(row_dict.get(col) for col in self.psql_columns))
            synced_ids.append(doc["_id"])

            # 배치 flush
            if len(buffer) >= batch_size:
                self._flush_to_postgres(buffer, placeholder, pk_conflict)
                self._mark_synced(primary_collection, synced_ids, sync_flag)
                synced_count += len(buffer)

                self.loggers["application"].info(
                    f"[{type_name}] {synced_count:,}건 처리 완료"
                )

                buffer = []
                synced_ids = []

            doc_count += 1

        # 남은 버퍼 flush
        if buffer:
            self._flush_to_postgres(buffer, placeholder, pk_conflict)
            self._mark_synced(primary_collection, synced_ids, sync_flag)
            synced_count += len(buffer)

            self.loggers["application"].info(
                f"[{type_name}] Final batch: {len(buffer):,}건 처리 (총: {synced_count:,}건)"
            )

        return synced_count, skip_count

    def _transform_to_psql_row(self, doc: dict, now: datetime) -> dict:
        """
        MongoDB 문서를 PostgreSQL row로 변환

        Args:
            doc: MongoDB 문서
            now: 현재 시간

        Returns:
            PostgreSQL row 딕셔너리
        """
        field_aliases = self.config.get("field_aliases")
        row_dict = transform_document(self.psql_meta, doc, field_aliases)
        row_dict.pop("_id", None)

        # prcbdrbizno NULL -> '' (PK 제약조건용)
        if row_dict.get("prcbdrbizno") is None:
            row_dict["prcbdrbizno"] = ""

        # synced_at 설정
        if "synced_at" in self.psql_columns:
            row_dict["synced_at"] = now

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

    def _mark_synced(self, collection, doc_ids: list, sync_flag: str):
        """MongoDB is_synced 플래그 업데이트"""
        if doc_ids:
            collection.update_many(
                {"_id": {"$in": doc_ids}},
                {"$set": {sync_flag: True}}
            )


def main():
    """CLI 엔트리포인트"""
    import argparse

    parser = argparse.ArgumentParser(description='Bid 테이블 동기화')
    parser.add_argument('--schema', type=str, default='test', help='PostgreSQL 스키마')
    parser.add_argument('--types', type=str, nargs='+', choices=['개찰완료', '유찰', '재입찰'],
                        help='동기화할 타입 (기본: 전체)')
    parser.add_argument('--limit', type=int, help='타입별 최대 건수 (테스트용)')

    args = parser.parse_args()

    syncer = BidSyncer(
        schema=args.schema,
        types=args.types,
        test_limit=args.limit,
    )

    try:
        syncer.sync()
    finally:
        syncer.close()


if __name__ == '__main__':
    main()
