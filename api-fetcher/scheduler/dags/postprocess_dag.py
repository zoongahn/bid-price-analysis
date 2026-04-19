"""
나라장터 데이터 후처리 DAG (계산 컬럼 UPDATE)

- 동기화 DAG 완료 후 트리거됨
- 각 후처리 단계를 개별 Task로 실행
- Task 간 의존성에 따라 순차 실행

후처리 순서:
1. update_notice_stats - notice 테이블 (answer_rate, min_winning_price)
2. update_company_stats - company 테이블 (has_bid, bid_count)
3. update_bid_sucsflwstlmtrt - bid 테이블 (sucsflwstlmtrt)
   ※ notice.sucsfbidlwltrate로 NULL인 낙찰하한율 채움
4. update_bid_rates - bid 테이블 (bid_rate, bid_rate_diff)
   ※ notice.a_value, bid.sucsflwstlmtrt 참조하므로 3번 완료 후 실행
5. update_winner_bid_rate - notice 테이블 (winner_bid_rate)
   ※ bid.bid_rate를 참조하므로 4번 완료 후 실행
6. update_industry_type_classification - notice_industry_type 테이블 (classification_code/name)
"""

from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))


# =============================================================================
# 설정
# =============================================================================

SCHEMA = "data"  # PostgreSQL 스키마 (테스트용: tmp, 운영용: data)


# =============================================================================
# 후처리 함수
# =============================================================================

def run_update_notice_stats(schema: str = SCHEMA, **context):
    """notice 테이블 후처리 (answer_rate, min_winning_price)"""
    from sync_data.postprocess.update_notice_stats import update_notice_stats

    print(f"\n{'=' * 80}")
    print(f"[후처리] notice 테이블 (answer_rate, min_winning_price)")
    print(f"{'=' * 80}\n")

    try:
        result = update_notice_stats(schema)
        print(f"\n[후처리] notice 테이블 완료")
        return result
    except Exception as e:
        print(f"\n[후처리] notice 테이블 실패: {e}")
        raise


def run_update_company_stats(schema: str = SCHEMA, **context):
    """company 테이블 후처리 (has_bid, bid_count)"""
    from sync_data.postprocess.update_company_stats import update_company_stats

    print(f"\n{'=' * 80}")
    print(f"[후처리] company 테이블 (has_bid, bid_count)")
    print(f"{'=' * 80}\n")

    try:
        result = update_company_stats(schema)
        print(f"\n[후처리] company 테이블 완료")
        return result
    except Exception as e:
        print(f"\n[후처리] company 테이블 실패: {e}")
        raise


def run_update_bid_sucsflwstlmtrt(schema: str = SCHEMA, **context):
    """bid 테이블 후처리 (sucsflwstlmtrt - 낙찰하한율)"""
    from sync_data.postprocess.update_bid_sucsflwstlmtrt import update_bid_sucsflwstlmtrt

    print(f"\n{'=' * 80}")
    print(f"[후처리] bid 테이블 (sucsflwstlmtrt)")
    print(f"{'=' * 80}\n")

    try:
        result = update_bid_sucsflwstlmtrt(schema)
        print(f"\n[후처리] bid 테이블 sucsflwstlmtrt 완료")
        return result
    except Exception as e:
        print(f"\n[후처리] bid 테이블 sucsflwstlmtrt 실패: {e}")
        raise


def run_update_bid_rates(schema: str = SCHEMA, **context):
    """bid 테이블 후처리 (bid_rate, bid_rate_diff)"""
    from sync_data.postprocess.update_bid_rates import update_bid_rates

    print(f"\n{'=' * 80}")
    print(f"[후처리] bid 테이블 (bid_rate, bid_rate_diff)")
    print(f"{'=' * 80}\n")

    try:
        result = update_bid_rates(schema)
        print(f"\n[후처리] bid 테이블 bid_rate 완료")
        return result
    except Exception as e:
        print(f"\n[후처리] bid 테이블 bid_rate 실패: {e}")
        raise


def run_update_winner_bid_rate(schema: str = SCHEMA, **context):
    """notice 테이블 후처리 (winner_bid_rate)"""
    from sync_data.postprocess.update_winner_bid_rate import update_winner_bid_rate

    print(f"\n{'=' * 80}")
    print(f"[후처리] notice 테이블 (winner_bid_rate)")
    print(f"{'=' * 80}\n")

    try:
        result = update_winner_bid_rate(schema)
        print(f"\n[후처리] notice 테이블 winner_bid_rate 완료")
        return result
    except Exception as e:
        print(f"\n[후처리] notice 테이블 winner_bid_rate 실패: {e}")
        raise


def run_update_industry_type_classification(**context):
    """notice_industry_type 테이블 후처리 (classification_code/name)"""
    from sync_data.postprocess.update_industry_type_classification import update_classification_info

    print(f"\n{'=' * 80}")
    print(f"[후처리] notice_industry_type 테이블 (classification_code/name)")
    print(f"{'=' * 80}\n")

    try:
        update_classification_info()
        print(f"\n[후처리] notice_industry_type 테이블 완료")
        return "success"
    except Exception as e:
        print(f"\n[후처리] notice_industry_type 테이블 실패: {e}")
        raise


# =============================================================================
# DAG 정의
# =============================================================================

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 3,
    "retry_delay": timedelta(minutes=1),
}

with DAG(
    "postprocess_g2b_data",
    default_args=default_args,
    description="나라장터 데이터 후처리 (계산 컬럼 UPDATE)",
    schedule_interval=None,  # 동기화 DAG에서 트리거
    start_date=days_ago(1),
    catchup=False,
    tags=["postprocess", "postgresql", "g2b"],
) as dag:

    # =========================================================================
    # Task 정의
    # =========================================================================

    # 1. notice 테이블 후처리
    task_notice_stats = PythonOperator(
        task_id="update_notice_stats",
        python_callable=run_update_notice_stats,
        op_kwargs={"schema": SCHEMA},
    )

    # 2. company 테이블 후처리
    task_company_stats = PythonOperator(
        task_id="update_company_stats",
        python_callable=run_update_company_stats,
        op_kwargs={"schema": SCHEMA},
    )

    # 3. bid 테이블 sucsflwstlmtrt 후처리
    task_bid_sucsflwstlmtrt = PythonOperator(
        task_id="update_bid_sucsflwstlmtrt",
        python_callable=run_update_bid_sucsflwstlmtrt,
        op_kwargs={"schema": SCHEMA},
    )

    # 4. bid 테이블 bid_rate 후처리
    task_bid_rates = PythonOperator(
        task_id="update_bid_rates",
        python_callable=run_update_bid_rates,
        op_kwargs={"schema": SCHEMA},
    )

    # 5. notice 테이블 winner_bid_rate 후처리
    task_winner_bid_rate = PythonOperator(
        task_id="update_winner_bid_rate",
        python_callable=run_update_winner_bid_rate,
        op_kwargs={"schema": SCHEMA},
    )

    # 6. notice_industry_type 테이블 후처리
    task_industry_classification = PythonOperator(
        task_id="update_industry_type_classification",
        python_callable=run_update_industry_type_classification,
    )

    # =========================================================================
    # Task 의존성
    # =========================================================================
    #
    # 병렬 실행 가능:
    #   - notice_stats, company_stats (서로 독립)
    #
    # 순차 실행 필요:
    #   - bid_sucsflwstlmtrt → bid_rates → winner_bid_rate
    #     (bid_rate는 sucsflwstlmtrt 필요, winner_bid_rate는 bid_rate 필요)
    #
    # 독립 실행 가능:
    #   - industry_classification (다른 후처리와 독립)

    # notice_stats, company_stats 완료 후 bid_sucsflwstlmtrt 실행
    [task_notice_stats, task_company_stats] >> task_bid_sucsflwstlmtrt

    # bid 관련 순차 실행
    task_bid_sucsflwstlmtrt >> task_bid_rates >> task_winner_bid_rate

    # industry_classification은 독립적으로 실행 (notice_stats 완료 후)
    task_notice_stats >> task_industry_classification
