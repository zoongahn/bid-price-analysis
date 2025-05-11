from typing import Any

from common.init_psql import init_psql
from sync_notice.type_converter import *
from utils.postgres_meta import PostgresMeta

psql_server, psql_conn = init_psql()

_META = PostgresMeta(psql_conn)
# notice 테이블의 column_name: pg_type 매핑
_COL_TYPES = _META.get_column_types("notice")

# 각 Postgres 타입 => 변환 함수
_TYPE_CONVERTERS = {
	"integer": to_int,
	"bigint": to_int,
	"numeric": to_decimal,
	"double precision": to_decimal,
	"timestamp without time zone": to_datetime,
	"timestamp with time zone": to_datetime,
	"timestamp": to_datetime,
	"date": to_datetime,  # date도 YYYY-MM-DD → datetime.date 로 변환
	"character": str,
	"text": str,
	"character varying": str,
}


def transform_document(doc: dict[str, Any]) -> dict[str, Any]:
	"""Mongo raw → Postgres ready dict (컬럼명 = notice 테이블 실제 칼럼)"""
	# ① 몽고 키를 전부 소문자로 만들어 Postgres 컬럼과 맞춘다
	lowercase_doc = {k.lower(): v for k, v in doc.items() if k != "_id"}

	transformed: dict[str, Any] = {}

	for col, pg_type in _COL_TYPES.items():
		raw_val = lowercase_doc.get(col)

		# 빈 문자열·하이픈·공백 → NULL
		if raw_val in ("", "-", " ", None):
			transformed[col] = None
			continue

		fn = _TYPE_CONVERTERS.get(pg_type, lambda x: x)
		transformed[col] = fn(raw_val)

	return transformed
