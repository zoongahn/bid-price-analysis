import os
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
def setup_loggers(year: str = None):
	# 현재 실행 중인 파일(src/main.py)의 위치
	current_dir = os.path.dirname(os.path.abspath(__file__))  # src/

	# 프로젝트 루트(api-fetcher/) 찾기 (src/의 상위 폴더)
	project_root = os.path.dirname(current_dir)  # api-fetcher/

	# logs 디렉토리 생성 (없으면 자동 생성)
	logs_dir = os.path.join(project_root, "logs")
	os.makedirs(logs_dir, exist_ok=True)  # logs 폴더 생성

	# 현재시각을 기준으로 log/ 에 디렉토리생성
	timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

	if year:
		dir_name = f"{timestamp}_YEAR{year}"
	else:
		dir_name = timestamp

	time_dir = os.path.join(logs_dir, dir_name)
	os.makedirs(time_dir, exist_ok=True)

	# 기존 루트 로거 핸들러 제거 (이중 출력 방지)
	logging.getLogger().handlers.clear()

	log_files = {
		"application": os.path.join(time_dir, f"application_{dir_name}.log"),
		"error": os.path.join(time_dir, f"error_{dir_name}.log"),
		"day": os.path.join(time_dir, f"day_{dir_name}.log"),
		"year": os.path.join(time_dir, f"year_{dir_name}.log"),
	}

	# 기본 로그 포맷 설정
	log_format = "[%(levelname)s] %(asctime)s - %(message)s"
	date_format = "%Y-%m-%d %H:%M:%S"

	loggers = {}

	for name, log_file in log_files.items():
		logger = logging.getLogger(name)
		logger.setLevel(logging.DEBUG)  # 모든 레벨 허용

		# 파일 핸들러 추가
		file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
		file_formatter = logging.Formatter(log_format, datefmt=date_format)
		file_handler.setFormatter(file_formatter)
		logger.addHandler(file_handler)

		# 콘솔 로그 설정 (colorlog 사용, application logger에만 적용)
		if name == "application":
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

	return loggers
