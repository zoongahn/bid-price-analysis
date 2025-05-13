from common.utils import *


# ---------------------------------------------------------------------------
# Record writer
# ---------------------------------------------------------------------------
class RecordWriter:
	"""Append processed ids/dates to text files under fetch_record/"""

	def __init__(self, collection_name: str):
		self.root = os.path.join(get_project_root(), "fetch_record", collection_name)
		os.makedirs(self.root, exist_ok=True)

	def append(self, text: str, filename: str):
		with open(os.path.join(self.root, filename), "a", encoding="utf-8") as fh:
			fh.write(text + "\n")
