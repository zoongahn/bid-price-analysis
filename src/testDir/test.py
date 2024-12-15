from bs4 import BeautifulSoup
import requests

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
import time
import pandas as pd
from math import ceil
import warnings


def to_int(s):
	f = s.find("/")
	if f != -1:
		s = s[:f].strip()
	return int(s.replace(",", ""))


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
# 팝업 차단 해제
options.add_argument('--disable-popup-blocking')

driver = webdriver.Chrome(service=service, options=options)

driver.get(url)

# 로그인
driver.find_element(By.ID, "idInfo").send_keys(login_info["id"])
driver.find_element(By.ID, "pwInfo").send_keys(login_info["pw"])
driver.find_element(By.ID, "login_btn").click()

# 낙찰정보 클릭
driver.find_element(By.ID, "nbid_menu2").click()

column = 3
criterion = 10
prtcptCnum = to_int(
	driver.find_element(By.XPATH, f"/html/body/div[5]/div/div[2]/table/tbody/tr[{column}]/td[13]/div").text)
if prtcptCnum > criterion:
	# 열 공고의 링크
	link = driver.find_element(By.XPATH,
	                           f"/html/body/div[5]/div/div[2]/table/tbody/tr[{column}]/td[2]/a").get_attribute("href")
	driver.switch_to.new_window('tab')
	driver.get(link)

	# get_table()
	driver.close()

	time.sleep(100)
