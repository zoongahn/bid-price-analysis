from typing import Union

from common.selenium_junginet import WebDriverManager
from common.utils import *


def get_bid_details(driver: WebDriverManager, row: int) -> dict:
	"""주어진 행(row)에서 입찰 정보를 추출"""
	bid_details = {}
	bid_details["link"] = driver.find_element_by_xpath(
		f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[2]/a").get_attribute(
		"href")
	bid_details["participants"] = int(price_converter(
		driver.find_element_by_xpath("/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[13]/div").text))
	return bid_details


def scrap(driver: WebDriverManager, attrs: list, criterion: int, row: int) -> Union[dict, None]:
	result = {key: "" for key in attrs}

	prtcptCnum = driver.check_prtcptCnum(row, criterion)
	if prtcptCnum == -1:
		print("PASS")
		return

	result["참여업체수"] = str(prtcptCnum)
	result["예가범위"] = driver.find_element_by_xpath(
		f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[16]/div").text

	# 오픈할 공고의 링크
	link = driver.find_element_by_xpath(
		f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[2]/a").get_attribute("href")

	# 새탭 오픈
	driver.new_tab(link)

	bid_infos = driver.find_elements_by_css(
		"#content1 > div:nth-child(4) > div:nth-child(1) > div > table > tbody > tr > td")
	result.update({
		"공고번호": bid_infos[0].text.split(" ")[0],
		"발주처": bid_infos[2].text.split(" ")[0],
		"지역제한": bid_infos[3].text,
		"기초금액": price_converter(bid_infos[5].text),
		"예정가격": price_converter(bid_infos[7].text),
		"투찰률": bid_infos[6].text.replace("%", ""),
		"정답사정률": bid_infos[8].text.split("%")[0]
	})

	# 공고 구분 표시
	bid_marks = [i.text for i in driver.find_elements_by_xpath(
		"//*[@id=\"content1\"]/div[2]/table/tbody/tr/td/a/label")]
	except_str = " ".join(bid_marks)
	result["공고구분표시"] = "/".join(bid_marks)

	# 공고 제목
	bid_title = driver.find_element_by_xpath("//*[@id=\"content1\"]/div[2]/table/tbody/tr/td/a").text.replace(
		except_str, "").strip()
	result["공고제목"] = bid_title

	# A값
	if "A값" in bid_marks:
		result["A값"] = str(price_converter(bid_infos[9].text))

	driver.close_tab()

	return result
