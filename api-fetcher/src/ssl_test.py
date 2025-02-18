import ssl

import requests
from requests.adapters import HTTPAdapter
from urllib3.poolmanager import PoolManager


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


url = "https://apis.data.go.kr/1230000/ad/BidPublicInfoService/getBidPblancListInfoCnstwk"

params = {
	"serviceKey": "OX2lNp+mKh6nT0VmeiI55CtNrKK8qZ2qLWTRzg4VZ/dbitnPlwrTu1i/+KkCrhwuU7naO/y+PowQ6csHGlCIYQ==",
	"pageNo": "1",
	"numOfRows": "10",
	"inqryDiv": "1",
	"inqryBgnDt": "202001010000",
	"type": "json",
	"inqryEndDt": "202001012359"
}

# 1) SSLContext 생성
ssl_ctx = ssl.create_default_context()
# 2) TLS 1.3 비활성 → TLS 1.2 이하
ssl_ctx.maximum_version = ssl.TLSVersion.TLSv1_2
# 3) "보안 레벨"을 1로 낮추어, 구버전 Cipher까지 허용
ssl_ctx.set_ciphers("DEFAULT:@SECLEVEL=1")

session = requests.Session()
session.mount("https://", SSLContextAdapter(ssl_context=ssl_ctx))

response = session.get(url, params=params)

# 상태 코드 출력
print(f"Status Code: {response.status_code}")

# 응답 내용 출력
try:
	print(response.json())  # JSON 형태일 경우
except Exception:
	print(response.text)  # JSON 파싱 실패 시 원본 출력
