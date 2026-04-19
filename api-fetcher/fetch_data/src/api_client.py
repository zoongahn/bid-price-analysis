import logging
import requests
import time
import ssl
from typing import Any, Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from common.api_key_manager import api_key_manager


# SSLContextAdapter (TLS 1.2 이하 강제 & 보안레벨 낮추기) ----------------
class SSLContextAdapter(HTTPAdapter):
	def __init__(self, ssl_context=None, **kwargs):
		self._ssl_context = ssl_context
		super().__init__(**kwargs)

	def init_poolmanager(self, connections, maxsize, block=False, **kwargs):
		if self._ssl_context is not None:
			kwargs["ssl_context"] = self._ssl_context
		self.poolmanager = PoolManager(
			num_pools=connections, maxsize=maxsize, block=block, **kwargs
		)


class ApiClient:
	"""Handles all HTTP communication with retry logic and API key rotation."""

	# 트래픽 초과 감지 패턴
	TRAFFIC_EXHAUSTED_PATTERNS = [
		"LIMITED_NUMBER_OF_SERVICE_REQUESTS_EXCEEDS_ERROR",
		"SERVICE_KEY_IS_NOT_REGISTERED_ERROR",
		"DAILY_TRAFFIC_LIMIT",
		"일일 트래픽",
	]

	def __init__(self, base_url: str):
		self.base_url = base_url
		# 이미 설정된 로거 사용 (setup_loggers 재호출 방지)
		self.logger = {
			"application": logging.getLogger("application"),
			"error": logging.getLogger("error"),
		}
		self.session = self._create_ssl_session()

	# ---------------------------------------------------------------------
	# Public helpers
	# ---------------------------------------------------------------------
	def get(self, endpoint: str, params: Dict[str, Any], retry_interval: int = 10) -> Dict[str, Any]:
		"""GET with automatic JSON decode, retry, and API key rotation."""
		full_url = f"{self.base_url}/{endpoint}"
		consecutive_429_count = 0  # 연속 429 카운터

		while True:
			# 현재 사용 가능한 API 키 가져오기
			try:
				current_key = api_key_manager.get_current_key()
				params["serviceKey"] = current_key
			except RuntimeError as e:
				# 모든 키 소진
				self.logger["error"].error(str(e))
				raise

			try:
				response = self.session.get(full_url, params=params, timeout=30)

				# HTTP 429 (Too Many Requests) 처리
				if response.status_code == 429:
					consecutive_429_count += 1
					if consecutive_429_count < 3:
						# 일시적 경쟁일 수 있음 - 대기 후 같은 키로 재시도
						self.logger["application"].warning(
							f"HTTP 429 - Retry {consecutive_429_count}/3 with same key after 2s"
						)
						time.sleep(2)
						continue
					else:
						# 3번 연속 429 - 진짜 소진으로 판단, 키 전환
						self.logger["application"].warning(
							f"HTTP 429 - Traffic limit exceeded, switching API key"
						)
						api_key_manager.mark_exhausted()
						consecutive_429_count = 0
						continue

				response.raise_for_status()
				data = response.json()

				# 응답 내 트래픽 초과 에러 확인
				if self._is_traffic_exhausted(data):
					self.logger["application"].warning(
						f"Traffic limit detected in response, switching API key"
					)
					api_key_manager.mark_exhausted()
					continue

				return data

			except requests.exceptions.HTTPError as exc:
				# 500 에러 등은 재시도
				if exc.response is not None and exc.response.status_code >= 500:
					self.logger["application"].error(
						f"HTTP {exc.response.status_code} error – retry in {retry_interval}s"
					)
					time.sleep(retry_interval)
					continue
				raise

			except (
				requests.exceptions.ConnectionError,
				requests.exceptions.JSONDecodeError,
				requests.exceptions.Timeout,
				requests.exceptions.ReadTimeout,
			) as exc:
				self.logger["application"].error(
					f"{exc.__class__.__name__} while requesting {full_url} – retry in {retry_interval}s"
				)
				time.sleep(retry_interval)
				continue

			except Exception as exc:  # pragma: no cover
				self.logger["error"].error("Unhandled exception in ApiClient", exc_info=True)
				raise

	def _is_traffic_exhausted(self, data: dict) -> bool:
		"""응답 데이터에서 트래픽 초과 여부 확인"""
		try:
			# 일반적인 공공데이터 API 에러 응답 구조
			result_code = data.get("response", {}).get("header", {}).get("resultCode", "")
			result_msg = data.get("response", {}).get("header", {}).get("resultMsg", "")

			# 에러 코드/메시지 확인
			combined = f"{result_code} {result_msg}".upper()
			for pattern in self.TRAFFIC_EXHAUSTED_PATTERNS:
				if pattern.upper() in combined:
					return True

			# OpenAPI 스타일 에러 응답
			if "cmmMsgHeader" in data:
				err_msg = data.get("cmmMsgHeader", {}).get("errMsg", "")
				for pattern in self.TRAFFIC_EXHAUSTED_PATTERNS:
					if pattern.upper() in err_msg.upper():
						return True

			return False
		except Exception:
			return False

	# ------------------------------------------------------------------
	# Private helpers
	# ------------------------------------------------------------------
	@staticmethod
	def _create_ssl_session() -> requests.Session:
		# 1) SSLContext 생성
		ssl_ctx = ssl.create_default_context()
		# 2) TLS 1.3 비활성 → TLS 1.2 이하
		ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
		# 3) "보안 레벨"을 1로 낮추어, 구버전 Cipher까지 허용
		ssl_ctx.set_ciphers("DEFAULT:@SECLEVEL=1")
		session = requests.Session()
		session.mount("https://", SSLContextAdapter(ssl_context=ssl_ctx))
		return session
