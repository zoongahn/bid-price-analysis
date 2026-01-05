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

    def build(
        self,
        api_type: str,
        date: str,
        sub_type: Optional[int] = None,
        bsns_div_cd: Optional[int] = None,
    ) -> Dict[str, Any]:
        params = self.params_list[api_type][sub_type].copy()
        # pubData API의 경우 bsnsDivCd 설정
        if api_type == "pubData" and bsns_div_cd is not None:
            params["bsnsDivCd"] = bsns_div_cd
        return self._set_date_params(api_type, params, date, sub_type)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    def _set_date_params(
        self, api_type: str, params: Dict[str, Any], date: str, sub_type: Optional[int]
    ):
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
                0: {
                    "serviceKey": sk,
                    "pageNo": 1,
                    "numOfRows": n,
                    "inqryDiv": 1,
                    "type": "json",
                    "inqryBgnDt": None,
                    "inqryEndDt": None,
                },
            },
            "company": {
                2: {
                    "serviceKey": sk,
                    "pageNo": 1,
                    "numOfRows": n,
                    "inqryDiv": 2,  # 변경일 기준 (chgDt) - 조달업체기본정보
                    "type": "json",
                    "inqryBgnDt": None,
                    "inqryEndDt": None,
                },
                3: {
                    "serviceKey": sk,
                    "pageNo": 1,
                    "numOfRows": n,
                    "inqryDiv": 3,  # 시스템변경일 기준 (systmChgDt) - 조달업체업종정보
                    "type": "json",
                    "inqryBgnDt": None,
                    "inqryEndDt": None,
                }
            },
            "institution": {
                1: {
                    "serviceKey": sk,
                    "pageNo": 1,
                    "numOfRows": n,
                    "inqryDiv": 2,  # 변경일 기준 (chgDt)
                    "type": "json",
                    "inqryBgnDt": None,
                    "inqryEndDt": None,
                }
            },
            # bsnsDivCd (사업구분코드): 1=물품, 2=외자, 3=공사, 5=용역
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
                    "bsnsDivCd": 3,  # 공사
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
            "company": ["inqryBgnDt", "inqryEndDt"],
            "institution": ["inqryBgnDt", "inqryEndDt"],
            "bid": [],
            "pubData": {
                1: ["bidNtceBgnDt", "bidNtceEndDt"],
                2: ["opengBgnDt", "opengEndDt"],
                3: ["cntrctCnclsBgnDate", "cntrctCnclsEndDate"],
            },
        }
