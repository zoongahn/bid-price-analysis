"""
투찰데이터 수집 CLI

DataCollector.collect_bid_data 메서드의 CLI 래퍼입니다.

사용법:
    python -m fetch_data.src.bid_data_collector --schema test --batch-size 1000
    python -m fetch_data.src.bid_data_collector --schema test --progrs-type 개찰완료
    python -m fetch_data.src.bid_data_collector --schema test --progrs-type 개찰완료 --num-workers 8
    python -m fetch_data.src.bid_data_collector --schema test --num-workers 200 --sync-flags
"""

import argparse
import os
from datetime import datetime
from multiprocessing import Process
from .data_collector import DataCollector
from common.api_key_manager import api_key_manager


def sync_bid_collected_flags(schema: str = "test"):
    """
    MongoDB 투찰 건수와 PostgreSQL prtcptcnum을 비교하여
    완전히 수집된 공고의 bid_collected 플래그를 TRUE로 업데이트
    """
    from common.init_mongodb import init_mongodb
    from common.init_psql import init_psql

    print("[INFO] bid_collected 플래그 보충 작업 시작...")

    # MongoDB 연결
    mongo_server, mongo_client = init_mongodb()
    db = mongo_client.get_database('gfcon_raw')
    collection = db['낙찰정보서비스.개찰결과개찰완료목록조회']

    # 1. MongoDB에서 모든 bidNtceNo별 투찰 건수 집계
    print('[INFO] MongoDB에서 공고별 투찰 건수 집계 중...')
    pipeline = [
        {'$group': {'_id': '$bidNtceNo', 'count': {'$sum': 1}}}
    ]
    mongo_counts = {}
    for doc in collection.aggregate(pipeline, allowDiskUse=True):
        mongo_counts[doc['_id']] = doc['count']
    print(f'[INFO]   MongoDB 공고 수: {len(mongo_counts):,}건')

    # PostgreSQL 연결
    psql_server, conn = init_psql()
    cursor = conn.cursor()

    # 2. PostgreSQL에서 bid_collected != TRUE인 개찰완료 공고 조회
    print('[INFO] PostgreSQL에서 미수집 플래그 공고 조회 중...')
    cursor.execute(f'''
        SELECT bidntceno, prtcptcnum
        FROM {schema}.notice
        WHERE progrsdivcdnm = '개찰완료'
        AND bid_collected IS NOT TRUE
    ''')

    # 3. 비교
    matched = []
    mismatched = 0
    not_in_mongo = 0

    for row in cursor.fetchall():
        bidntceno, pg_count = row
        if bidntceno in mongo_counts:
            if pg_count == mongo_counts[bidntceno]:
                matched.append(bidntceno)
            else:
                mismatched += 1
        else:
            not_in_mongo += 1

    print(f'[INFO] 비교 결과:')
    print(f'[INFO]   일치 (완전 수집): {len(matched):,}건')
    print(f'[INFO]   불일치 (불완전): {mismatched:,}건')
    print(f'[INFO]   MongoDB에 없음: {not_in_mongo:,}건')

    # 4. 플래그 업데이트
    if matched:
        print(f'[INFO] 플래그 업데이트 중... ({len(matched):,}건)')
        batch_size = 1000
        updated = 0
        for i in range(0, len(matched), batch_size):
            batch = matched[i:i+batch_size]
            placeholders = ','.join(['%s'] * len(batch))
            cursor.execute(f'''
                UPDATE {schema}.notice
                SET bid_collected = TRUE
                WHERE bidntceno IN ({placeholders})
            ''', batch)
            updated += cursor.rowcount
        conn.commit()
        print(f'[INFO] 완료! {updated:,}건 업데이트됨')
    else:
        print('[INFO] 업데이트할 공고가 없습니다.')

    conn.close()
    mongo_client.close()
    if psql_server:
        psql_server.stop()
    if mongo_server:
        mongo_server.stop()

    return len(matched)


def run_worker(
    worker_id: int,
    num_workers: int,
    schema: str,
    progrs_type: str | None,
    batch_size: int,
    limit: int | None,
    max_retries: int,
    workers_per_key: int,
    shared_log_dir: str | None = None,
):
    """개별 워커 프로세스에서 실행되는 함수"""
    # 워커에 담당 키 할당
    api_key_manager.assign_key_for_worker(worker_id, workers_per_key=workers_per_key)

    DataCollector.collect_bid_data(
        schema=schema,
        progrs_type=progrs_type,
        batch_size=batch_size,
        limit=limit,
        max_retries=max_retries,
        worker_id=worker_id,
        num_workers=num_workers,
        shared_log_dir=shared_log_dir,
    )


def main():
    parser = argparse.ArgumentParser(
        description="투찰데이터 수집",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--schema",
        type=str,
        default="test",
        help="PostgreSQL 스키마 (기본값: test)",
    )
    parser.add_argument(
        "--progrs-type",
        type=str,
        choices=["개찰완료", "유찰", "재입찰", "재시담"],
        help="특정 진행구분만 수집",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="배치 크기 (기본값: 100)",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="수집할 최대 공고 수",
    )
    parser.add_argument(
        "--max-retries",
        type=int,
        default=3,
        help="실패 시 최대 재시도 횟수 (기본값: 3)",
    )
    parser.add_argument(
        "--num-workers",
        type=int,
        default=1,
        help="워커 수 (기본값: 1, 병렬 처리 시 증가)",
    )
    parser.add_argument(
        "--workers-per-key",
        type=int,
        default=2,
        help="키당 워커 수 (기본값: 2)",
    )
    parser.add_argument(
        "--sync-flags",
        action="store_true",
        help="수집 완료 후 bid_collected 플래그 보충 작업 실행",
    )

    args = parser.parse_args()

    if args.num_workers > 1:
        # 멀티프로세스 모드
        print(f"[INFO] {args.num_workers}개 워커로 병렬 수집 시작")

        # 공유 로그 디렉토리 생성
        current_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(os.path.dirname(current_dir))
        logs_dir = os.path.join(project_root, "logs", "fetch")
        os.makedirs(logs_dir, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        progrs_suffix = f"_{args.progrs_type}" if args.progrs_type else ""
        shared_log_dir = os.path.join(
            logs_dir,
            f"{timestamp}_낙찰정보서비스_개찰결과{progrs_suffix}"
        )
        os.makedirs(shared_log_dir, exist_ok=True)
        print(f"[INFO] 로그 디렉토리: {shared_log_dir}")

        processes = []
        for worker_id in range(args.num_workers):
            p = Process(
                target=run_worker,
                args=(
                    worker_id,
                    args.num_workers,
                    args.schema,
                    args.progrs_type,
                    args.batch_size,
                    args.limit,
                    args.max_retries,
                    args.workers_per_key,
                    shared_log_dir,
                ),
            )
            p.start()
            processes.append(p)
            print(f"[INFO] 워커 {worker_id} 시작 (PID: {p.pid})")

        # 모든 워커 완료 대기
        for p in processes:
            p.join()

        print("[INFO] 모든 워커 완료")

        # 플래그 보충 작업
        if args.sync_flags:
            sync_bid_collected_flags(args.schema)
    else:
        # 단일 프로세스 모드
        DataCollector.collect_bid_data(
            schema=args.schema,
            progrs_type=args.progrs_type,
            batch_size=args.batch_size,
            limit=args.limit,
            max_retries=args.max_retries,
        )

        # 플래그 보충 작업
        if args.sync_flags:
            sync_bid_collected_flags(args.schema)


if __name__ == "__main__":
    main()
