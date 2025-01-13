from typing import Tuple, Union

from pandas import DataFrame

from common.selenium_junginet import WebDriverManager
from common.utils import *
import pandas as pd


def find_file_in_folder(file_name: str, folder_path: str) -> Union[str, None]:
	"""
	지정된 폴더 내에서 특정 파일을 탐색합니다 (하위 폴더는 제외).

	param file_name: 찾고자 하는 파일명
	param folder_path: 탐색할 폴더 경로
	"""
	for item in os.listdir(folder_path):
		item_path = os.path.join(folder_path, item)
		if os.path.isfile(item_path) and item == file_name:
			return item_path  # 파일 경로 반환
	return None  # 파일을 찾지 못한 경우


def extract_table(driver: WebDriverManager, prtcptCnum: int) -> DataFrame:
	df = pd.DataFrame()

	max_page = (prtcptCnum - 1) // 50

	# 1st page's table
	html = driver.find_element_by_xpath("//*[@id=\"company_list\"]/div[2]/table").get_attribute("outerHTML")
	df = pd.concat([df, pd.read_html(html)[0]])

	sequence = list(range(2, 12))  # 처음에 2~11
	while len(sequence) < max_page:
		sequence += list(range(3, 13))  # 이후에 3~12 추가
	for i in sequence[:max_page]:
		# 다음 페이지로
		driver.find_element_by_xpath(f"/html/body/main/div/div/div[3]/div/div/a[{i}]").send_keys("\n")

		# current page's table
		html = driver.find_element_by_xpath("//*[@id=\"company_list\"]/div[2]/table").get_attribute("outerHTML")
		df = pd.concat([df, pd.read_html(html)[0]])

	return df


def scrap(driver: WebDriverManager, dir_path: str, criterion: int, row: int) -> None:
	prtcptCnum = driver.check_prtcptCnum(row, criterion)
	bid_code = driver.find_element_by_xpath(f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[2]/label").text[
	           1:-1]

	print(f"[공고번호:{bid_code} / row={row} / 참여업체수={prtcptCnum}] PROCESSING --- ", end="")

	if prtcptCnum == -1:
		print("PASS")
		return

	# "/"는 파일명에 존재하면 X
	if bid_code.find("/") != -1:
		print("INVALID FILE NAME")
		return

	# 이미 해당 폴더에 다운받은 csv파일이 있는지 확인
	if find_file_in_folder(f"{bid_code}.csv", dir_path) is not None:
		print("EXISTING")
		return

	# 오픈할 공고의 링크
	link = driver.find_element_by_xpath(
		f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[2]/a").get_attribute("href")

	# 새탭 오픈
	driver.new_tab(link)

	result = extract_table(driver, prtcptCnum)

	result.to_csv(f"{dir_path}/{bid_code}.csv", index=False, encoding="utf-8-sig")

	driver.close_tab()

	# 다운로드 로그
	print(f"COMPLETE")
