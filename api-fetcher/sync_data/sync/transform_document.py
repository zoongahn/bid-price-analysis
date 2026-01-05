from typing import Any

from common.init_psql import init_psql
from sync_data.sync.utils.type_converter import to_int, to_decimal, to_datetime

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


def transform_document(psql_columns_meta: dict[str, str],
                       doc: dict[str, Any],
                       field_aliases: list[tuple[str, str]] | None = None,
                       ) -> dict[str, Any]:
	# ① 몽고 키를 전부 소문자로 만들어 Postgres 컬럼과 맞춘다
	lowercase_doc = {k.lower(): v for k, v in doc.items() if k != "_id"}

	if field_aliases:
		for pg_field, mongo_field in field_aliases:
			if pg_field not in lowercase_doc and mongo_field in doc:
				lowercase_doc[pg_field] = doc[mongo_field]

	transformed: dict[str, Any] = {}

	for col, pg_type in psql_columns_meta.items():
		raw_val = lowercase_doc.get(col)

		# None → NULL, 빈 문자열은 TEXT 타입일 때만 유지
		if raw_val is None:
			transformed[col] = None
			continue
		if raw_val == "":
			# TEXT 타입은 빈 문자열 유지, 나머지는 NULL
			if pg_type in ("text", "character varying", "character"):
				transformed[col] = ""
			else:
				transformed[col] = None
			continue

		fn = _TYPE_CONVERTERS.get(pg_type, lambda x: x)

		# BIGINT 타입일 때 원본 값도 함께 전달하여 필드명 로깅 가능하게
		if pg_type == "bigint":
			result = fn(raw_val)
			if result is None and raw_val not in [None, "", "-"]:
				# 변환 실패하거나 범위 초과한 경우
				try:
					int_val = int(raw_val)
					if int_val > 9223372036854775807 or int_val < -9223372036854775808:
						print(f"⚠️  [{col}] BIGINT 범위 초과: {raw_val} -> NULL")
				except:
					pass
			transformed[col] = result
		else:
			transformed[col] = fn(raw_val)

	return transformed
