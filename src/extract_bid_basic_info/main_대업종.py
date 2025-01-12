import csv

from selenium import webdriver
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select

import time
import warnings

from common.utils import to_int

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
year = "2014"
page_num = 2
Select(driver.find_element(By.ID, "list_num_select")).select_by_value(str(info_count))
Select(driver.find_element(By.ID, "align_select")).select_by_value(year)
list_max = driver.find_element(By.XPATH, "/html/body/div[5]/div/div[2]/table/tbody/tr[1]/td[1]/p").text

# driver.find_element(By.XPATH, f"/html/body/div[5]/div/div[4]/div/a[{page_num}]").send_keys("\n")

RESULT_FILE_PATH = f"../../output/공고_기본_정보/original/공고기본정보_{year}_서울_통신_original.csv"

f = open(RESULT_FILE_PATH, "a", newline="")
wr = csv.writer(f)

attrs = ["id", "공고번호", "공고제목", "발주처(수요기관)", "지역제한", "기초금액", "예정가격", "예가범위", "A값", "투찰률(%)", "참여업체수", "공고구분표시",
         "정답사정률(%)"]

row = 179
data_row_counter = 170

result = {
	"id": "", "공고번호": "", "공고제목": "", "발주처": "", "지역제한": "", "기초금액": "", "예정가격": "", "예가범위": "", "A값": "0",
	"투찰률": "", "참여업체수": "", "공고구분표시": "", "정답사정률": ""
}

prtcptCnum = to_int(
	driver.find_element(By.XPATH, f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[13]/div").text)

result["참여업체수"] = str(prtcptCnum)

result["예가범위"] = driver.find_element(By.XPATH,
                                     f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[16]/div").text

# 오픈할 공고의 링크
link = driver.find_element(By.XPATH,
                           f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[2]/a").get_attribute("href")

# 새탭 오픈
driver.switch_to.new_window('tab')
driver.get(link)

bid_infos = driver.find_elements(By.CSS_SELECTOR,
                                 "#content1 > div:nth-child(4) > div:nth-child(1) > div > table > tbody > tr > td")

for i in range(len(bid_infos)):
	print(i, bid_infos[i].text)

result["id"] = data_row_counter
result["공고번호"] = bid_infos[0].text.split(" ")[0]
result["발주처"] = bid_infos[3].text.split(" ")[0]
result["지역제한"] = bid_infos[4].text
result["기초금액"] = str(to_int(bid_infos[6].text))
result["예정가격"] = str(to_int(bid_infos[8].text))
result["투찰률"] = bid_infos[7].text.replace("%", "")
result["정답사정률"] = bid_infos[9].text.split("%")[0]

bid_marks = [i.text for i in driver.find_elements(By.XPATH,
                                                  "//*[@id=\"content1\"]/div[2]/table/tbody/tr/td/a/label")]

except_str = " ".join(bid_marks)

bid_title = driver.find_element(By.XPATH, "//*[@id=\"content1\"]/div[2]/table/tbody/tr/td/a").text.replace(
	except_str,
	"").strip()

result["공고제목"] = bid_title
result["공고구분표시"] = "/".join(bid_marks)

if "A값" in bid_marks:
	result["A값"] = str(to_int(bid_infos[10].text))

wr.writerow(result.values())
data_row_counter += 1

driver.close()
driver.switch_to.window(driver.window_handles[-1])
time.sleep(1)

f.close()
