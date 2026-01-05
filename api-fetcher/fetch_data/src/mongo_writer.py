from typing import Any, Dict, List, Optional
from pymongo.errors import DuplicateKeyError
from datetime import datetime, timezone, timedelta
import re

# 한국 표준시 (UTC+9)
KST = timezone(timedelta(hours=9))


# ---------------------------------------------------------------------------
# Persistence layer
# ---------------------------------------------------------------------------
class MongoWriter:
	"""Wraps MongoDB collection with safe insert/update (upsert) behaviour."""

	# 필드 밀림 교정이 필요한 컬렉션
	FIELD_SHIFT_COLLECTIONS = [
		"입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회"
	]

	def __init__(self, db, collection_name: str, unique_fields: List[str]):
		self.collection = db[collection_name]
		self.collection_name = collection_name
		self.unique_fields = unique_fields
		self._ensure_index()

	def _correct_field_shift(self, item: Dict[str, Any]) -> Dict[str, Any]:
		"""
		면허제한정보조회 컬렉션의 필드 밀림 현상 교정.
		나라장터 API 응답에서 필드가 1칸씩 앞으로 밀려오는 경우가 있음.

		비정상 패턴:
		  indstrytyMfrcFldList: "2021-08-04 10:20:20"  <- rgstDt 값
		  rgstDt: "공사"                               <- bsnsDivNm 값
		  bsnsDivNm: ""

		교정 후:
		  indstrytyMfrcFldList: ""
		  rgstDt: "2021-08-04 10:20:20"
		  bsnsDivNm: "공사"
		"""
		if self.collection_name not in self.FIELD_SHIFT_COLLECTIONS:
			return item

		rgstDt = item.get("rgstDt", "")

		# rgstDt가 날짜 형식이 아니면 밀림 현상으로 판단
		# 정상 형식: "2021-08-04 10:20:20"
		if rgstDt and not re.match(r"^\d{4}-\d{2}-\d{2}", rgstDt):
			# 필드 복원
			item["rgstDt"] = item.get("indstrytyMfrcFldList", "")
			item["bsnsDivNm"] = rgstDt  # 원래 rgstDt에 있던 값
			item["indstrytyMfrcFldList"] = ""  # 원래 값 알 수 없음
			item["_field_corrected"] = True

		return item

	def upsert(self, item: Dict[str, Any]) -> str:
		"""
			"insert"  -> 새 문서가 삽입됨
			"update"  -> 중복으로 인해 수정 수행
			"error"   -> 다른 예외가 발생 (로그는 여기서 남기고, 예외는 상위에서 처리)
		"""
		# 필드 밀림 교정 (해당 컬렉션만)
		item = self._correct_field_shift(item)

		# 수집 시점 기록 (KST)
		item["collected_at"] = datetime.now(KST)

		try:
			# 1) insert 시도
			self.collection.insert_one(item)
			return "insert"

		except DuplicateKeyError:
			# 2) 중복이면 update 수행
			item.pop("_id", None)  # _id 필드 제거 (원본 로직과 동일)
			item["is_synced"] = False  # 데이터 변경 시 재동기화 필요

			# 낙찰정보 컬렉션은 notice, bid 두 테이블로 동기화되므로 별도 플래그도 리셋
			if self.collection_name == "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보":
				item["notice_is_synced"] = False

			update_query = {field: item[field] for field in self.unique_fields}
			self.collection.update_one(update_query, {"$set": item})
			return "update"

		except Exception as exc:
			# 3) 기타 에러는 내부 로깅 후 'error' 반환
			import logging

			logging.getLogger("application").error(f"Mongo upsert 실패: {exc}", exc_info=True)
			logging.getLogger("error").error(f"Mongo upsert 실패: {exc}", exc_info=True)
			return "error"

	def _ensure_index(self) -> None:
		index_spec = [(field, 1) for field in self.unique_fields]
		self.collection.create_index(index_spec, unique=True)
