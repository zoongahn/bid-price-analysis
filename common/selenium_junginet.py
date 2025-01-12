import warnings

from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import Select
from .utils import *

# ignore FutureWarnings
warnings.simplefilter(action='ignore', category=FutureWarning)


class LoginConfig:
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


class ChromeOptionsManager:
	def __init__(self):
		self.options = webdriver.ChromeOptions()

	def add_heedless(self):
		self.options.add_argument('headless')
		return self

	def add_default_options(self):
		self.options.add_argument("no-sandbox")

		self.options.add_argument("window-size=1920x1080")

		self.options.add_argument("disable-gpu")  # 가속 사용 x
		self.options.add_argument("lang=ko_KR")  # 가짜 플러그인 탑재
		self.options.add_argument(
			'user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_12_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/61.0.3163.100 Safari/537.36')  # user-agent 이름 설정
		return self

	def get_options(self):
		return self.options


class WebDriverManager:
	def __init__(self, options: webdriver.ChromeOptions = None):
		service = ChromeService(executable_path=ChromeDriverManager().install())

		# 옵션을 설정한 후 드라이버 생성
		if options is None:
			options = ChromeOptionsManager().get_options()  # 기본 옵션을 가져오거나, 사용자 정의 옵션을 전달
		self.driver = webdriver.Chrome(options)

	def open_page(self, url: str):
		"""주어진 URL을 열기"""
		self.driver.get(url)

	def new_tab(self, url: str):
		self.driver.switch_to.new_window('tab')
		self.open_page(url)

	def close_tab(self, return_tab_number: int = 0):
		self.driver.close()
		self.driver.switch_to.window(self.driver.window_handles[return_tab_number])

	def login(self, username: str = LoginConfig.login_info["id"], password: str = LoginConfig.login_info["pw"]):
		self.driver.find_element(By.ID, "idInfo").send_keys(username)
		self.driver.find_element(By.ID, "pwInfo").send_keys(password)
		self.driver.find_element(By.ID, "login_btn").click()

	def manip_page(self, page_bid_total: int, search_year: int):
		# 낙찰정보 클릭
		self.driver.find_element(By.ID, "nbid_menu2").click()

		Select(self.driver.find_element(By.ID, "list_num_select")).select_by_value(str(page_bid_total))
		Select(self.driver.find_element(By.ID, "align_select")).select_by_value(str(search_year))
		list_max = self.driver.find_element(By.XPATH, "/html/body/div[5]/div/div[2]/table/tbody/tr[1]/td[1]/p").text

	def switch_page(self, page_num: int):
		if page_num != 1:
			# 페이지 번호 클릭
			self.driver.find_element(By.XPATH, f"/html/body/div[5]/div/div[4]/div/a[{page_num}]").send_keys("\n")

	def find_element_by_xpath(self, xpath: str):
		return self.driver.find_element(By.XPATH, xpath)

	def find_elements_by_css(self, css_selector: str):
		return self.driver.find_elements(By.CSS_SELECTOR, css_selector)

	def find_elements_by_xpath(self, xpath: str):
		return self.driver.find_elements(By.XPATH, xpath)

	# 참여업체수가 기준치 초과면 참여업체수를, 그렇지않으면 -1 리턴
	def check_prtcptCnum(self, row, criterion) -> int:
		# 참여업체수 확인
		prtcptCnum = int(price_converter(
			self.find_element_by_xpath(f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[13]/div").text))

		return prtcptCnum if prtcptCnum > criterion else -1

	def get_driver(self):
		return self.driver

	def quit(self):
		self.driver.quit()
