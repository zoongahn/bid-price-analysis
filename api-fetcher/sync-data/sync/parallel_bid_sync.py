from multiprocessing import Manager, Process
from pymongo import MongoClient
from bson import ObjectId
from tqdm import tqdm
import time

from sync import DataSync


class ParallelBidSync:
	def __init__(self, num_workers, batch_size):
		self.num_workers = num_workers
		self.syncer = DataSync(batch_size)
		self.mongo_bid = self.syncer.mongo_bid
		self.syncer.psql_cur.execute("SELECT bidntceno, bidntceord FROM notice;")
		# DataSync 인스턴스 내부에 notice_keys 생성
		self.syncer.notice_keys = self.syncer.psql_cur.fetchall()

	def _log(self, message: str):
		print(f"[ParallelBidSync] {message}")

	def get_split_points(self) -> list[ObjectId]:
		self._log(f"Calculating split points for {self.num_workers} workers")
		total = self.mongo_bid.count_documents({"is_synced": {"$ne": True}})
		num_splits = self.num_workers
		step = total // num_splits
		ids: list[ObjectId] = []

		for i in range(num_splits):
			skip = i * step
			doc = self.mongo_bid.find({"is_synced": {"$ne": True}}).sort("_id", 1).skip(skip).limit(1).next()
			ids.append(doc["_id"])
			self._log(f"  -> Split point {i + 1}/{num_splits}: {doc['_id']}")

		self._log(f"Split points calculated ({len(ids)} points): {ids}")

		ids.append(ObjectId())
		return ids

	def run(self):
		# 1) 범위 분할
		self._log("Starting run()")
		self._log("Step 1: split-point calculation")
		points = self.get_split_points()

		self._log("Step 2: spawning worker processes")
		manager = Manager()

		progress_counter = manager.Value("i", 0)
		processes = []

		# 2) 워커 스폰
		for i in range(self.num_workers):
			self._log(f"  -> Spawning worker {i + 1}/{self.num_workers} for range {points[i]}…{points[i + 1]}")
			start_id, end_id = points[i], points[i + 1]
			p = Process(
				target=self.syncer.sync_mongo_to_postgres,
				kwargs={
					"mongo_collection": self.mongo_bid,
					"psql_table": "bid",
					"psql_pk": ("bidntceno", "bidntceord", "bidprccorpbizrno"),
					"mongo_unique_keys": ("bidNtceNo", "bidNtceOrd", "bidprcCorpBizrno"),
					"preprocess": self.syncer.preprocess_bid,
					"start_id": start_id,
					"end_id": end_id,
					"progress_counter": progress_counter,
				}
			)
			p.start()
			processes.append(p)

		# 모니터링: 전체 배치 수 계산 및 tqdm 표시
		self._log("Workers started; entering monitoring phase")
		total_docs = self.mongo_bid.count_documents({"is_synced": {"$ne": True}})
		total_batches = (total_docs + self.syncer.batch_size - 1) // self.syncer.batch_size
		pbar = tqdm(total=total_batches, desc="전체 배치 진행")
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
	parallel_bid_sync = ParallelBidSync(num_workers=get_cpu_count() * 2, batch_size=10000)
	parallel_bid_sync.run()
