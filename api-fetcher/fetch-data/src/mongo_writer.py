from typing import Any, Dict, List, Optional
from pymongo.errors import DuplicateKeyError


# ---------------------------------------------------------------------------
# Persistence layer
# ---------------------------------------------------------------------------
class MongoWriter:
	"""Wraps MongoDB collection with safe insert/update (upsert) behaviour."""

	def __init__(self, db, collection_name: str, unique_fields: List[str]):
		self.collection = db[collection_name]
		self.unique_fields = unique_fields
		self._ensure_index()

	def upsert(self, item: Dict[str, Any]) -> str:
		"""
			"insert"  -> 새 문서가 삽입됨
			"update"  -> 중복으로 인해 수정 수행
			"error"   -> 다른 예외가 발생 (로그는 여기서 남기고, 예외는 상위에서 처리)
		"""
		try:
			# 1) insert 시도
			self.collection.insert_one(item)
			return "insert"

		except DuplicateKeyError:
			# 2) 중복이면 update 수행
			item.pop("_id", None)  # _id 필드 제거 (원본 로직과 동일)

			update_query = {field: item[field] for field in self.unique_fields}
			self.collection.update_one(update_query, {"$set": item})
			return "update"

		except Exception as exc:
			# 3) 기타 에러는 내부 로깅 후 'error' 반환
			from common.logger import setup_loggers

			loggers = setup_loggers()
			loggers["application"].error(f"Mongo upsert 실패: {exc}", exc_info=True)
			loggers["error"].error(f"Mongo upsert 실패: {exc}", exc_info=True)
			return "error"

	def _ensure_index(self) -> None:
		index_spec = [(field, 1) for field in self.unique_fields]
		self.collection.create_index(index_spec, unique=True)
