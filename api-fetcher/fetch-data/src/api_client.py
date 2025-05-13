import requests
import time
import ssl
from typing import Any, Dict, List, Optional
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager

from common.logger import setup_loggers


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
	"""Handles all HTTP communication with retry logic."""

	def __init__(self, base_url: str):
		self.base_url = base_url
		self.logger = setup_loggers()
		self.session = self._create_ssl_session()

	# ---------------------------------------------------------------------
	# Public helpers
	# ---------------------------------------------------------------------
	def get(self, endpoint: str, params: Dict[str, Any], retry_interval: int = 10) -> Dict[str, Any]:
		"""GET with automatic JSON decode & retry."""
		full_url = f"{self.base_url}/{endpoint}"
		while True:
			try:
				response = self.session.get(full_url, params=params, timeout=30)
				response.raise_for_status()
				return response.json()
			except (requests.exceptions.ConnectionError, requests.exceptions.JSONDecodeError) as exc:
				self.logger["application"].error(
					f"{exc.__class__.__name__} while requesting {full_url} – retry in {retry_interval}s"
				)
				time.sleep(retry_interval)
				continue
			except Exception as exc:  # pragma: no cover
				self.logger["error"].error("Unhandled exception in ApiClient", exc_info=True)
				raise

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
