import functools

from common.selenium_junginet import *
from extract import scrap
import pandas as pd

url = "https://www.jungi.net/login"
PAGE_BID_TOTAL = 500

driver = WebDriverManager(options=ChromeOptionsManager().add_default_options().add_heedless().get_options())


def print_status(func):
	@functools.wraps(func)
	def wrapper(*args, **kwargs):
		print(f"Function {func.__name__} with args={args}, kwargs={kwargs} STARTED.")
		func(*args, **kwargs)
		print(f"Function {func.__name__} with args={args}, kwargs={kwargs} FINISHED.")

	return wrapper


@print_status
def get_data_by_page(page_num: int, row_amount: int, dir_path: str):
	driver.switch_page(page_num)

	start_row = 1
	end_row = row_amount

	for row in range(start_row, end_row + 1):
		# 함수 내부에서 csv파일까지 export함에 주의
		try:
			scrap(driver, dir_path, criterion=10, row=row)
		except:
			print("UNKNOWN ERROR")
			driver.close_tab()
			bid_code = driver.find_element_by_xpath(
				f"/html/body/div[5]/div/div[2]/table/tbody/tr[{row}]/td[2]/label").text[1:-1]
			add_exception(bid_code)


@print_status
def get_data_by_year(year: int):
	driver.manip_page(PAGE_BID_TOTAL, search_year=year)

	dir_path = f"../../output/공고별_기업_투찰정보_년도별/공고별_기업_투찰정보_{year}"

	# 해당 경로로 폴더 생성
	create_folder_if_not_exists(dir_path)

	# max_page = len(driver.find_elements_by_xpath("/html/body/div[5]/div/div[4]/div/a"))
	end_row = int(driver.find_element_by_xpath("/html/body/div[5]/div/div[2]/table/tbody/tr[1]/td[1]/p").text)
	row_amount_by_page = split_into_chunks_n(end_row, PAGE_BID_TOTAL)

	for page in range(1, len(row_amount_by_page) + 1):
		get_data_by_page(page, row_amount_by_page[page - 1], dir_path)


@print_status
def main():
	try:
		driver.open_page(url)
		driver.login()

		for year in range(2015, 2013, -1):
			get_data_by_year(year)

	finally:
		driver.quit()


if __name__ == "__main__":
	main()
