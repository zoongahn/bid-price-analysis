from typing import Any

from common.init_psql import init_psql
from utils import *

# 각 Postgres 타입 => 변환 함수
_TYPE_CONVERTERS = {
	"integer": to_int,
	"bigint": to_int,
	"smallint": to_int,
	"numeric": to_decimal,
	"double precision": to_decimal,
	"timestamp without time zone": to_datetime,
	"timestamp with time zone": to_datetime,
	"timestamp": to_datetime,
	"date": to_datetime,  # date도 YYYY-MM-DD → datetime.date 로 변환
	"time": to_datetime,
	"time without time zone": to_datetime,
	"character": str,
	"text": str,
	"character varying": str,
}


def transform_document(psql_conn,
                       table_name: str,
                       doc: dict[str, Any],
                       field_aliases: list[tuple[str, str]] = None,
                       ) -> dict[str, Any]:
	if psql_conn is not None:
		psql_columns = PostgresMeta(psql_conn).get_column_types(table_name)

	"""Mongo raw → Postgres ready dict (컬럼명 = notice 테이블 실제 칼럼)"""
	# ① 몽고 키를 전부 소문자로 만들어 Postgres 컬럼과 맞춘다
	lowercase_doc = {k.lower(): v for k, v in doc.items() if k != "_id"}

	if field_aliases:
		for pg_field, mongo_field in field_aliases:
			if pg_field not in lowercase_doc and mongo_field in doc:
				lowercase_doc[pg_field] = doc[mongo_field]

	transformed: dict[str, Any] = {}

	for col, pg_type in psql_columns.items():
		raw_val = lowercase_doc.get(col)

		# 빈 문자열·하이픈·공백 → NULL
		if raw_val == "":
			transformed[col] = None
			continue

		fn = _TYPE_CONVERTERS.get(pg_type, lambda x: x)
		transformed[col] = fn(raw_val)

	return transformed
