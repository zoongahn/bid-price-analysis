import os


def float_to_int(flt):
	return int(flt) if flt.isdecimal() else int(float(flt))


def price_converter(s):
	f = s.find("/")
	if f != -1:
		s = s[:f].strip()

	s = s.replace("원", "").replace(",", "")

	try:
		i = int(s)
	except:
		i = float(s)

	return str(i)


def create_folder_if_not_exists(dir_path):
	"""
	parent_path 경로 안에 folder_name 폴더가 있는지 확인 후,
	없으면 새 폴더를 생성한다.
	"""
	# parent_path와 folder_name을 합쳐서 절대 경로를 생성
	target_folder = os.path.join(dir_path)

	# 해당 경로가 존재하지 않으면 디렉터리 생성
	if not os.path.exists(target_folder):
		os.makedirs(target_folder)
		print(f"폴더 생성 완료: {target_folder}")
	else:
		print(f"이미 존재하는 폴더: {target_folder}")


def split_into_chunks_n(total: int, n: int) -> list[int]:
	"""
	'total' 값을 n=500 단위로 나누어 리스트를 반환하는 예시.
	예: total=1240 -> [500, 500, 240]
		total=1824 -> [500, 500, 500, 324]
	"""
	a = total // n  # n으로 나눈 몫
	remainder = total % n  # 나머지
	chunks = [n] * a  # 몫 개수만큼 n을 넣음

	if remainder != 0:
		chunks.append(remainder)

	return chunks


def add_exception(bid_code: str, file_path: str = "../../output/공고별_기업_투찰정보_년도별/exception_list.txt", mode: str = "a"):
	with open(file_path, mode, encoding="utf-8") as file:
		file.write(f"{bid_code}\n")


def search_text_exactly_in_file(target_text: str, file_path: str = "../../output/공고별_기업_투찰정보_년도별/exception_list.txt",
                                ) -> bool:
	"""
	파일에서 특정 텍스트와 완전히 일치하는 줄이 있는지 확인하는 함수.

	Args:
		file_path (str): 검색할 파일 경로
		target_text (str): 검색할 텍스트

	Returns:
		bool: 완전히 일치하는 줄이 있으면 True, 없으면 False
	"""
	try:
		with open(file_path, "r", encoding="utf-8") as file:
			for line in file:
				# 줄 끝의 개행 문자를 제거한 뒤 비교
				if line.strip() == target_text:
					return True
		return False
	except FileNotFoundError:
		print(f"Error: File '{file_path}' not found.")
		return False
