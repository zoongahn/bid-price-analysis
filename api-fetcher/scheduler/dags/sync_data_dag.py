"""
나라장터 데이터 동기화 DAG (MongoDB → PostgreSQL)

- 수집 DAG 완료 후 트리거됨
- 모든 테이블을 순차적으로 동기화
- 동기화 완료 후 후처리 DAG 트리거
- 테이블별 재시도 (10회, 즉시 재시도)

동기화 순서:
1. notice_unified (공고 - 공사/물품/외자/용역 4개 카테고리 통합)
2. company (업체 - FK 참조됨)
3. handle_unknown_companies (더미/테스트 bizrno → __UNKNOWN__ 처리)
4. verify_bizrno (bid의 모든 bizrno가 company에 존재하는지 확인)
5. institution (수요기관)
6. bid (투찰 - notice, company 참조)
7. reserve_price_range (예비가격 - notice 참조)
8. notice_industry_type (공고 면허제한정보 - notice 참조)
9. notice_region (공고 참가가능지역 - notice 참조)
10. company_industry_type (업체 업종정보 - company 참조)
11. trigger_postprocess (후처리 DAG 트리거)
"""

from datetime import timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from sync_data.sync.syncer_factory import create_syncer


# =============================================================================
# 설정
# =============================================================================

SCHEMA = "data"  # PostgreSQL 스키마 (테스트용: tmp, 운영용: data)

# 동기화 순서 (FK 의존성 고려)
SYNC_ORDER = [
    "notice",  # 공사/물품/외자/용역 4개 카테고리 통합 (syncer_factory: NoticeUnifiedSyncer)
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


def handle_unknown_companies(schema: str = SCHEMA, **context):
    """
    더미/테스트 bizrno를 __UNKNOWN__ 업체로 company 테이블에 추가

    company 동기화 후에도 bid에 있지만 company에 없는 bizrno가 있는 경우,
    해당 bizrno를 corpnm='__UNKNOWN__'으로 company 테이블에 INSERT합니다.
    """
    from sync_data.prefetch.handle_missing_companies import MissingCompanyHandler

    print(f"\n{'=' * 80}")
    print(f"[FK 핸들링] 더미/테스트 bizrno → __UNKNOWN__ 처리 (schema: {schema})")
    print(f"{'=' * 80}\n")

    handler = MissingCompanyHandler(schema=schema)
    try:
        inserted = handler.insert_missing_as_unknown_companies()
        print(f"\n[FK 핸들링] __UNKNOWN__ 업체 추가 완료: {inserted}개")
    except Exception as e:
        print(f"\n[FK 핸들링] 실패: {e}")
        raise
    finally:
        handler.close_connections()


def verify_bizrno_before_bid_sync(schema: str = SCHEMA, **context):
    """
    bid 동기화 전 모든 bizrno가 company에 존재하는지 확인

    누락된 bizrno가 있으면 오류를 발생시켜 bid 동기화를 중단합니다.
    """
    from sync_data.prefetch.handle_missing_companies import MissingCompanyHandler

    print(f"\n{'=' * 80}")
    print(f"[FK 검증] bid bizrno가 company에 모두 존재하는지 확인 (schema: {schema})")
    print(f"{'=' * 80}\n")

    handler = MissingCompanyHandler(schema=schema)
    try:
        summary = handler.get_summary()
        missing_count = summary["missing_bizno_count"]

        print(f"  - bid 테이블 총 행: {summary['bid_total']:,}")
        print(f"  - bid unique bizrno: {summary['bid_unique_bizno']:,}")
        print(f"  - company 테이블 총 행: {summary['company_count']:,}")
        print(f"  - 누락된 bizrno: {missing_count}")

        if missing_count > 0:
            # 누락된 bizrno 목록 조회
            missing_bizno = handler.get_missing_bizno_from_psql()
            print(f"\n[FK 검증] 오류: 누락된 bizrno {missing_count}개 발견!")
            print(f"  - 누락 목록: {list(missing_bizno)[:20]}")
            raise Exception(f"bid 동기화 불가: company에 없는 bizrno {missing_count}개 존재")

        print(f"\n[FK 검증] 통과: 모든 bizrno가 company에 존재함")

    except Exception as e:
        print(f"\n[FK 검증] 실패: {e}")
        raise
    finally:
        handler.close_connections()


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
    # Task 생성 - FK 핸들링 (company 동기화 후, bid 동기화 전)
    # =========================================================================

    # 더미/테스트 bizrno → __UNKNOWN__ 업체로 추가
    handle_unknown_task = PythonOperator(
        task_id="handle_unknown_companies",
        python_callable=handle_unknown_companies,
        op_kwargs={"schema": SCHEMA},
    )

    # bid 동기화 전 모든 bizrno가 company에 존재하는지 확인
    verify_bizrno_task = PythonOperator(
        task_id="verify_bizrno_before_bid_sync",
        python_callable=verify_bizrno_before_bid_sync,
        op_kwargs={"schema": SCHEMA},
    )

    # =========================================================================
    # Task 생성 - 후처리 DAG 트리거
    # =========================================================================

    trigger_postprocess = TriggerDagRunOperator(
        task_id="trigger_postprocess_dag",
        trigger_dag_id="postprocess_g2b_data",
        wait_for_completion=False,  # 후처리 완료를 기다리지 않음
    )

    # =========================================================================
    # Task 의존성 - 순차 실행
    # =========================================================================

    # 흐름: notice → company → [FK 핸들링] → institution → bid → ... → postprocess
    #
    # 1. notice_unified → company
    # 2. company → handle_unknown_companies → verify_bizrno → institution
    # 3. institution → bid → reserve_price_range → ... → postprocess

    # notice → company
    tasks["notice"] >> tasks["company"]

    # company → FK 핸들링 → institution
    tasks["company"] >> handle_unknown_task >> verify_bizrno_task >> tasks["institution"]

    # institution → bid 순차, 이후는 병렬 (서로 독립적)
    tasks["institution"] >> tasks["bid"]

    parallel_tables = ["reserve_price_range", "notice_industry_type",
                       "notice_region", "company_industry_type"]
    for t in parallel_tables:
        tasks["bid"] >> tasks[t] >> trigger_postprocess
