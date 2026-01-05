"""
나라장터 데이터 동기화 DAG (MongoDB → PostgreSQL)

- 수집 DAG 완료 후 트리거됨
- 모든 테이블을 순차적으로 동기화
- 동기화 완료 후 후처리 UPDATE 실행
- 테이블별 재시도 (10회, 즉시 재시도)

동기화 순서:
1. notice_unified (공고 - 공사/물품/외자/용역 4개 카테고리 통합)
2. company (업체 - FK 참조됨)
3. institution (수요기관)
4. bid (투찰 - notice, company 참조)
5. reserve_price_range (예비가격 - notice 참조)
6. notice_industry_type (공고 면허제한정보 - notice 참조)
7. notice_region (공고 참가가능지역 - notice 참조)
8. company_industry_type (업체 업종정보 - company 참조)
9. postprocess (후처리 UPDATE - 계산 컬럼)
"""

from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.utils.dates import days_ago
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sync_data.sync.syncer_factory import create_syncer


# =============================================================================
# 설정
# =============================================================================

SCHEMA = "tmp"  # PostgreSQL 스키마 (테스트용: tmp, 운영용: data)

# 동기화 순서 (FK 의존성 고려)
SYNC_ORDER = [
    "notice_unified",  # 공사/물품/외자/용역 4개 카테고리 통합
    "company",
    "institution",
    "bid",
    "reserve_price_range",
    "notice_industry_type",
    "notice_region",
    "company_industry_type",
]


# =============================================================================
# 동기화 함수
# =============================================================================

def sync_table(table_name: str, schema: str = SCHEMA, **context):
    """
    단일 테이블 동기화 실행

    Args:
        table_name: 동기화할 테이블명
        schema: PostgreSQL 스키마명
    """
    print(f"\n{'=' * 80}")
    print(f"[동기화] {table_name} 테이블 시작 (schema: {schema})")
    print(f"{'=' * 80}\n")

    syncer = None
    try:
        syncer = create_syncer(table_name, schema=schema)
        syncer.sync()
        print(f"\n[동기화] {table_name} 테이블 완료")
    except Exception as e:
        print(f"\n[동기화] {table_name} 테이블 실패: {e}")
        raise
    finally:
        if syncer is not None:
            syncer.close()


def run_postprocess(schema: str = SCHEMA, **context):
    """
    후처리 UPDATE 실행

    동기화 완료 후 계산 컬럼들을 UPDATE합니다.
    - notice: bid_count, answer_rate
    - company: has_bid, bid_count
    - bid: bid_rate, bid_rate_diff
    - notice_industry_type: classification_code, classification_name
    """
    from sync_data.postprocess.run_all import run_all_postprocess

    print(f"\n{'=' * 80}")
    print(f"[후처리] 계산 컬럼 UPDATE 시작 (schema: {schema})")
    print(f"{'=' * 80}\n")

    try:
        success = run_all_postprocess(schema=schema)
        if not success:
            raise Exception("후처리 중 일부 작업 실패")
        print(f"\n[후처리] 모든 계산 컬럼 UPDATE 완료")
    except Exception as e:
        print(f"\n[후처리] 실패: {e}")
        raise


# =============================================================================
# DAG 정의
# =============================================================================

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 10,
    "retry_delay": timedelta(seconds=0),  # 즉시 재시도
}

with DAG(
    "sync_g2b_data_daily",
    default_args=default_args,
    description="나라장터 데이터 동기화 (MongoDB → PostgreSQL)",
    schedule_interval=None,  # 수집 DAG에서 트리거
    start_date=days_ago(1),
    catchup=False,
    tags=["sync", "postgresql", "mongodb", "g2b"],
) as dag:

    # =========================================================================
    # Task 생성 - 테이블별 동기화
    # =========================================================================

    tasks = {}

    for table_name in SYNC_ORDER:
        task = PythonOperator(
            task_id=f"sync_{table_name}",
            python_callable=sync_table,
            op_kwargs={"table_name": table_name, "schema": SCHEMA},
        )
        tasks[table_name] = task

    # =========================================================================
    # Task 생성 - 후처리 UPDATE
    # =========================================================================

    postprocess_task = PythonOperator(
        task_id="postprocess_calculated_columns",
        python_callable=run_postprocess,
        op_kwargs={"schema": SCHEMA},
    )

    # =========================================================================
    # Task 의존성 - 순차 실행
    # =========================================================================

    # notice → company → institution → bid → reserve_price_range → notice_industry_type → company_industry_type → postprocess
    for i in range(len(SYNC_ORDER) - 1):
        current_table = SYNC_ORDER[i]
        next_table = SYNC_ORDER[i + 1]
        tasks[current_table] >> tasks[next_table]

    # 마지막 동기화 Task 완료 후 후처리 실행
    tasks[SYNC_ORDER[-1]] >> postprocess_task
