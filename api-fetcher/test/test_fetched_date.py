import os
import pytest
from src.utils import load_fetched_date, save_fetched_date

# ✅ 테스트용 디렉토리 및 파일 설정
TEST_DIR = os.path.join(os.path.dirname(__file__), "test_date_record")
FETCHED_FILE = os.path.join(TEST_DIR, "fetched_date.txt")
ERROR_FILE = os.path.join(TEST_DIR, "error_date.txt")


@pytest.fixture(scope="function", autouse=True)
def setup_test_dir():
	""" 테스트 시작 전, 디렉토리 및 파일 초기화 """
	os.makedirs(TEST_DIR, exist_ok=True)

	# 테스트 시작 전 기존 파일 삭제
	for file in [FETCHED_FILE, ERROR_FILE]:
		if os.path.exists(file):
			os.remove(file)

	yield  # 테스트 실행

	# 테스트 종료 후 정리
	for file in [FETCHED_FILE, ERROR_FILE]:
		if os.path.exists(file):
			os.remove(file)


def test_load_fetched_date_empty():
	""" 파일이 없을 때 빈 set 반환 확인 """
	assert load_fetched_date(FETCHED_FILE) == set()
	assert load_fetched_date(ERROR_FILE) == set()


def test_save_fetched_date():
	""" 날짜 저장 및 로드 확인 """
	save_fetched_date("2025-02-19")  # 기본 파일에 저장
	save_fetched_date("2025-02-20")
	save_fetched_date("2025-02-21", error=True)  # 에러 파일에 저장

	# 데이터 로드
	fetched_dates = load_fetched_date(FETCHED_FILE)
	error_dates = load_fetched_date(ERROR_FILE)

	assert fetched_dates == {"2025-02-19", "2025-02-20"}
	assert error_dates == {"2025-02-21"}


def test_save_fetched_date_append():
	""" 여러 번 실행했을 때 데이터가 덮어쓰이지 않고 추가되는지 확인 """
	save_fetched_date("2025-02-19")
	save_fetched_date("2025-02-20")
	save_fetched_date("2025-02-21", error=True)

	save_fetched_date("2025-02-22")
	save_fetched_date("2025-02-23", error=True)

	fetched_dates = load_fetched_date(FETCHED_FILE)
	error_dates = load_fetched_date(ERROR_FILE)

	assert fetched_dates == {"2025-02-19", "2025-02-20", "2025-02-22"}
	assert error_dates == {"2025-02-21", "2025-02-23"}
