"""
나라장터 공공데이터 수집 DAG
- 매일 새벽 2시(KST) 실행 → 전날 데이터 수집
- 예: 12/16 02:00 실행 → 12/15 데이터 수집
- 모든 API를 병렬로 수집하여 MongoDB에 저장

수집 대상 API:
[입찰공고정보서비스]
1. 입찰공고목록정보에대한공사조회 (operation_number=1)
2. 입찰공고목록정보에대한용역조회 (operation_number=2)
3. 입찰공고목록정보에대한외자조회 (operation_number=3)
4. 입찰공고목록정보에대한물품조회 (operation_number=4)
5. 입찰공고목록정보에대한물품기초금액조회 (operation_number=5)
6. 입찰공고목록정보에대한공사기초금액조회 (operation_number=6)
7. 입찰공고목록정보에대한용역기초금액조회 (operation_number=7)
8. 입찰공고목록정보에대한면허제한정보조회 (operation_number=15)
9. 입찰공고목록정보에대한참가가능지역정보조회 (operation_number=16)
[사용자정보서비스]
11. 수요기관정보조회 (operation_number=1)
12. 조달업체기본정보 (operation_number=2)
13. 조달업체업종정보조회 (operation_number=3)

[국세청]
22. 사업자등록 상태조회 (조달업체기본정보 수집 후 실행)

[낙찰정보서비스 - 예비가격]
14. 개찰결과물품예비가격상세목록조회 (operation_number=9)
15. 개찰결과공사예비가격상세목록조회 (operation_number=10)
16. 개찰결과용역예비가격상세목록조회 (operation_number=11)
17. 개찰결과외자예비가격상세목록조회 (operation_number=12)

[낙찰정보서비스 - 개찰결과] (입력일시 기준)
22. 개찰결과물품목록조회 (operation_number=5)
23. 개찰결과공사목록조회 (operation_number=6)
24. 개찰결과용역목록조회 (operation_number=7)
25. 개찰결과외자목록조회 (operation_number=8)

[공공데이터개방표준서비스]
18. 데이터셋개방표준에따른낙찰정보-물품 (operation_number=2, bsns_div_cd=1)
19. 데이터셋개방표준에따른낙찰정보-외자 (operation_number=2, bsns_div_cd=2)
20. 데이터셋개방표준에따른낙찰정보-공사 (operation_number=2, bsns_div_cd=3)
21. 데이터셋개방표준에따른낙찰정보-용역 (operation_number=2, bsns_div_cd=5)
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.trigger_dagrun import TriggerDagRunOperator
from airflow.utils.dates import days_ago
import sys
import os

# 프로젝트 루트를 Python path에 추가
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../"))

from fetch_data.src.data_collector import DataCollector
from fetch_data.src.missing_company_collector import collect_missing_companies
from fetch_data.src.nts_status_collector import collect_nts_status


# =============================================================================
# 수집 함수 정의
# =============================================================================

def get_target_date(context) -> str:
    """
    실행일 기준 전날 날짜 반환

    Airflow 스케줄 특성상 execution_date는 인터벌 시작 시점이므로,
    KST 02:00 실행 시 전날 데이터를 수집하려면 +1일 필요
    예: KST 12/16 02:00 실행 → execution_date=12/14 → +1일 → 12/15 수집
    """
    execution_date = context["execution_date"]
    target_date = execution_date + timedelta(days=1)
    return target_date.strftime("%Y-%m-%d")


def collect_notice_cnstwk(**context):
    """[공고] 입찰공고목록정보에대한공사조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=1,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-공사] 수집 완료: {date_str}")


def collect_notice_bssamt(**context):
    """[공고] 입찰공고목록정보에대한공사기초금액조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=6,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-기초금액] 수집 완료: {date_str}")


def collect_notice_license(**context):
    """[공고] 입찰공고목록정보에대한면허제한정보조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=15,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-면허제한] 수집 완료: {date_str}")


def collect_bid_data_goods(**context):
    """[투찰] 데이터셋개방표준에따른낙찰정보 - 물품"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="공공데이터개방표준서비스",
        operation_number=2,
        start_date=date_str,
        end_date=date_str,
        bsns_div_cd=1,  # 물품
    )
    collector.execute()
    print(f"[투찰-낙찰정보-물품] 수집 완료: {date_str}")


def collect_bid_data_foreign(**context):
    """[투찰] 데이터셋개방표준에따른낙찰정보 - 외자"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="공공데이터개방표준서비스",
        operation_number=2,
        start_date=date_str,
        end_date=date_str,
        bsns_div_cd=2,  # 외자
    )
    collector.execute()
    print(f"[투찰-낙찰정보-외자] 수집 완료: {date_str}")


def collect_bid_data_cnstwk(**context):
    """[투찰] 데이터셋개방표준에따른낙찰정보 - 공사"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="공공데이터개방표준서비스",
        operation_number=2,
        start_date=date_str,
        end_date=date_str,
        bsns_div_cd=3,  # 공사
    )
    collector.execute()
    print(f"[투찰-낙찰정보-공사] 수집 완료: {date_str}")


def collect_bid_data_service(**context):
    """[투찰] 데이터셋개방표준에따른낙찰정보 - 용역"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="공공데이터개방표준서비스",
        operation_number=2,
        start_date=date_str,
        end_date=date_str,
        bsns_div_cd=5,  # 용역
    )
    collector.execute()
    print(f"[투찰-낙찰정보-용역] 수집 완료: {date_str}")


def collect_company_basic(**context):
    """[업체] 조달업체기본정보"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="사용자정보서비스",
        operation_number=2,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[업체-기본정보] 수집 완료: {date_str}")


def collect_company_industry(**context):
    """[업체] 조달업체업종정보조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="사용자정보서비스",
        operation_number=3,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[업체-업종정보] 수집 완료: {date_str}")


def collect_institution(**context):
    """[수요기관] 수요기관정보조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="사용자정보서비스",
        operation_number=1,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[수요기관] 수집 완료: {date_str}")


def collect_reserve_price_goods(**context):
    """[예비가격] 개찰결과물품예비가격상세목록조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=9,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[예비가격-물품] 수집 완료: {date_str}")


def collect_reserve_price_cnstwk(**context):
    """[예비가격] 개찰결과공사예비가격상세목록조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=10,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[예비가격-공사] 수집 완료: {date_str}")


def collect_reserve_price_service(**context):
    """[예비가격] 개찰결과용역예비가격상세목록조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=11,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[예비가격-용역] 수집 완료: {date_str}")


def collect_reserve_price_foreign(**context):
    """[예비가격] 개찰결과외자예비가격상세목록조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=12,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[예비가격-외자] 수집 완료: {date_str}")


def collect_notice_service(**context):
    """[공고] 입찰공고목록정보에대한용역조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=2,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-용역] 수집 완료: {date_str}")


def collect_notice_foreign(**context):
    """[공고] 입찰공고목록정보에대한외자조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=3,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-외자] 수집 완료: {date_str}")


def collect_notice_goods(**context):
    """[공고] 입찰공고목록정보에대한물품조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=4,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-물품] 수집 완료: {date_str}")


def collect_notice_goods_bssamt(**context):
    """[공고] 입찰공고목록정보에대한물품기초금액조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=5,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-물품기초금액] 수집 완료: {date_str}")


def collect_notice_service_bssamt(**context):
    """[공고] 입찰공고목록정보에대한용역기초금액조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=7,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-용역기초금액] 수집 완료: {date_str}")


def collect_notice_region(**context):
    """[공고] 입찰공고목록정보에대한참가가능지역정보조회"""
    date_str = get_target_date(context)

    collector = DataCollector(
        service_name="입찰공고정보서비스",
        operation_number=16,
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[공고-참가가능지역] 수집 완료: {date_str}")


def collect_openg_result_goods(**context):
    """[개찰결과] 개찰결과물품목록조회 - 입력일시 기준"""
    date_str = get_target_date(context)
    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=5,  # 개찰결과물품목록조회
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[개찰결과-물품] 수집 완료: {date_str}")


def collect_openg_result_cnstwk(**context):
    """[개찰결과] 개찰결과공사목록조회 - 입력일시 기준"""
    date_str = get_target_date(context)
    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=6,  # 개찰결과공사목록조회
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[개찰결과-공사] 수집 완료: {date_str}")


def collect_openg_result_service(**context):
    """[개찰결과] 개찰결과용역목록조회 - 입력일시 기준"""
    date_str = get_target_date(context)
    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=7,  # 개찰결과용역목록조회
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[개찰결과-용역] 수집 완료: {date_str}")


def collect_openg_result_foreign(**context):
    """[개찰결과] 개찰결과외자목록조회 - 입력일시 기준"""
    date_str = get_target_date(context)
    collector = DataCollector(
        service_name="낙찰정보서비스",
        operation_number=8,  # 개찰결과외자목록조회
        start_date=date_str,
        end_date=date_str,
    )
    collector.execute()
    print(f"[개찰결과-외자] 수집 완료: {date_str}")


# =============================================================================
# DAG 정의
# =============================================================================

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "email_on_failure": False,
    "email_on_retry": False,
    "retries": 2,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    "collect_g2b_data_daily",
    default_args=default_args,
    description="나라장터 공공데이터 일일 수집 (전체 API 병렬 실행)",
    schedule_interval="0 17 * * *",  # UTC 17:00 = KST 02:00 (매일 새벽 2시)
    start_date=days_ago(1),
    catchup=True,
    tags=["data-collection", "mongodb", "g2b"],
) as dag:

    # =========================================================================
    # Task 정의 - 모든 API 병렬 수집
    # =========================================================================

    # 공고 관련
    task_notice_cnstwk = PythonOperator(
        task_id="collect_notice_cnstwk",
        python_callable=collect_notice_cnstwk,
    )

    task_notice_bssamt = PythonOperator(
        task_id="collect_notice_bssamt",
        python_callable=collect_notice_bssamt,
    )

    task_notice_license = PythonOperator(
        task_id="collect_notice_license",
        python_callable=collect_notice_license,
    )

    # 투찰/낙찰 관련 (4가지 사업구분별)
    task_bid_data_goods = PythonOperator(
        task_id="collect_bid_data_goods",
        python_callable=collect_bid_data_goods,
    )

    task_bid_data_foreign = PythonOperator(
        task_id="collect_bid_data_foreign",
        python_callable=collect_bid_data_foreign,
    )

    task_bid_data_cnstwk = PythonOperator(
        task_id="collect_bid_data_cnstwk",
        python_callable=collect_bid_data_cnstwk,
    )

    task_bid_data_service = PythonOperator(
        task_id="collect_bid_data_service",
        python_callable=collect_bid_data_service,
    )

    # 업체 관련
    task_company_basic = PythonOperator(
        task_id="collect_company_basic",
        python_callable=collect_company_basic,
    )

    task_company_industry = PythonOperator(
        task_id="collect_company_industry",
        python_callable=collect_company_industry,
    )

    # 수요기관
    task_institution = PythonOperator(
        task_id="collect_institution",
        python_callable=collect_institution,
    )

    # 예비가격 (4가지 공종별)
    task_reserve_price_goods = PythonOperator(
        task_id="collect_reserve_price_goods",
        python_callable=collect_reserve_price_goods,
    )

    task_reserve_price_cnstwk = PythonOperator(
        task_id="collect_reserve_price_cnstwk",
        python_callable=collect_reserve_price_cnstwk,
    )

    task_reserve_price_service = PythonOperator(
        task_id="collect_reserve_price_service",
        python_callable=collect_reserve_price_service,
    )

    task_reserve_price_foreign = PythonOperator(
        task_id="collect_reserve_price_foreign",
        python_callable=collect_reserve_price_foreign,
    )

    # 공고 - 용역
    task_notice_service = PythonOperator(
        task_id="collect_notice_service",
        python_callable=collect_notice_service,
    )

    # 공고 - 외자
    task_notice_foreign = PythonOperator(
        task_id="collect_notice_foreign",
        python_callable=collect_notice_foreign,
    )

    # 공고 - 물품
    task_notice_goods = PythonOperator(
        task_id="collect_notice_goods",
        python_callable=collect_notice_goods,
    )

    # 공고 - 물품 기초금액
    task_notice_goods_bssamt = PythonOperator(
        task_id="collect_notice_goods_bssamt",
        python_callable=collect_notice_goods_bssamt,
    )

    # 공고 - 용역 기초금액
    task_notice_service_bssamt = PythonOperator(
        task_id="collect_notice_service_bssamt",
        python_callable=collect_notice_service_bssamt,
    )

    # 공고 - 참가가능지역정보
    task_notice_region = PythonOperator(
        task_id="collect_notice_region",
        python_callable=collect_notice_region,
    )

    # =========================================================================
    # 개찰결과 수집 (4종) - 입력일시 기준
    # =========================================================================
    task_openg_result_goods = PythonOperator(
        task_id="collect_openg_result_goods",
        python_callable=collect_openg_result_goods,
    )

    task_openg_result_cnstwk = PythonOperator(
        task_id="collect_openg_result_cnstwk",
        python_callable=collect_openg_result_cnstwk,
    )

    task_openg_result_service = PythonOperator(
        task_id="collect_openg_result_service",
        python_callable=collect_openg_result_service,
    )

    task_openg_result_foreign = PythonOperator(
        task_id="collect_openg_result_foreign",
        python_callable=collect_openg_result_foreign,
    )

    # =========================================================================
    # 누락 company 증분 수집 - bid 수집 완료 후 실행
    # =========================================================================

    task_collect_missing_companies = PythonOperator(
        task_id="collect_missing_companies",
        python_callable=collect_missing_companies,
    )

    # =========================================================================
    # 국세청 사업자등록 상태조회 - company 수집 완료 후 실행
    # =========================================================================

    task_collect_nts_status = PythonOperator(
        task_id="collect_nts_status",
        python_callable=collect_nts_status,
    )

    # =========================================================================
    # 동기화 DAG 트리거 - 모든 수집 완료 후 실행
    # =========================================================================

    trigger_sync = TriggerDagRunOperator(
        task_id="trigger_sync_dag",
        trigger_dag_id="sync_g2b_data_daily",
        wait_for_completion=False,  # 동기화 완료를 기다리지 않음
    )

    # =========================================================================
    # Task 의존성
    # =========================================================================
    # 1. bid 4개 수집 완료 → 누락 company 수집
    # 2. company 수집 완료 → 국세청 상태조회
    # 3. 모든 수집 완료 → 동기화 DAG 트리거

    # bid 수집 완료 후 누락 company 수집
    [
        task_bid_data_goods,
        task_bid_data_foreign,
        task_bid_data_cnstwk,
        task_bid_data_service,
    ] >> task_collect_missing_companies

    # company 수집 완료 후 국세청 상태조회
    task_company_basic >> task_collect_nts_status

    # 모든 수집 완료 후 동기화 DAG 트리거
    [
        # 입찰공고정보서비스
        task_notice_cnstwk,
        task_notice_service,
        task_notice_foreign,
        task_notice_goods,
        task_notice_bssamt,
        task_notice_goods_bssamt,
        task_notice_service_bssamt,
        task_notice_license,
        task_notice_region,
        # 사용자정보서비스
        task_company_industry,
        task_institution,
        # 국세청 상태조회 (company 수집 후 실행)
        task_collect_nts_status,
        # 낙찰정보서비스 (예비가격 4종)
        task_reserve_price_goods,
        task_reserve_price_cnstwk,
        task_reserve_price_service,
        task_reserve_price_foreign,
        # 낙찰정보서비스 (개찰결과 4종)
        task_openg_result_goods,
        task_openg_result_cnstwk,
        task_openg_result_service,
        task_openg_result_foreign,
        # 누락 company 수집 (bid 수집 후 실행)
        task_collect_missing_companies,
    ] >> trigger_sync
