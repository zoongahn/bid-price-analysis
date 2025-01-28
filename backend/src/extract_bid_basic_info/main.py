from common.selenium_junginet import *
from extract import *
import pandas as pd

url = "https://www.jungi.net"
file_path = f"../../output/공고_기본_정보"


def main():
	driver = WebDriverManager(options=ChromeOptionsManager().add_default_options().get_options())

	attrs = ["id", "공고번호", "공고제목", "발주처(수요기관)", "지역제한", "기초금액", "예정가격", "예가범위", "A값", "투찰률(%)", "참여업체수", "공고구분표시",
	         "정답사정률(%)"]
	df = pd.DataFrame(columns=attrs)

	start_row = 1
	end_row = 5
	year = 2024

	page_num = 1

	try:
		driver.open_page(url)
		driver.login()
		driver.manip_page(500, search_year=year)
		driver.switch_page(page_num)

		for row in range(start_row, end_row + 1):
			result = scrap(driver, attrs, criterion=10, row=row)
			if result:
				df = pd.concat([df, pd.DataFrame([result])], ignore_index=True)

	finally:
		driver.quit()

	df.to_csv(file_path, index=False, encoding="utf-8-sig")
	print("csv저장완료")


if __name__ == "__main__":
	main()
