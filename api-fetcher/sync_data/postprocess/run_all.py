"""
모든 후처리 스크립트를 순차적으로 실행

실행 순서:
1. update_notice_stats - notice 테이블 (bid_count, answer_rate, min_winning_price)
2. update_company_stats - company 테이블 (has_bid, bid_count)
3. update_bid_rates - bid 테이블 (bid_rate, bid_rate_diff)
   ※ notice.a_value를 참조하므로 notice 동기화 완료 후 실행
4. update_industry_type_classification - notice_industry_type 테이블 (classification_code/name)

사용법:
    python -m sync_data.postprocess.run_all
    python -m sync_data.postprocess.run_all --schema data
"""
import os
import sys
import argparse
from pathlib import Path
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
project_root = Path(__file__).resolve().parent.parent.parent
sys.path.insert(0, str(project_root))

from common.logger import setup_sync_loggers, update_log_meta


def run_all_postprocess(schema: str = None):
    """
    모든 후처리 스크립트 순차 실행

    Args:
        schema: PostgreSQL 스키마명 (기본값: 환경변수 또는 'data')
    """
    from sync_data.postprocess.update_notice_stats import update_notice_stats
    from sync_data.postprocess.update_company_stats import update_company_stats
    from sync_data.postprocess.update_bid_rates import update_bid_rates
    from sync_data.postprocess.update_industry_type_classification import update_classification_info

    schema = schema or os.getenv("POSTGRES_SCHEMA", "data")
    start_time = datetime.now()

    # 로거 설정
    log_result = setup_sync_loggers(
        table_name="all",
        schema=schema,
        process_type="postprocess",
    )
    loggers = log_result["loggers"]
    meta_path = log_result["meta_path"]

    loggers["application"].info("후처리 전체 실행 시작")
    loggers["application"].info(f"스키마: {schema}")
    loggers["application"].info(f"시작 시간: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")

    print("=" * 80)
    print("후처리 전체 실행 시작")
    print(f"스키마: {schema}")
    print("=" * 80)

    results = {}
    errors = []
    error_count = 0

    # 1. notice 테이블 후처리
    try:
        loggers["application"].info("[1/4] notice 테이블 후처리 (bid_count, answer_rate, min_winning_price)")
        print("\n[1/4] notice 테이블 후처리 (bid_count, answer_rate, min_winning_price)")
        results["notice"] = update_notice_stats(schema)
        loggers["application"].info("[1/4] notice 테이블 후처리 완료")
    except Exception as e:
        loggers["error"].error(f"[1/4] notice 테이블 후처리 실패: {e}", exc_info=True)
        print(f"[1/4] notice 테이블 후처리 실패: {e}")
        errors.append(("notice", e))
        error_count += 1

    # 2. company 테이블 후처리
    try:
        loggers["application"].info("[2/4] company 테이블 후처리 (has_bid, bid_count)")
        print("\n[2/4] company 테이블 후처리 (has_bid, bid_count)")
        results["company"] = update_company_stats(schema)
        loggers["application"].info("[2/4] company 테이블 후처리 완료")
    except Exception as e:
        loggers["error"].error(f"[2/4] company 테이블 후처리 실패: {e}", exc_info=True)
        print(f"[2/4] company 테이블 후처리 실패: {e}")
        errors.append(("company", e))
        error_count += 1

    # 3. bid 테이블 후처리 (notice.a_value 참조)
    try:
        loggers["application"].info("[3/4] bid 테이블 후처리 (bid_rate, bid_rate_diff)")
        print("\n[3/4] bid 테이블 후처리 (bid_rate, bid_rate_diff)")
        results["bid"] = update_bid_rates(schema)
        loggers["application"].info("[3/4] bid 테이블 후처리 완료")
    except Exception as e:
        loggers["error"].error(f"[3/4] bid 테이블 후처리 실패: {e}", exc_info=True)
        print(f"[3/4] bid 테이블 후처리 실패: {e}")
        errors.append(("bid", e))
        error_count += 1

    # 4. notice_industry_type 테이블 후처리
    try:
        loggers["application"].info("[4/4] notice_industry_type 테이블 후처리 (classification_code/name)")
        print("\n[4/4] notice_industry_type 테이블 후처리 (classification_code/name)")
        update_classification_info()  # 이 함수는 schema 파라미터 없음 (내부에서 처리)
        results["notice_industry_type"] = "success"
        loggers["application"].info("[4/4] notice_industry_type 테이블 후처리 완료")
    except Exception as e:
        loggers["error"].error(f"[4/4] notice_industry_type 테이블 후처리 실패: {e}", exc_info=True)
        print(f"[4/4] notice_industry_type 테이블 후처리 실패: {e}")
        errors.append(("notice_industry_type", e))
        error_count += 1

    # 결과 요약
    end_time = datetime.now()
    elapsed = end_time - start_time

    loggers["application"].info(f"후처리 전체 실행 완료 - 소요시간: {elapsed}")
    print("\n" + "=" * 80)
    print("후처리 전체 실행 완료")
    print(f"소요 시간: {elapsed}")
    print("=" * 80)

    # 성공/실패 요약
    success_count = 4 - error_count
    loggers["application"].info(f"성공: {success_count}/4, 실패: {error_count}/4")
    print(f"성공: {success_count}/4, 실패: {error_count}/4")

    # 메타데이터 업데이트
    status = "success" if error_count == 0 else "completed_with_errors"
    update_log_meta(
        meta_path,
        status=status,
        error_count=error_count,
    )

    if errors:
        loggers["error"].error("실패한 작업:")
        print("실패한 작업:")
        for table, error in errors:
            loggers["error"].error(f"  - {table}: {error}")
            print(f"  - {table}: {error}")
        return False

    loggers["application"].info("모든 후처리 작업 성공!")
    print("모든 후처리 작업 성공!")
    return True


def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description="후처리 스크립트 전체 실행")
    parser.add_argument(
        "--schema",
        type=str,
        default=None,
        help="PostgreSQL 스키마명 (기본값: 환경변수 POSTGRES_SCHEMA 또는 'data')"
    )
    args = parser.parse_args()

    success = run_all_postprocess(schema=args.schema)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
