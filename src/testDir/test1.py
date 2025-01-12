from common.selenium_junginet import *
from extract import scrap
import pandas as pd

url = "https://www.jungi.net"


def main():
	driver = WebDriverManager(options=ChromeOptionsManager().add_default_options().get_options())

	attrs = ["id", "공고번호", "공고제목", "발주처(수요기관)", "지역제한", "기초금액", "예정가격", "예가범위", "A값", "투찰률(%)", "참여업체수", "공고구분표시",
	         "정답사정률(%)"]
	df = pd.DataFrame(columns=attrs)

	start_row = 1
	end_row = 5
	year = 2023

	page_num = 1

	dir_path = f"../../output/공고_기본_정보/년도별/공고별_기업_투찰정보_{year}"

	try:
		driver.open_page(url)
		driver.login()
		driver.manip_page(500, search_year=year)
		driver.switch_page(page_num)

		print(driver.find_element_by_xpath("/html/body/div[5]/div/div[2]/table/tbody/tr[1]/td[2]/label"))

	finally:
		driver.quit()


if __name__ == "__main__":
	main()
