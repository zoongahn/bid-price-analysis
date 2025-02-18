import logging
import colorlog
import os


def setup_logger(log_file="application.log", log_level=logging.INFO):
	# 기존 root logger의 핸들러 제거 (중복 방지)
	logging.getLogger().handlers = []

	# 1) 콘솔 로그 설정 (colorlog 사용)
	log_format_console = "%(log_color)s[%(levelname)s] %(asctime)s - %(message)s"
	console_handler = colorlog.StreamHandler()
	console_formatter = colorlog.ColoredFormatter(
		log_format_console,
		datefmt="%Y-%m-%d %H:%M:%S",
		log_colors={
			"DEBUG": "cyan",
			"INFO": "green",
			"WARNING": "yellow",
			"ERROR": "red",
			"CRITICAL": "bold_red"
		}
	)
	console_handler.setFormatter(console_formatter)
	console_handler.setLevel(log_level)

	# 2) 파일 로그 설정 (일반 텍스트로 저장)
	log_format_file = "[%(levelname)s] %(asctime)s - %(message)s"
	file_handler = logging.FileHandler(log_file, mode="a", encoding="utf-8")
	file_formatter = logging.Formatter(log_format_file, datefmt="%Y-%m-%d %H:%M:%S")
	file_handler.setFormatter(file_formatter)
	file_handler.setLevel(log_level)

	# 3) 루트 로거에 두 개의 핸들러(콘솔, 파일)를 연결
	logging.getLogger().setLevel(log_level)
	logging.getLogger().addHandler(console_handler)
	logging.getLogger().addHandler(file_handler)

	# 테스트 로그
	logging.info("Logger initialized: console + file")


if __name__ == "__main__":
	setup_logger()
	logging.info("안녕하세요! 터미널엔 컬러로, 파일엔 텍스트로 기록됩니다.")
	logging.warning("경고 레벨 로그")
	logging.error("에러 레벨 로그")
