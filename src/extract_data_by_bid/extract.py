from typing import Tuple

from pandas import DataFrame

from common.selenium_junginet import WebDriverManager
from common.utils import *
import pandas as pd


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
