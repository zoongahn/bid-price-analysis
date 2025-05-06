from datetime import datetime
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
		return datetime.strptime(v, "%Y-%m-%d %H:%M:%S") if v else None
	except:
		return None
