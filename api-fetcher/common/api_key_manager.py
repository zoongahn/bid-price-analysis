"""
API 키 순환 매니저

N개의 API 키를 관리하며, 일일 트래픽 초과 시 다음 키로 자동 전환합니다.
.env 파일에서 API_SERVICE_KEY_1, API_SERVICE_KEY_2, ... 형식으로 키를 추가할 수 있습니다.

사용법:
    from common.api_key_manager import api_key_manager

    key = api_key_manager.get_current_key()
    # API 호출 후 트래픽 초과 감지 시
    api_key_manager.mark_exhausted()
    key = api_key_manager.get_current_key()  # 다음 키 반환
"""

import os
import logging
from datetime import datetime, date
from pathlib import Path
from threading import Lock
from dotenv import load_dotenv

# 프로젝트 루트의 .env 파일 로드
project_root = Path(__file__).resolve().parent.parent
load_dotenv(project_root / ".env")

logger = logging.getLogger("application")


class ApiKeyManager:
    """API 키 순환 관리자 (싱글톤)"""

    _instance = None
    _lock = Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
                    cls._instance._initialized = False
        return cls._instance

    def __init__(self):
        if self._initialized:
            return

        # API 키 목록 로드 (API_SERVICE_KEY_1, API_SERVICE_KEY_2, ... 형식)
        self._keys = []
        i = 1
        while True:
            name = f"API_SERVICE_KEY_{i}"
            key = os.getenv(name)
            if key:
                self._keys.append({"name": name, "key": key, "exhausted_date": None})
                i += 1
            else:
                break

        if not self._keys:
            raise ValueError("No API keys found in environment variables")

        self._current_index = 0
        self._assigned_key_index = None  # 워커별 고정 키 인덱스
        self._initialized = True

        logger.info(f"ApiKeyManager initialized with {len(self._keys)} keys")

    def assign_key_for_worker(self, worker_id: int, workers_per_key: int = 2):
        """워커에게 담당 키 할당 (키당 workers_per_key개 워커)"""
        key_index = worker_id // workers_per_key
        if key_index >= len(self._keys):
            raise ValueError(f"Worker {worker_id} has no assigned key (only {len(self._keys)} keys available)")

        self._assigned_key_index = key_index
        self._current_index = key_index
        key_name = self._keys[key_index]["name"]
        logger.info(f"Worker {worker_id} assigned to {key_name}")

    def get_current_key(self) -> str:
        """현재 사용 가능한 API 키 반환"""
        today = date.today()

        # 고정 키가 할당된 경우
        if self._assigned_key_index is not None:
            key_info = self._keys[self._assigned_key_index]
            if key_info["exhausted_date"] == today:
                raise RuntimeError(f"Assigned API key {key_info['name']} exhausted for today")
            return key_info["key"]

        # 일반 모드: 모든 키 순환
        available_keys = [
            i for i, k in enumerate(self._keys)
            if k["exhausted_date"] != today
        ]

        if not available_keys:
            raise RuntimeError("All API keys exhausted for today")

        # 현재 키가 소진되었으면 다음 사용 가능한 키로 이동
        if self._keys[self._current_index]["exhausted_date"] == today:
            self._current_index = available_keys[0]
            logger.info(f"Switched to API key: {self._keys[self._current_index]['name']}")

        return self._keys[self._current_index]["key"]

    def mark_exhausted(self):
        """현재 키를 오늘 날짜로 소진 처리하고 다음 키로 전환"""
        today = date.today()

        # 고정 키가 할당된 경우
        if self._assigned_key_index is not None:
            key_info = self._keys[self._assigned_key_index]
            if key_info["exhausted_date"] != today:
                key_info["exhausted_date"] = today
                logger.warning(f"Assigned API key {key_info['name']} marked as exhausted for {today}")
            return

        # 일반 모드: 키 전환
        current_key_info = self._keys[self._current_index]

        if current_key_info["exhausted_date"] != today:
            current_key_info["exhausted_date"] = today
            logger.warning(
                f"API key {current_key_info['name']} marked as exhausted for {today}"
            )

        # 다음 사용 가능한 키 찾기
        for i in range(len(self._keys)):
            next_index = (self._current_index + 1 + i) % len(self._keys)
            if self._keys[next_index]["exhausted_date"] != today:
                self._current_index = next_index
                logger.info(f"Switched to API key: {self._keys[self._current_index]['name']}")
                return

        logger.error("All API keys exhausted for today!")

    def get_status(self) -> dict:
        """현재 키 상태 반환"""
        today = date.today()
        return {
            "total_keys": len(self._keys),
            "current_key": self._keys[self._current_index]["name"],
            "available_today": sum(
                1 for k in self._keys if k["exhausted_date"] != today
            ),
            "keys": [
                {
                    "name": k["name"],
                    "exhausted": k["exhausted_date"] == today,
                    "exhausted_date": str(k["exhausted_date"]) if k["exhausted_date"] else None,
                }
                for k in self._keys
            ],
        }

    def reset_for_new_day(self):
        """새 날짜가 되면 모든 키의 소진 상태 리셋 (자동으로 처리됨)"""
        # get_current_key()에서 날짜 비교로 자동 처리됨
        pass


# 싱글톤 인스턴스
api_key_manager = ApiKeyManager()
