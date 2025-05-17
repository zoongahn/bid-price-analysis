from datetime import datetime, date, time
from decimal import Decimal


def to_int(v):
	try:
		return int(v) if v not in [None, "", "-"] else None
	except:
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
			for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d", "%H:%M:%S", "%H:%M"):
				try:
					return datetime.strptime(v, fmt)
				except ValueError:
					continue
		return None
	except:
		return None
