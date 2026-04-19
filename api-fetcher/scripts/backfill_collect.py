"""미수집 기간 일괄 수집 스크립트 (Airflow 없이 직접 실행)"""
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from fetch_data.src.data_collector import DataCollector

# 수집 대상 API 목록 (서비스명, 오퍼레이션번호, bsns_div_cd)
APIS = [
    ("입찰공고정보서비스", 1, None),   # 공사
    ("입찰공고정보서비스", 2, None),   # 용역
    ("입찰공고정보서비스", 3, None),   # 외자
    ("입찰공고정보서비스", 4, None),   # 물품
    ("입찰공고정보서비스", 5, None),   # 물품 기초금액
    ("입찰공고정보서비스", 6, None),   # 공사 기초금액
    ("입찰공고정보서비스", 7, None),   # 용역 기초금액
    ("입찰공고정보서비스", 15, None),  # 면허제한
    ("입찰공고정보서비스", 16, None),  # 참가가능지역
    ("사용자정보서비스", 1, None),     # 수요기관
    ("사용자정보서비스", 2, None),     # 조달업체기본정보
    ("사용자정보서비스", 3, None),     # 조달업체업종정보
    ("낙찰정보서비스", 5, None),       # 개찰결과 물품
    ("낙찰정보서비스", 6, None),       # 개찰결과 공사
    ("낙찰정보서비스", 7, None),       # 개찰결과 용역
    ("낙찰정보서비스", 8, None),       # 개찰결과 외자
    ("낙찰정보서비스", 9, None),       # 예비가격 물품
    ("낙찰정보서비스", 10, None),      # 예비가격 공사
    ("낙찰정보서비스", 11, None),      # 예비가격 용역
    ("낙찰정보서비스", 12, None),      # 예비가격 외자
    ("공공데이터개방표준서비스", 2, 1), # 낙찰정보 물품
    ("공공데이터개방표준서비스", 2, 2), # 낙찰정보 외자
    ("공공데이터개방표준서비스", 2, 3), # 낙찰정보 공사
    ("공공데이터개방표준서비스", 2, 5), # 낙찰정보 용역
]


def collect_one(service_name, op_num, bsns_div_cd, date_str):
    try:
        kwargs = dict(
            service_name=service_name,
            operation_number=op_num,
            start_date=date_str,
            end_date=date_str,
        )
        if bsns_div_cd is not None:
            kwargs["bsns_div_cd"] = bsns_div_cd
        collector = DataCollector(**kwargs)
        collector.execute()
        return True, f"{service_name} op{op_num} bsns{bsns_div_cd} {date_str}"
    except Exception as e:
        return False, f"{service_name} op{op_num} bsns{bsns_div_cd} {date_str}: {e}"


def collect_day(date_str, max_workers=8):
    """하루치 전체 API를 병렬로 수집"""
    print(f"\n{'='*60}")
    print(f"[{date_str}] 수집 시작 ({len(APIS)}개 API, workers={max_workers})")
    print(f"{'='*60}")

    success, fail = 0, 0
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {}
        for svc, op, bsns in APIS:
            f = executor.submit(collect_one, svc, op, bsns, date_str)
            futures[f] = f"{svc} op{op}"

        for future in as_completed(futures):
            ok, msg = future.result()
            if ok:
                success += 1
            else:
                fail += 1
                print(f"  [FAIL] {msg}")

    print(f"[{date_str}] 완료: 성공 {success}, 실패 {fail}")
    return success, fail


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-date", required=True, help="시작일 (YYYY-MM-DD)")
    parser.add_argument("--end-date", required=True, help="종료일 (YYYY-MM-DD)")
    parser.add_argument("--workers", type=int, default=8, help="병렬 워커 수")
    args = parser.parse_args()

    start = datetime.strptime(args.start_date, "%Y-%m-%d")
    end = datetime.strptime(args.end_date, "%Y-%m-%d")

    total_days = (end - start).days + 1
    total_success, total_fail = 0, 0

    print(f"수집 기간: {args.start_date} ~ {args.end_date} ({total_days}일)")

    current = start
    day_num = 0
    while current <= end:
        day_num += 1
        date_str = current.strftime("%Y-%m-%d")
        print(f"\n>>> [{day_num}/{total_days}] {date_str}")
        s, f = collect_day(date_str, max_workers=args.workers)
        total_success += s
        total_fail += f
        current += timedelta(days=1)

    print(f"\n{'='*60}")
    print(f"전체 완료: {total_days}일, 성공 {total_success}, 실패 {total_fail}")
    print(f"{'='*60}")
