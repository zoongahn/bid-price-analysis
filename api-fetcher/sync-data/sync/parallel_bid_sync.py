from multiprocessing import Process, Value
from pymongo import MongoClient
from bson import ObjectId
from tqdm import tqdm
import time

from sync import DataSync
from common.init_mongodb import init_mongodb
from common.init_psql import init_psql


def _run_worker(batch_size, notice_keys, query, start_id, end_id, progress_counter):
	syncer = DataSync(batch_size)
	syncer.notice_keys = notice_keys
	syncer.query = query
	syncer.sync_mongo_to_postgres(
		mongo_collection=syncer.mongo_bid,
		psql_table="bid",
		psql_pk=("bidntceno", "bidntceord", "bidprccorpbizrno"),
		preprocess=syncer.preprocess_bid,
		start_id=start_id,
		end_id=end_id,
		progress_counter=progress_counter
	)


class ParallelBidSync:
	def __init__(self, num_workers, batch_size):
		self.num_workers = num_workers
		self.syncer = DataSync(batch_size)
		self.mongo_bid = self.syncer.mongo_bid
		psql_server, psql_conn = init_psql()
		psql_conn.autocommit = True
		psql_cur = psql_conn.cursor()
		psql_cur.execute("SELECT bidntceno, bidntceord FROM notice;")
		# DataSync 인스턴스 내부에 notice_keys 생성
		self.syncer.notice_keys = psql_cur.fetchall()

		self.query = {"is_synced": {"$ne": True}}
		self.total_docs = self.mongo_bid.count_documents(self.query)

	def _log(self, message: str):
		print(f"[ParallelBidSync] {message}")

	def get_split_points(self) -> list[ObjectId]:

		# 1) 전체 문서 수
		total = self.total_docs
		num = self.num_workers
		step = total // num

		# 2) split points
		ids = []
		for i in range(num):
			skip = i * step
			# skip가 크면 느릴 수 있지만, limit(1)만 읽으므로 full scan보단 낫습니다
			doc = self.mongo_bid.find(self.query, {"_id": 1}) \
				.sort("_id", 1) \
				.skip(skip) \
				.limit(1) \
				.next()
			ids.append(doc["_id"])
		# sentinel
		ids.append(ObjectId())
		return ids

	def run(self, split_point_ids: list[str] | None = None):
		"""
		split_point_ids:
		  - None: 내부 get_split_points() 호출
		  - List[str]: ObjectId로 변환하여 직접 사용
		"""

		# 1) split points 결정
		if split_point_ids:
			points = [ObjectId(s) for s in split_point_ids]
		else:
			self._log("No split_point_ids provided, computing with get_split_points()")
			points = self.get_split_points()

		points.append(ObjectId())

		# 2) 공유 카운터 및 프로세스 리스트 준비
		self._log("Step 2: spawning worker processes")
		progress_counter = Value("i", 0)
		processes = []

		# 3) 워커 스폰
		for i in range(self.num_workers):
			self._log(f"  -> Worker {i + 1}/{self.num_workers}: range {points[i]}…{points[i + 1]}")
			start_id, end_id = points[i], points[i + 1]
			p = Process(
				target=_run_worker,
				args=(
					self.syncer.batch_size,
					self.syncer.notice_keys,
					self.query,
					start_id,
					end_id,
					progress_counter,
				)
			)
			p.start()
			processes.append(p)

		# 모니터링: 전체 배치 수 계산 및 tqdm 표시
		self._log("Workers started; entering monitoring phase")
		pbar = tqdm(total=self.total_docs, desc="전체 문서 진행")
		self._log("Step 3: monitoring progress")
		prev = 0
		try:
			while any(p.is_alive() for p in processes):
				time.sleep(0.5)
				curr = progress_counter.value
				pbar.update(curr - prev)
				prev = curr
		finally:
			self._log("Finalizing: closing progress bar and joining workers")
			# 최종 업데이트
			curr = progress_counter.value
			pbar.update(curr - prev)
			pbar.close()
			for p in processes:
				p.join()


def get_cpu_count():
	import multiprocessing
	return multiprocessing.cpu_count()


if __name__ == "__main__":
	split_point_ids = [
		"67ec2008812d548e4f14330d",
		"67f42552634b36b8d630e87a",
		"67f5abfc63efa2c12de882bb",
		"67f7060688dc9df0b26f7649",
		"67f842e488dc9df0b2028294",
		"67f997ca88dc9df0b297a2e1",
		"67fa4ea3057a21a72ca7345f",
		"67fa6629c51e4f48dfd47683",
		"67fa7eaaf571d724d7cca134",
		"67fa9b5b9f6356d4ba74498c",
		"67faba248f765726ca7e762f",
		"67fadac99f6356d4ba94a5ef",
		"67fafd23bf7211f76e35fc5d",
		"67fb24f1c51e4f48df0c4c55",
		"67fb464fca22e7ab4f6bb09c",
		"67fb66d0bbdbd2e61fe6e405",
		"67fb9068f571d724d71804f0",
		"67fbb891f571d724d722a0c5",
		"67fbdccdf571d724d72c760a",
		"67fc04fdca22e7ab4fa99fa9",
		"67fc32b0f571d724d74385b3",
		"67fc674fbbdbd2e61f2d4f33",
		"67fca04d88c2e92726d8917b",
		"67fcdf73ca22e7ab4fdf6b0f",
		"67fd1dc488c2e92726f2ea0c",
		"67fd5b4fbbdbd2e61f5e70c0",
		"67fd9807bbdbd2e61f697604",
		"67fdd61d057a21a72caf9b73",
		"67fe19b88f765726ca616e90",
		"67fe5c5bbbdbd2e61f926352",
		"67fe96f1184580c828de4004",
		"67fed30aca22e7ab4f7d1e4a",
		"67ff1ecb057a21a72c129b7b",
		"67ff6b2a057a21a72c1f2455",
		"67ffb503c51e4f48df1df4d4",
		"67fffccf88c2e9272689f09d",
		"6800564488c2e92726a49143",
		"6800d238f571d724d76a1da3",
		"680173d5c51e4f48df981de5",
		"6805330f88c2e927260c9350",
	]

	parallel_bid_sync = ParallelBidSync(num_workers=get_cpu_count() * 2, batch_size=10000)
	parallel_bid_sync.run(split_point_ids)
