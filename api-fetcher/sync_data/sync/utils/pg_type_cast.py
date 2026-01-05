from decimal import Decimal
from datetime import date, datetime, time
from dateutil.parser import parse as dt_parse


def pg_cast(value: str | None, pg_type: str):
	"""MongoDB → PostgreSQL 타입 캐스팅."""
	if value in (None, "", "-"):
		return None

	try:
		match pg_type:  # information_schema.data_type 값
			case "text" | "character varying":
				return str(value)

			case "integer":
				return int(value)

			case "bigint":
				return int(value)

			case "numeric" | "double precision" | "real":
				return Decimal(value)

			case "date":
				# 'YYYY‑MM‑DD' / 'YYYY/MM/DD' 모두 허용
				return date.fromisoformat(value[:10]) if len(value) >= 10 else None

			case "time without time zone" | "time with time zone":
				# 'HH:MM(:SS)' 문자열 → datetime.time
				return time.fromisoformat(value)

			case "timestamp without time zone" | "timestamp with time zone":
				# dateutil 로 거의 모든 포맷 파싱
				return dt_parse(value)

			case _:
				# 알 수 없는 타입은 그대로 text 로
				return value
	except Exception:
		# 변환 실패 → NULL 삽입
		return None
