"""
단순 1:1 동기화 유틸리티

MongoDB 컬렉션을 PostgreSQL 테이블로 그대로 동기화합니다.
설정 파일 없이 직접 컬렉션명과 테이블명을 지정할 수 있습니다.
"""

from __future__ import annotations
from typing import Optional, Callable
from bson import ObjectId
from tqdm import tqdm
from psycopg2.extras import execute_values

from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
from sync_data.sync.utils.postgres_meta import PostgresMeta
from sync_data.sync.transform_document import transform_document


class SimpleSync:
    """
    단순 1:1 동기화 클래스

    MongoDB 컬렉션 → PostgreSQL 테이블 직접 동기화
    설정 파일 불필요, 테이블이 미리 생성되어 있어야 함
    """

    def __init__(
        self,
        mongo_collection_name: str,
        psql_table_name: str,
        psql_pk: tuple[str, ...],
        batch_size: int = 10000,
        sync_flag: str = "is_synced",
        field_aliases: list[tuple[str, str]] | None = None,
        preprocess_func: callable | None = None,
    ):
        """
        Args:
            mongo_collection_name: MongoDB 컬렉션명 (전체 경로)
            psql_table_name: PostgreSQL 테이블명
            psql_pk: PostgreSQL Primary Key 컬럼명 튜플 (소문자)
                     예: ("bidntceno", "bidntceord")
            batch_size: 배치 크기 (기본 10,000)
            sync_flag: MongoDB에 마킹할 플래그명 (기본 "is_synced")
            field_aliases: 필드명 매핑 [(psql_field, mongo_field), ...]
            preprocess_func: MongoDB 문서 전처리 함수 (선택)
                             func(doc: dict) -> dict
        """
        self.mongo_collection_name = mongo_collection_name
        self.psql_table_name = psql_table_name
        self.psql_pk = psql_pk
        self.batch_size = batch_size
        self.sync_flag = sync_flag
        self.field_aliases = field_aliases
        self.preprocess_func = preprocess_func

        # MongoDB 연결
        self.mongo_server, self.mongo_client = init_mongodb()
        self.mongo_db = self.mongo_client.get_database("gfcon_raw")
        self.mongo_collection = self.mongo_db[mongo_collection_name]

        # PostgreSQL 연결
        self.psql_server, self.psql_conn = init_psql()
        self.psql_cur = self.psql_conn.cursor()

        # PostgreSQL 메타데이터
        self.psql_meta = PostgresMeta(self.psql_conn).get_column_types(psql_table_name)
        self.psql_columns = list(self.psql_meta.keys())

    def sync(self):
        """동기화 실행"""
        # 미동기화 문서 수 확인
        query = {self.sync_flag: {"$ne": True}}
        total = self.mongo_collection.count_documents(query)

        print(f"🔄 [{self.psql_table_name}] 동기화 시작")
        print(f"   MongoDB: {self.mongo_collection_name}")
        print(f"   PostgreSQL: {self.psql_table_name}")
        print(f"   총 {total:,}건 (batch={self.batch_size})\n")

        if total == 0:
            print(f"✅ 동기화할 데이터가 없습니다.")
            return

        # 커서 생성
        cursor = self.mongo_collection.find(query).batch_size(1000)

        # SQL 템플릿
        placeholder = "(" + ",".join(["%s"] * len(self.psql_columns)) + ")"
        pk_conflict = f"({', '.join(self.psql_pk)})"

        # 버퍼
        buffer = []
        synced_ids = []

        doc_count = 0
        for doc in tqdm(cursor, total=total, desc="동기화 진행"):
            # 100,000건마다 PostgreSQL 연결 재생성
            if doc_count > 0 and doc_count % 100000 == 0:
                self._reconnect_postgres()

            # 전처리 함수 적용 (있으면)
            if self.preprocess_func:
                doc = self.preprocess_func(doc)

            # 문서 변환
            row_dict = transform_document(self.psql_meta, doc, self.field_aliases)
            row_dict.pop("_id", None)

            # 버퍼에 추가
            buffer.append(tuple(row_dict.get(col) for col in self.psql_columns))
            synced_ids.append(doc["_id"])

            doc_count += 1

            # 배치 flush
            if len(buffer) >= self.batch_size:
                self._flush(buffer, placeholder, pk_conflict)
                self._mark_synced(synced_ids)
                buffer.clear()
                synced_ids.clear()

        # 남은 버퍼 처리
        if buffer:
            self._flush(buffer, placeholder, pk_conflict)
            self._mark_synced(synced_ids)

        print(f"\n✅ [{self.psql_table_name}] 동기화 완료: {doc_count:,}건 처리")

    def _flush(self, rows: list[tuple], placeholder: str, pk_conflict: str):
        """PostgreSQL에 배치 삽입"""
        if not rows:
            return

        sql = f"""
            INSERT INTO {self.psql_table_name} ({', '.join(self.psql_columns)})
            VALUES %s
            ON CONFLICT {pk_conflict} DO NOTHING;
        """
        execute_values(self.psql_cur, sql, rows, template=placeholder)
        self.psql_conn.commit()

    def _mark_synced(self, synced_ids: list[ObjectId]):
        """MongoDB에 is_synced 마킹"""
        if not synced_ids:
            return

        self.mongo_collection.update_many(
            {"_id": {"$in": synced_ids}},
            {"$set": {self.sync_flag: True}}
        )

    def _reconnect_postgres(self):
        """PostgreSQL 연결 재생성"""
        self.psql_cur.close()
        self.psql_conn.close()
        self.psql_server, self.psql_conn = init_psql()
        self.psql_cur = self.psql_conn.cursor()

    def close(self):
        """리소스 정리"""
        if hasattr(self, 'psql_cur'):
            self.psql_cur.close()
        if hasattr(self, 'psql_conn'):
            self.psql_conn.close()
        if hasattr(self, 'mongo_client'):
            self.mongo_client.close()


def sync_collection_to_table(
    mongo_collection_name: str,
    psql_table_name: str,
    psql_pk: tuple[str, ...],
    batch_size: int = 10000,
    sync_flag: str = "is_synced",
    field_aliases: list[tuple[str, str]] | None = None,
    preprocess_func: callable | None = None,
):
    """
    MongoDB 컬렉션을 PostgreSQL 테이블로 1:1 동기화 (헬퍼 함수)

    Args:
        mongo_collection_name: MongoDB 컬렉션명
        psql_table_name: PostgreSQL 테이블명
        psql_pk: Primary Key 컬럼 튜플
        batch_size: 배치 크기
        sync_flag: 동기화 플래그명
        field_aliases: 필드명 매핑
        preprocess_func: 전처리 함수

    Example:
        >>> sync_collection_to_table(
        ...     "사용자정보서비스.조달업체기본정보",
        ...     "company",
        ...     ("bizno",)
        ... )

        >>> # 전처리 함수 사용
        >>> from sync_data.sync.preprocessors import preprocess_notice_industry_type
        >>> sync_collection_to_table(
        ...     "입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회",
        ...     "notice_industry_type",
        ...     ("bidntceno", "bidntceord", "lmtgrpno", "lmtsno"),
        ...     preprocess_func=preprocess_notice_industry_type
        ... )
    """
    syncer = None
    try:
        syncer = SimpleSync(
            mongo_collection_name=mongo_collection_name,
            psql_table_name=psql_table_name,
            psql_pk=psql_pk,
            batch_size=batch_size,
            sync_flag=sync_flag,
            field_aliases=field_aliases,
            preprocess_func=preprocess_func,
        )
        syncer.sync()
    except Exception as e:
        print(f"❌ 동기화 실패: {e}")
        raise
    finally:
        if syncer:
            syncer.close()


def main():
    """테스트용 메인 함수"""
    import sys

    if len(sys.argv) < 4:
        print("Usage: python simple_sync.py <collection_name> <table_name> <pk1> [pk2] [pk3]...")
        print("\nExample:")
        print('  python simple_sync.py "사용자정보서비스.조달업체기본정보" company bizno')
        print('  python simple_sync.py "입찰공고정보서비스.입찰공고목록정보에대한공사조회" notice bidntceno bidntceord')
        sys.exit(1)

    collection_name = sys.argv[1]
    table_name = sys.argv[2]
    pk_columns = tuple(sys.argv[3:])

    print("\n" + "=" * 80)
    print("단순 1:1 동기화")
    print("=" * 80)
    print(f"MongoDB 컬렉션: {collection_name}")
    print(f"PostgreSQL 테이블: {table_name}")
    print(f"Primary Key: {', '.join(pk_columns)}")
    print("=" * 80 + "\n")

    sync_collection_to_table(collection_name, table_name, pk_columns)


if __name__ == "__main__":
    main()
