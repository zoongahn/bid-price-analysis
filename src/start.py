from bs4 import BeautifulSoup
import requests

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import time
import pandas as pd
from math import ceil
import warnings


def to_int(s):
	f = s.find("/")
	if f != -1:
		s = s[:f].strip()
	return int(s.replace(",", ""))


def extract_table():
	df = pd.DataFrame()
	max_page = prtcptCnum // 50

	# 1st page's table
	html = driver.find_element(By.XPATH, "//*[@id=\"company_list\"]/div[2]/table").get_attribute("outerHTML")
	df = pd.concat([df, pd.read_html(html)[0]])

	sequence = list(range(2, 12))  # 처음에 2~11
	while len(sequence) < max_page:
		sequence += list(range(3, 13))  # 이후에 3~12 추가
	for i in sequence[:max_page]:
		# 다음 페이지로
		driver.find_element(By.XPATH, f"/html/body/main/div/div/div[3]/div/div/a[{i}]").send_keys("\n")

		# current page's table
		html = driver.find_element(By.XPATH, "//*[@id=\"company_list\"]/div[2]/table").get_attribute("outerHTML")
		df = pd.concat([df, pd.read_html(html)[0]])

	df.to_csv(f"../output/{code}.csv")


# ignore FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)

login_info = {
	"status": "login",
	"url2": "common",
	"url": "",
	"login_page_value": "1",
	"go_page": "",
	"id": "bitn0415",
	"pw": "87732"
}

login_headers = {
	"Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
	"Accept-Encoding": "gzip, deflate, br, zstd",
	"Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
	"User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36"
}

url = "https://www.jungi.net"
list_url = "https://www.jungi.net/nbid?part=42&local=20&list_num=100&align=2024&pageNum"
login_url = "https://www.jungi.net/login"

service = ChromeService(executable_path=ChromeDriverManager().install())

options = webdriver.ChromeOptions()

# options.add_argument('headless')
options.add_argument("no-sandbox")

options.add_argument("window-size=1920x1080")

options.add_argument("disable-gpu")  # 가속 사용 x
options.add_argument("lang=ko_KR")  # 가짜 플러그인 탑재
options.add_argument(
	'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')  # user-agent 이름 설정

driver = webdriver.Chrome(service=service, options=options)

driver.get(url)

# 로그인
driver.find_element(By.ID, "idInfo").send_keys(login_info["id"])
driver.find_element(By.ID, "pwInfo").send_keys(login_info["pw"])
driver.find_element(By.ID, "login_btn").click()

# 낙찰정보 클릭
driver.find_element(By.ID, "nbid_menu2").click()

# 500개씩, 특정년도로
info_count = 500
Select(driver.find_element(By.ID, "list_num_select")).select_by_value(str(info_count))
Select(driver.find_element(By.ID, "align_select")).select_by_value("2024")
list_max = driver.find_element(By.XPATH, "/html/body/div[5]/div/div[2]/table/tbody/tr[1]/td[1]/p").text

criterion = 10
for column in range(1, info_count + 1):

	prtcptCnum = to_int(
		driver.find_element(By.XPATH, f"/html/body/div[5]/div/div[2]/table/tbody/tr[{column}]/td[13]/div").text)

	# 참여업체수가 기준보다 낮으면 패스
	if prtcptCnum < criterion:
		continue

	# 오픈할 공고의 링크
	link = driver.find_element(By.XPATH,
	                           f"/html/body/div[5]/div/div[2]/table/tbody/tr[{column}]/td[2]/a").get_attribute("href")
	# 새탭 오픈
	driver.switch_to.new_window('tab')
	driver.get(link)

	# 공고번호 저장(aka csv파일 이름)
	x = driver.find_element(By.XPATH, "//*[@id=\"content1\"]/div[3]/div[1]/div/table/tbody/tr[1]/td").text
	code = x[:x.find(" ")]

	extract_table()

	driver.close()
	driver.switch_to.window(driver.window_handles[-1])
	time.sleep(1)
