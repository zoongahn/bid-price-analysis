"""
BaseSyncer 추상 클래스

모든 동기화 클래스의 베이스가 되는 추상 클래스입니다.
공통 동기화 로직을 정의하고, 테이블별 특수 로직은 서브클래스에서 구현합니다.
"""

from abc import ABC, abstractmethod
from typing import Optional
from bson import ObjectId
import os

from common.init_mongodb import init_mongodb
from common.init_psql import init_psql
from common.logger import setup_sync_loggers, update_log_meta
from sync_data.sync_config import get_config, get_primary_source
from sync_data.sync.utils.postgres_meta import PostgresMeta


class BaseSyncer(ABC):
    """
    동기화 클래스의 추상 베이스 클래스

    Template Method 패턴을 사용하여 동기화 흐름을 정의하고,
    세부 구현은 서브클래스에서 오버라이드합니다.
    """

    def __init__(self, table_name: str, schema: str = None, test_limit: int = None):
        """
        Args:
            table_name: 동기화할 PostgreSQL 테이블명
            schema: PostgreSQL 스키마명 (기본값: 환경변수 POSTGRES_SCHEMA 또는 'data')
            test_limit: 테스트 모드 시 최대 동기화 건수 (기본값: None = 제한 없음)
        """
        self.table_name = table_name
        self.config = get_config(table_name)
        self.test_limit = test_limit

        # 스키마 설정: 인자 > 환경변수 > 기본값(data)
        self.schema = schema or os.getenv("POSTGRES_SCHEMA", "data")

        # 로거 설정
        log_result = setup_sync_loggers(
            table_name=table_name,
            schema=self.schema,
            process_type="sync",
        )
        self.loggers = log_result["loggers"]
        self.log_dir = log_result["log_dir"]
        self.meta_path = log_result["meta_path"]

        self.loggers["application"].info(
            f"동기화 시작: {self.schema}.{table_name}"
        )

        # MongoDB 연결
        self.mongo_server, self.mongo_client = init_mongodb()
        self.mongo_db = self.mongo_client.get_database("gfcon_raw")
        self.loggers["application"].info("MongoDB 연결 완료")

        # PostgreSQL 연결
        self.psql_server, self.psql_conn = init_psql()
        self.psql_cur = self.psql_conn.cursor()
        self.loggers["application"].info("PostgreSQL 연결 완료")

        # 테이블 존재 여부 확인
        self._verify_table_exists()

        # PostgreSQL 메타데이터 (스키마 지정)
        self.psql_meta = PostgresMeta(
            self.psql_conn, schema=self.schema
        ).get_column_types(self.config["psql_table"])
        self.psql_columns = list(self.psql_meta.keys())

        # Fully qualified table name (스키마.테이블)
        self.qualified_table_name = f"{self.schema}.{self.config['psql_table']}"

        # 통계
        self.total_synced = 0
        self.total_skip = 0
        self._error_count = 0

    def _verify_table_exists(self):
        """
        테이블 존재 여부 확인 및 자동 생성

        테이블이 없으면 SQL 파일을 읽어서 자동 생성합니다.
        """
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
            self._create_table_from_sql()
        else:
            self.loggers["application"].info(
                f"테이블 {self.schema}.{self.config['psql_table']} 확인됨"
            )

    def _create_table_from_sql(self):
        """
        SQL 파일을 읽어서 테이블 생성

        Raises:
            FileNotFoundError: SQL 파일이 존재하지 않는 경우
            RuntimeError: 테이블 생성 실패
        """
        sql_file = os.path.join(
            os.path.dirname(__file__),
            "..",
            "create",
            f"{self.config['psql_table']}.sql"
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
        # DROP TABLE IF EXISTS tablename → DROP TABLE IF EXISTS schema.tablename
        sql_content = sql_content.replace(
            f"DROP TABLE IF EXISTS {self.config['psql_table']}",
            f"DROP TABLE IF EXISTS {self.schema}.{self.config['psql_table']}"
        )

        # CREATE TABLE IF NOT EXISTS tablename → CREATE TABLE IF NOT EXISTS schema.tablename
        sql_content = sql_content.replace(
            f"CREATE TABLE IF NOT EXISTS {self.config['psql_table']}",
            f"CREATE TABLE IF NOT EXISTS {self.schema}.{self.config['psql_table']}"
        )

        # 인덱스도 스키마 지정
        # CREATE INDEX ... ON tablename → CREATE INDEX ... ON schema.tablename
        sql_content = sql_content.replace(
            f" ON {self.config['psql_table']}(",
            f" ON {self.schema}.{self.config['psql_table']}("
        )
        # 괄호 앞에 공백이 있는 경우도 처리
        sql_content = sql_content.replace(
            f" ON {self.config['psql_table']} (",
            f" ON {self.schema}.{self.config['psql_table']} ("
        )

        # COMMENT ON TABLE/COLUMN도 스키마 지정
        sql_content = sql_content.replace(
            f"COMMENT ON TABLE {self.config['psql_table']}",
            f"COMMENT ON TABLE {self.schema}.{self.config['psql_table']}"
        )
        sql_content = sql_content.replace(
            f"COMMENT ON COLUMN {self.config['psql_table']}.",
            f"COMMENT ON COLUMN {self.schema}.{self.config['psql_table']}."
        )

        # INSERT INTO 문도 스키마 지정
        sql_content = sql_content.replace(
            f"INSERT INTO {self.config['psql_table']} ",
            f"INSERT INTO {self.schema}.{self.config['psql_table']} "
        )

        # ALTER TABLE 스키마 지정
        sql_content = sql_content.replace(
            f"ALTER TABLE {self.config['psql_table']}",
            f"ALTER TABLE {self.schema}.{self.config['psql_table']}"
        )

        # FOREIGN KEY REFERENCES 스키마 지정
        # 알려진 참조 테이블들에 대해 스키마 적용
        referenced_tables = ["notice", "company", "bid", "institution"]
        for ref_table in referenced_tables:
            # REFERENCES table_name ( 패턴
            sql_content = sql_content.replace(
                f"REFERENCES {ref_table} (",
                f"REFERENCES {self.schema}.{ref_table} ("
            )
            # REFERENCES table_name( 패턴 (공백 없는 경우)
            sql_content = sql_content.replace(
                f"REFERENCES {ref_table}(",
                f"REFERENCES {self.schema}.{ref_table}("
            )
            # 하드코딩된 data.table 패턴도 현재 스키마로 변경
            sql_content = sql_content.replace(
                f"REFERENCES data.{ref_table}(",
                f"REFERENCES {self.schema}.{ref_table}("
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

    @abstractmethod
    def sync(self):
        """
        메인 동기화 메서드 (서브클래스에서 구현 필수)

        이 메서드는 실제 동기화 전략을 실행합니다.
        """
        pass

    def get_primary_collection(self):
        """메인 MongoDB 컬렉션 반환"""
        primary_source = get_primary_source(self.config)
        return self.mongo_db[primary_source["collection_name"]]

    def get_primary_sync_flag(self) -> str:
        """메인 컬렉션의 sync_flag 반환"""
        primary_source = get_primary_source(self.config)
        return primary_source["sync_flag"]

    def build_unsynced_query(self) -> dict:
        """
        미동기화 문서 조회 쿼리 생성

        Returns:
            MongoDB 쿼리 딕셔너리
        """
        sync_flag = self.get_primary_sync_flag()
        return {sync_flag: {"$ne": True}}

    def preprocess_document(self, doc: dict) -> Optional[dict]:
        """
        MongoDB 문서 전처리 (필요시 서브클래스에서 오버라이드)

        Args:
            doc: MongoDB 문서

        Returns:
            전처리된 문서 또는 None (skip 시)
        """
        # 기본 전처리 함수 적용 (설정에 있으면)
        preprocess_name = self.config.get("preprocess")
        if preprocess_name:
            from sync_data.sync.preprocessors import (
                preprocess_notice_industry_type,
            )

            preprocess_map = {
                "notice_industry_type": preprocess_notice_industry_type,
            }

            preprocess_func = preprocess_map.get(preprocess_name)
            if preprocess_func:
                doc = preprocess_func(doc)

        return doc

    def validate_row(self, row_dict: dict) -> bool:
        """
        PostgreSQL row 유효성 검증 (필요시 서브클래스에서 오버라이드)

        Args:
            row_dict: 변환된 row 딕셔너리

        Returns:
            유효하면 True, skip할 경우 False
        """
        return True

    def reconnect_postgres(self):
        """PostgreSQL 연결 재생성 (메모리 누수 방지)"""
        self.psql_cur.close()
        self.psql_conn.close()
        self.psql_server, self.psql_conn = init_psql()
        self.psql_cur = self.psql_conn.cursor()

    def close(self, status: str = None):
        """
        리소스 정리 및 메타데이터 업데이트

        Args:
            status: 동기화 상태 ("success", "failed", None=자동판단)
        """
        # 상태 자동 판단
        if status is None:
            status = "success" if self._error_count == 0 else "completed_with_errors"

        # 메타데이터 업데이트
        if hasattr(self, "meta_path"):
            update_log_meta(
                self.meta_path,
                status=status,
                records_total=self.total_synced + self.total_skip,
                records_synced=self.total_synced,
                records_skipped=self.total_skip,
                error_count=self._error_count,
            )

        # 로그 기록
        if hasattr(self, "loggers"):
            self.loggers["application"].info(
                f"동기화 종료: {self.schema}.{self.table_name} - "
                f"동기화: {self.total_synced:,}건, 스킵: {self.total_skip:,}건, "
                f"에러: {self._error_count}건"
            )

        # 리소스 정리
        if hasattr(self, "psql_cur"):
            self.psql_cur.close()
        if hasattr(self, "psql_conn"):
            self.psql_conn.close()
        if hasattr(self, "mongo_client"):
            self.mongo_client.close()

    def print_sync_info(self):
        """동기화 시작 정보 출력 및 로깅"""
        info_lines = [
            f"동기화 정보:",
            f"  - 대상 스키마: {self.schema}",
            f"  - 대상 테이블: {self.config['psql_table']}",
            f"  - Full Name: {self.schema}.{self.config['psql_table']}",
            f"  - 동기화 방식: {'병렬 처리' if self.config.get('parallel') else '단일 프로세스'}",
            f"  - Batch Size: {self.config['batch_size']:,}",
        ]
        for line in info_lines:
            self.loggers["application"].info(line)

        # 콘솔 출력도 유지 (Airflow 로그용)
        print(f"\n{'=' * 80}")
        print(f"📊 동기화 정보")
        print(f"{'=' * 80}")
        for line in info_lines[1:]:  # "동기화 정보:" 제외
            print(f"  {line}")
        print(f"{'=' * 80}\n")

    def print_summary(self):
        """동기화 결과 요약 출력 및 로깅"""
        summary = (
            f"[{self.schema}.{self.table_name}] 동기화 완료 - "
            f"총 동기화: {self.total_synced:,}건, Skip: {self.total_skip:,}건"
        )
        self.loggers["application"].info(summary)

        # 콘솔 출력도 유지 (Airflow 로그용)
        print(f"\n{'=' * 80}")
        print(f"✅ [{self.schema}.{self.table_name}] 동기화 완료")
        print(f"   - 총 동기화: {self.total_synced:,}건")
        if self.total_skip > 0:
            print(f"   - Skip: {self.total_skip:,}건")
        print(f"{'=' * 80}\n")
