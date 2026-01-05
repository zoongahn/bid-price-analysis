import os
import json
import logging
import colorlog
from datetime import datetime

# ✅ 커스텀 로그 레벨 추가
VERIFY_LEVEL = 22
FETCH_LEVEL = 23
DAY_LEVEL = 24
YEAR_LEVEL = 25

logging.addLevelName(VERIFY_LEVEL, "VERIFY")
logging.addLevelName(FETCH_LEVEL, "FETCH")
logging.addLevelName(DAY_LEVEL, "DAY")
logging.addLevelName(YEAR_LEVEL, "YEAR")


# ✅ Logger 클래스 확장
class CustomLogger(logging.getLoggerClass()):
	def verify(self, message, *args, **kwargs):
		if self.isEnabledFor(VERIFY_LEVEL):
			self._log(VERIFY_LEVEL, message, args, **kwargs)

	def fetch(self, message, *args, **kwargs):
		if self.isEnabledFor(FETCH_LEVEL):
			self._log(FETCH_LEVEL, message, args, **kwargs)

	def day(self, message, *args, **kwargs):
		if self.isEnabledFor(DAY_LEVEL):
			self._log(DAY_LEVEL, message, args, **kwargs)

	def year(self, message, *args, **kwargs):
		if self.isEnabledFor(YEAR_LEVEL):
			self._log(YEAR_LEVEL, message, args, **kwargs)


logging.setLoggerClass(CustomLogger)


# 로깅
def setup_loggers(
	year: str = None,
	service_name: str = None,
	operation_name: str = None,
	target_start: str = None,
	target_end: str = None,
	bsns_div_cd: int = None,
):
	"""
	로거 설정 및 로그 디렉토리 생성

	Args:
		year: 수집 연도 (예: "2024")
		service_name: 서비스명 (예: "입찰공고정보서비스")
		operation_name: 오퍼레이션명 (예: "공사조회")
		target_start: 수집 시작일 (예: "2025-01-01")
		target_end: 수집 종료일 (예: "2025-12-14")
		bsns_div_cd: 사업구분코드 (1=물품, 2=외자, 3=공사, 5=용역)

	Returns:
		dict: {"loggers": {...}, "log_dir": str, "meta_path": str}
	"""
	# 현재 실행 중인 파일의 위치
	current_dir = os.path.dirname(os.path.abspath(__file__))
	project_root = os.path.dirname(current_dir)

	# logs/fetch 디렉토리 생성
	logs_dir = os.path.join(project_root, "logs", "fetch")
	os.makedirs(logs_dir, exist_ok=True)

	# 현재시각
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	run_start_iso = datetime.now().isoformat()

	# bsns_div_cd 매핑 (디렉토리명 생성용)
	bsns_div_map = {1: "물품", 2: "외자", 3: "공사", 5: "용역"}

	# 디렉토리명 생성: timestamp_서비스명_오퍼레이션명_사업구분_수집날짜
	dir_parts = [timestamp]
	if service_name:
		dir_parts.append(service_name)
	if operation_name:
		dir_parts.append(operation_name)
	if bsns_div_cd and bsns_div_cd in bsns_div_map:
		dir_parts.append(bsns_div_map[bsns_div_cd])
	if target_start and target_end:
		if target_start == target_end:
			dir_parts.append(target_start)
		else:
			dir_parts.append(f"{target_start}_to_{target_end}")
	elif year:
		dir_parts.append(f"YEAR{year}")
	dir_name = "_".join(dir_parts)

	time_dir = os.path.join(logs_dir, dir_name)
	os.makedirs(time_dir, exist_ok=True)

	# meta.json 생성
	meta = {
		"service_name": service_name,
		"operation_name": operation_name,
		"target_start": target_start,
		"target_end": target_end,
		"year": year,
		"bsns_div_cd": bsns_div_cd,
		"bsns_div_name": bsns_div_map.get(bsns_div_cd) if bsns_div_cd else None,
		"run_start": run_start_iso,
		"run_end": None,
		"status": "running",
		"records_total": 0,
		"records_inserted": 0,
		"records_updated": 0,
		"error_count": 0,
		"log_dir": time_dir,
	}
	meta_path = os.path.join(time_dir, "meta.json")
	with open(meta_path, "w", encoding="utf-8") as f:
		json.dump(meta, f, ensure_ascii=False, indent=2)

	# 기존 루트 로거 핸들러 제거 (이중 출력 방지)
	logging.getLogger().handlers.clear()

	log_files = {
		"application": os.path.join(time_dir, "application.log"),
		"error": os.path.join(time_dir, "error.log"),
		"day": os.path.join(time_dir, "day.log"),
		"year": os.path.join(time_dir, "year.log"),
	}

	# 기본 로그 포맷 설정
	log_format = "[%(levelname)s] %(asctime)s - %(message)s"
	date_format = "%Y-%m-%d %H:%M:%S"

	loggers = {}

	for name, log_file in log_files.items():
		logger = logging.getLogger(name)
		# Prevent duplicate logs when setup_loggers() is called again
		logger.handlers.clear()
		logger.propagate = False
		logger.setLevel(logging.DEBUG)  # 모든 레벨 허용

		# 파일 핸들러 추가
		file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
		file_formatter = logging.Formatter(log_format, datefmt=date_format)
		file_handler.setFormatter(file_formatter)
		logger.addHandler(file_handler)

		# 콘솔 로그 설정 (application logger에만 적용)
		# Airflow 환경에서는 colorlog가 충돌을 일으키므로 비활성화
		if name == "application" and not os.getenv("AIRFLOW_CTX_DAG_ID"):
			console_handler = colorlog.StreamHandler()
			console_formatter = colorlog.ColoredFormatter(
				"%(log_color)s[%(levelname)s] %(asctime)s - %(message)s",
				datefmt=date_format,
				log_colors={
					"VERIFY": "purple",
					"FETCH": "cyan",
					"DAY": "green",
					"YEAR": "yellow",
					"ERROR": "red",
					"CRITICAL": "bold_red"
				}
			)
			console_handler.setFormatter(console_formatter)
			logger.addHandler(console_handler)

		loggers[name] = logger

	return {
		"loggers": loggers,
		"log_dir": time_dir,
		"meta_path": meta_path,
	}


def setup_sync_loggers(
	table_name: str = None,
	schema: str = None,
	process_type: str = "sync",  # sync, postprocess
):
	"""
	동기화용 로거 설정 및 로그 디렉토리 생성

	Args:
		table_name: 테이블명 (예: "notice", "bid")
		schema: PostgreSQL 스키마명 (예: "data", "tmp")
		process_type: 프로세스 타입 ("sync", "postprocess")

	Returns:
		dict: {"loggers": {...}, "log_dir": str, "meta_path": str}
	"""
	# 현재 실행 중인 파일의 위치
	current_dir = os.path.dirname(os.path.abspath(__file__))
	project_root = os.path.dirname(current_dir)

	# logs/sync 디렉토리 생성
	logs_dir = os.path.join(project_root, "logs", process_type)
	os.makedirs(logs_dir, exist_ok=True)

	# 현재시각
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
	run_start_iso = datetime.now().isoformat()

	# 디렉토리명 생성: timestamp_schema_table
	dir_parts = [timestamp]
	if schema:
		dir_parts.append(schema)
	if table_name:
		dir_parts.append(table_name)
	dir_name = "_".join(dir_parts)

	time_dir = os.path.join(logs_dir, dir_name)
	os.makedirs(time_dir, exist_ok=True)

	# meta.json 생성
	meta = {
		"process_type": process_type,
		"table_name": table_name,
		"schema": schema,
		"run_start": run_start_iso,
		"run_end": None,
		"status": "running",
		"records_total": 0,
		"records_synced": 0,
		"records_skipped": 0,
		"error_count": 0,
		"log_dir": time_dir,
	}
	meta_path = os.path.join(time_dir, "meta.json")
	with open(meta_path, "w", encoding="utf-8") as f:
		json.dump(meta, f, ensure_ascii=False, indent=2)

	# 기존 루트 로거 핸들러 제거 (이중 출력 방지)
	# 주의: 전역 핸들러 제거는 다른 로거에 영향을 줄 수 있음
	# logging.getLogger().handlers.clear()

	log_files = {
		"application": os.path.join(time_dir, "application.log"),
		"error": os.path.join(time_dir, "error.log"),
		"batch": os.path.join(time_dir, "batch.log"),
	}

	# 기본 로그 포맷 설정
	log_format = "[%(levelname)s] %(asctime)s - %(message)s"
	date_format = "%Y-%m-%d %H:%M:%S"

	loggers = {}

	# 유니크한 로거 이름 생성 (중복 방지)
	logger_prefix = f"{process_type}_{table_name}_{timestamp}"

	for name, log_file in log_files.items():
		logger_name = f"{logger_prefix}_{name}"
		logger = logging.getLogger(logger_name)
		# Prevent duplicate logs when setup_sync_loggers() is called again
		logger.handlers.clear()
		logger.propagate = False
		logger.setLevel(logging.DEBUG)  # 모든 레벨 허용

		# 파일 핸들러 추가
		file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
		file_formatter = logging.Formatter(log_format, datefmt=date_format)
		file_handler.setFormatter(file_formatter)
		logger.addHandler(file_handler)

		# 콘솔 로그 설정 (application logger에만 적용)
		# Airflow 환경에서는 colorlog가 충돌을 일으키므로 비활성화
		if name == "application" and not os.getenv("AIRFLOW_CTX_DAG_ID"):
			console_handler = colorlog.StreamHandler()
			console_formatter = colorlog.ColoredFormatter(
				"%(log_color)s[%(levelname)s] %(asctime)s - %(message)s",
				datefmt=date_format,
				log_colors={
					"DEBUG": "white",
					"INFO": "green",
					"WARNING": "yellow",
					"ERROR": "red",
					"CRITICAL": "bold_red"
				}
			)
			console_handler.setFormatter(console_formatter)
			logger.addHandler(console_handler)

		loggers[name] = logger

	return {
		"loggers": loggers,
		"log_dir": time_dir,
		"meta_path": meta_path,
	}


def update_log_meta(meta_path: str, **updates):
	"""
	meta.json 파일 업데이트

	Args:
		meta_path: meta.json 파일 경로
		**updates: 업데이트할 필드들

	Example:
		update_log_meta(meta_path, status="success", records_total=100)
	"""
	if not os.path.exists(meta_path):
		return

	with open(meta_path, "r", encoding="utf-8") as f:
		meta = json.load(f)

	meta.update(updates)

	# run_end 자동 설정 (status가 success/failed로 변경될 때)
	if updates.get("status") in ("success", "failed") and not meta.get("run_end"):
		meta["run_end"] = datetime.now().isoformat()

	with open(meta_path, "w", encoding="utf-8") as f:
		json.dump(meta, f, ensure_ascii=False, indent=2)
