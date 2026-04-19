"""
DB 명세서 CSV 자동 생성 스크립트

PostgreSQL 데이터베이스의 테이블 정보를 조회하여 CSV 형태의 명세서를 생성합니다.
"""

import os
import sys
import csv
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from common.init_psql import init_psql


# 범주형으로 판단할 최대 고유값 개수 (이 값 이하면 범주형으로 판단)
CATEGORICAL_THRESHOLD = 100


def get_table_list(cursor, schema: str) -> list:
    """스키마 내 모든 테이블 목록 조회"""
    cursor.execute("""
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
          AND table_type = 'BASE TABLE'
        ORDER BY table_name
    """, (schema,))
    return [row[0] for row in cursor.fetchall()]


def get_column_info(cursor, schema: str, table_name: str) -> list:
    """테이블의 컬럼 메타정보 조회"""
    cursor.execute("""
        SELECT
            c.column_name,
            c.data_type,
            c.character_maximum_length,
            c.numeric_precision,
            c.numeric_scale,
            c.is_nullable,
            c.column_default,
            c.ordinal_position
        FROM information_schema.columns c
        WHERE c.table_schema = %s
          AND c.table_name = %s
        ORDER BY c.ordinal_position
    """, (schema, table_name))
    return cursor.fetchall()


def get_primary_keys(cursor, schema: str, table_name: str) -> set:
    """테이블의 Primary Key 컬럼 목록 조회"""
    cursor.execute("""
        SELECT kcu.column_name
        FROM information_schema.table_constraints tc
        JOIN information_schema.key_column_usage kcu
            ON tc.constraint_name = kcu.constraint_name
            AND tc.table_schema = kcu.table_schema
        WHERE tc.constraint_type = 'PRIMARY KEY'
          AND tc.table_schema = %s
          AND tc.table_name = %s
    """, (schema, table_name))
    return {row[0] for row in cursor.fetchall()}


def get_column_comments(cursor, schema: str, table_name: str) -> dict:
    """컬럼별 코멘트(설명) 조회"""
    cursor.execute("""
        SELECT
            a.attname AS column_name,
            d.description
        FROM pg_class c
        JOIN pg_namespace n ON n.oid = c.relnamespace
        JOIN pg_attribute a ON a.attrelid = c.oid
        LEFT JOIN pg_description d ON d.objoid = c.oid AND d.objsubid = a.attnum
        WHERE n.nspname = %s
          AND c.relname = %s
          AND a.attnum > 0
          AND NOT a.attisdropped
    """, (schema, table_name))
    return {row[0]: row[1] or '' for row in cursor.fetchall()}


def get_table_stats(cursor, schema: str, table_name: str, columns: list) -> dict:
    """
    테이블의 모든 컬럼 통계를 단일 쿼리로 조회 (NULL 갯수, 범주 갯수)

    Args:
        columns: get_column_info()에서 반환된 컬럼 정보 리스트

    Returns:
        {column_name: {'null_count': int, 'distinct_count': int}, ...}
    """
    full_table_name = f'"{schema}"."{table_name}"'

    # 각 컬럼별 NULL 개수와 DISTINCT 개수를 한 번에 조회하는 쿼리 생성
    select_parts = []
    for col in columns:
        col_name = col[0]
        quoted_col = f'"{col_name}"'
        select_parts.append(f'COUNT(*) - COUNT({quoted_col}) AS "{col_name}_nulls"')
        select_parts.append(f'COUNT(DISTINCT {quoted_col}) AS "{col_name}_distinct"')

    query = f"SELECT {', '.join(select_parts)} FROM {full_table_name}"

    try:
        cursor.execute(query)
        result = cursor.fetchone()

        stats = {}
        for i, col in enumerate(columns):
            col_name = col[0]
            null_count = result[i * 2]
            distinct_count = result[i * 2 + 1]
            stats[col_name] = {
                'null_count': null_count,
                'distinct_count': distinct_count
            }

        return stats

    except Exception as e:
        print(f"  [WARN] {table_name} 통계 조회 실패: {e}")
        return {}


def format_data_type(data_type: str, char_max_length: int, numeric_precision: int, numeric_scale: int) -> str:
    """데이터 타입 문자열 포맷팅"""
    if char_max_length:
        return f"{data_type}({char_max_length})"
    elif numeric_precision and data_type == 'numeric':
        if numeric_scale:
            return f"{data_type}({numeric_precision},{numeric_scale})"
        return f"{data_type}({numeric_precision})"
    return data_type


def format_length(char_max_length: int, numeric_precision: int) -> str:
    """길이 정보 포맷팅"""
    if char_max_length:
        return str(char_max_length)
    elif numeric_precision:
        return str(numeric_precision)
    return ''


def generate_schema_docs(schema: str = None, output_path: str = None, tables: list = None):
    """
    DB 명세서 CSV 생성

    Args:
        schema: 대상 스키마명 (기본값: 환경변수 POSTGRES_SCHEMA 또는 'data')
        output_path: 출력 CSV 파일 경로 (기본값: db_docs/schema_docs_{timestamp}.csv)
        tables: 대상 테이블 목록 (기본값: 스키마 내 모든 테이블)
    """
    schema = schema or os.getenv("POSTGRES_SCHEMA", "data")

    if output_path is None:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        output_path = os.path.join(
            os.path.dirname(os.path.abspath(__file__)),
            f"schema_docs_{timestamp}.csv"
        )

    print(f"DB 명세서 생성 시작")
    print(f"  스키마: {schema}")
    print(f"  출력 파일: {output_path}")

    # DB 연결
    server, conn = init_psql()
    cursor = conn.cursor()

    try:
        # 테이블 목록 조회
        if tables is None:
            tables = get_table_list(cursor, schema)

        print(f"  대상 테이블 수: {len(tables)}")

        # CSV 작성
        rows = []
        headers = [
            '테이블명', '컬럼명', '타입', '범주형 여부', '범주 갯수',
            'NULL 갯수', '길이', 'PK', 'NN', '국문 설명'
        ]

        for table_name in tables:
            print(f"\n  처리 중: {table_name}")

            # 컬럼 정보 조회
            columns = get_column_info(cursor, schema, table_name)
            primary_keys = get_primary_keys(cursor, schema, table_name)
            comments = get_column_comments(cursor, schema, table_name)

            # 테이블 전체 통계를 단일 쿼리로 조회
            stats = get_table_stats(cursor, schema, table_name, columns)

            for col in columns:
                col_name, data_type, char_max_len, num_precision, num_scale, is_nullable, _, _ = col

                # 통계 정보 가져오기
                col_stats = stats.get(col_name, {})
                null_count = col_stats.get('null_count')
                distinct_count = col_stats.get('distinct_count')

                # 범주형 여부 판단
                is_categorical = (
                    distinct_count is not None
                    and distinct_count <= CATEGORICAL_THRESHOLD
                    and data_type not in (
                        'text', 'json', 'jsonb', 'bytea', 'timestamp', 'timestamptz',
                        'date', 'time', 'timetz', 'uuid'
                    )
                )

                row = {
                    '테이블명': table_name,
                    '컬럼명': col_name,
                    '타입': format_data_type(data_type, char_max_len, num_precision, num_scale),
                    '범주형 여부': 'Y' if is_categorical else 'N',
                    '범주 갯수': distinct_count if distinct_count is not None else '',
                    'NULL 갯수': null_count if null_count is not None else '',
                    '길이': format_length(char_max_len, num_precision),
                    'PK': 'Y' if col_name in primary_keys else '',
                    'NN': 'Y' if is_nullable == 'NO' else '',
                    '국문 설명': comments.get(col_name, '')
                }
                rows.append(row)

        # CSV 파일 저장
        with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.DictWriter(f, fieldnames=headers)
            writer.writeheader()
            writer.writerows(rows)

        print(f"\n완료: {len(rows)}개 컬럼 정보 저장")
        print(f"출력 파일: {output_path}")

        return output_path

    finally:
        cursor.close()
        conn.close()
        if server:
            server.stop()


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='DB 명세서 CSV 생성')
    parser.add_argument('--schema', '-s', type=str, help='대상 스키마명')
    parser.add_argument('--output', '-o', type=str, help='출력 파일 경로')
    parser.add_argument('--tables', '-t', nargs='+', help='대상 테이블 목록 (공백으로 구분)')

    args = parser.parse_args()

    generate_schema_docs(
        schema=args.schema,
        output_path=args.output,
        tables=args.tables
    )
