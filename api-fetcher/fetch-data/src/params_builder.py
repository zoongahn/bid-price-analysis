from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Parameter builder
# ---------------------------------------------------------------------------
class ParamsBuilder:
	"""Generate API params & map date fields."""

	def __init__(self, api_service_key: str, num_of_rows: int = 500):
		self.api_service_key = api_service_key
		self.num_of_rows = num_of_rows
		self.params_list = self._build_params_list()
		self.date_field_map = self._build_date_field_map()

	def build(self, api_type: str, date: str, sub_type: Optional[int] = None) -> Dict[str, Any]:
		params = (
			self.params_list[api_type][sub_type].copy()
			if api_type == "pubData"
			else self.params_list[api_type].copy()
		)
		return self._set_date_params(api_type, params, date, sub_type)

	# ------------------------------------------------------------------
	# Internal helpers
	# ------------------------------------------------------------------
	def _set_date_params(self, api_type: str, params: Dict[str, Any], date: str, sub_type: Optional[int]):
		start, end = f"{date}0000", f"{date}2359"
		fields = (
			self.date_field_map[api_type][sub_type]
			if api_type == "pubData"
			else self.date_field_map[api_type]
		)
		for idx, key in enumerate(fields):
			params[key] = start if idx == 0 else end
		return params

	def _build_params_list(self):
		sk, n = self.api_service_key, self.num_of_rows
		return {
			"notice": {
				"serviceKey": sk,
				"pageNo": 1,
				"numOfRows": n,
				"inqryDiv": 1,
				"type": "json",
				"inqryBgnDt": None,
				"inqryEndDt": None,
			},
			"bid": {
				"serviceKey": sk,
				"pageNo": 1,
				"numOfRows": n,
				"type": "json",
				"bidNtceNo": None,
			},
			"pubData": {
				1: {
					"serviceKey": sk,
					"pageNo": 1,
					"numOfRows": n,
					"type": "json",
					"bsnsDivCd": None,
					"bidNtceBgnDt": None,
					"bidNtceEndDt": None,
				},
				2: {
					"serviceKey": sk,
					"pageNo": 1,
					"numOfRows": n,
					"type": "json",
					"bsnsDivCd": 3,
					"opengBgnDt": None,
					"opengEndDt": None,
				},
				3: {
					"serviceKey": sk,
					"pageNo": 1,
					"numOfRows": n,
					"type": "json",
					"cntrctCnclsBgnDate": None,
					"cntrctCnclsEndDate": None,
				},
			},
		}

	@staticmethod
	def _build_date_field_map():
		return {
			"notice": ["inqryBgnDt", "inqryEndDt"],
			"bid": [],
			"pubData": {
				1: ["bidNtceBgnDt", "bidNtceEndDt"],
				2: ["opengBgnDt", "opengEndDt"],
				3: ["cntrctCnclsBgnDate", "cntrctCnclsEndDate"],
			},
		}
