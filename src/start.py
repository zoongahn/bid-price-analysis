from bs4 import BeautifulSoup
import requests

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

import time
import pandas as pd
from math import ceil
import warnings
import os


def to_int(s):
	f = s.find("/")
	if f != -1:
		s = s[:f].strip()
	return int(s.replace(",", ""))


def extract_table():
	df = pd.DataFrame()
	max_page = prtcptCnum // 50

	try:
		# 1st page's table
		table = WebDriverWait(driver, 10).until(
			EC.presence_of_element_located((By.XPATH, "//*[@id=\"company_list\"]/div[2]/table"))
		)
		html = table.get_attribute("outerHTML")
		df = pd.concat([df, pd.read_html(html)[0]])

		sequence = list(range(2, 12))  # 처음에 2~11
		while len(sequence) < max_page:
			sequence += list(range(3, 13))  # 이후에 3~12 추가
		
		for i in sequence[:max_page]:
			# 다음 페이지로
			next_page = WebDriverWait(driver, 10).until(
				EC.element_to_be_clickable((By.XPATH, f"/html/body/main/div/div/div[3]/div/div/a[{i}]"))
			)
			next_page.send_keys("\n")
			time.sleep(1)  # Give time for table to load

			# current page's table
			table = WebDriverWait(driver, 10).until(
				EC.presence_of_element_located((By.XPATH, "//*[@id=\"company_list\"]/div[2]/table"))
			)
			html = table.get_attribute("outerHTML")
			df = pd.concat([df, pd.read_html(html)[0]])

		# Create output directory if it doesn't exist
		os.makedirs("../output", exist_ok=True)
		df.to_csv(f"../output/{code}.csv", index=False)
		
	except Exception as e:
		print(f"Error extracting table: {str(e)}")


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

try:
	service = ChromeService(executable_path=ChromeDriverManager().install())
	options = webdriver.ChromeOptions()
	options.add_argument("no-sandbox")
	options.add_argument("window-size=1920x1080")
	options.add_argument("disable-gpu")
	options.add_argument("lang=ko_KR")
	options.add_argument(
		'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')

	driver = webdriver.Chrome(service=service, options=options)
	wait = WebDriverWait(driver, 10)

	driver.get(url)

	# 로그인
	wait.until(EC.presence_of_element_located((By.ID, "idInfo"))).send_keys(login_info["id"])
	wait.until(EC.presence_of_element_located((By.ID, "pwInfo"))).send_keys(login_info["pw"])
	wait.until(EC.element_to_be_clickable((By.ID, "login_btn"))).click()

	# 낙찰정보 클릭
	wait.until(EC.element_to_be_clickable((By.ID, "nbid_menu2"))).click()

	# 500개씩, 특정년도로
	info_count = 500
	Select(wait.until(EC.presence_of_element_located((By.ID, "list_num_select")))).select_by_value(str(info_count))
	Select(wait.until(EC.presence_of_element_located((By.ID, "align_select")))).select_by_value("2024")
	list_max = wait.until(EC.presence_of_element_located((By.XPATH, "/html/body/div[5]/div/div[2]/table/tbody/tr[1]/td[1]/p"))).text

	criterion = 10
	for column in range(1, info_count + 1):
		try:
			prtcptCnum = to_int(
				wait.until(EC.presence_of_element_located((By.XPATH, f"/html/body/div[5]/div/div[2]/table/tbody/tr[{column}]/td[13]/div"))).text
			)

			# 참여업체수가 기준보다 낮으면 패스
			if prtcptCnum < criterion:
				continue

			# 오픈할 공고의 링크
			link = wait.until(EC.presence_of_element_located((By.XPATH,
				f"/html/body/div[5]/div/div[2]/table/tbody/tr[{column}]/td[2]/a"))).get_attribute("href")
			
			# 새탭 오픈
			driver.switch_to.new_window('tab')
			driver.get(link)
			
			# 공고번호 저장(aka csv파일 이름)
			x = wait.until(EC.presence_of_element_located((By.XPATH, "//*[@id=\"content1\"]/div[3]/div[1]/div/table/tbody/tr[1]/td"))).text
			code = x[:x.find(" ")]

			extract_table()

			driver.close()
			driver.switch_to.window(driver.window_handles[-1])
			time.sleep(1)
			
		except Exception as e:
			print(f"Error processing column {column}: {str(e)}")
			continue

except Exception as e:
	print(f"Fatal error: {str(e)}")
finally:
	if 'driver' in locals():
		driver.quit()
