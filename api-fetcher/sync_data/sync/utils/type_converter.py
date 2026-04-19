from datetime import datetime, date, time
from decimal import Decimal

# PostgreSQL BIGINT 범위: -9223372036854775808 ~ 9223372036854775807
BIGINT_MAX = 9223372036854775807
BIGINT_MIN = -9223372036854775808


def to_int(v):
	try:
		if v in [None, "", "-"]:
			return None

		result = int(v)

		# BIGINT 범위를 벗어나면 None 반환 (또는 로깅)
		if result > BIGINT_MAX or result < BIGINT_MIN:
			print(f"⚠️  BIGINT 범위 초과: {result} -> NULL로 변환")
			return None

		return result
	except Exception as e:
		# 변환 실패 시 None 반환
		return None


def to_decimal(v):
	try:
		return Decimal(v) if v not in [None, "", "-"] else None
	except:
		return None


def to_datetime(v):
	try:
		if isinstance(v, (datetime, date, time)):
			return v
		if not v:
			return None
		if isinstance(v, str):
			for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M", "%Y-%m-%d", "%H:%M:%S", "%H:%M"):
				try:
					return datetime.strptime(v, fmt)
				except ValueError:
					continue
		return None
	except:
		return None
