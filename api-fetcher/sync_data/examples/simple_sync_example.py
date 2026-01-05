"""
SimpleSync 사용 예시

설정 파일 없이 MongoDB 컬렉션을 PostgreSQL 테이블로 1:1 동기화하는 예시입니다.
"""

from sync_data.sync.simple_sync import sync_collection_to_table, SimpleSync


def example1_basic_sync():
    """
    예시 1: 기본 사용법

    단일 Primary Key를 가진 테이블 동기화
    """
    print("\n" + "=" * 80)
    print("예시 1: 기본 동기화 (company)")
    print("=" * 80 + "\n")

    sync_collection_to_table(
        mongo_collection_name="사용자정보서비스.조달업체기본정보",
        psql_table_name="company",
        psql_pk=("bizno",),
        batch_size=10000,
    )


def example2_composite_key():
    """
    예시 2: 복합 Primary Key

    여러 컬럼으로 구성된 PK를 가진 테이블 동기화
    """
    print("\n" + "=" * 80)
    print("예시 2: 복합 PK 동기화 (notice)")
    print("=" * 80 + "\n")

    sync_collection_to_table(
        mongo_collection_name="입찰공고정보서비스.입찰공고목록정보에대한공사조회",
        psql_table_name="notice_simple",  # 테스트용 별도 테이블
        psql_pk=("bidntceno", "bidntceord"),
        batch_size=5000,
    )


def example3_field_mapping():
    """
    예시 3: 필드명 매핑

    MongoDB 필드명과 PostgreSQL 컬럼명이 다를 때
    """
    print("\n" + "=" * 80)
    print("예시 3: 필드명 매핑 (reserve_price_range)")
    print("=" * 80 + "\n")

    sync_collection_to_table(
        mongo_collection_name="낙찰정보서비스.개찰결과공사예비가격상세목록조회",
        psql_table_name="reserve_price_range",
        psql_pk=("bidntceno", "bidntceord", "range_no"),
        field_aliases=[
            # (PostgreSQL 컬럼명, MongoDB 필드명)
            ("range_no", "compnoRsrvtnPrceSno"),
        ],
        batch_size=10000,
    )


def example4_custom_sync_flag():
    """
    예시 4: 커스텀 동기화 플래그

    같은 컬렉션을 여러 테이블로 동기화할 때 플래그를 다르게 설정
    """
    print("\n" + "=" * 80)
    print("예시 4: 커스텀 동기화 플래그")
    print("=" * 80 + "\n")

    # 첫 번째 테이블: is_synced_table1 플래그 사용
    sync_collection_to_table(
        mongo_collection_name="공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보",
        psql_table_name="bid_table1",
        psql_pk=("bidntceno", "bidntceord", "bidprccorpbizrno"),
        sync_flag="is_synced_table1",  # 커스텀 플래그
    )

    # 두 번째 테이블: is_synced_table2 플래그 사용
    sync_collection_to_table(
        mongo_collection_name="공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보",
        psql_table_name="bid_table2",
        psql_pk=("bidntceno", "bidntceord", "bidprccorpbizrno"),
        sync_flag="is_synced_table2",  # 다른 플래그
    )


def example5_class_usage():
    """
    예시 5: SimpleSync 클래스 직접 사용

    더 세밀한 제어가 필요할 때
    """
    print("\n" + "=" * 80)
    print("예시 5: SimpleSync 클래스 직접 사용")
    print("=" * 80 + "\n")

    syncer = None
    try:
        syncer = SimpleSync(
            mongo_collection_name="사용자정보서비스.조달업체기본정보",
            psql_table_name="company",
            psql_pk=("bizno",),
            batch_size=10000,
            sync_flag="is_synced",
        )

        # 동기화 실행
        syncer.sync()

        # 추가 작업 가능...

    except Exception as e:
        print(f"❌ 오류 발생: {e}")
    finally:
        if syncer:
            syncer.close()


def example6_new_collection():
    """
    예시 6: 새로운 컬렉션 동기화

    기존에 없던 새로운 MongoDB 컬렉션을 PostgreSQL로 동기화
    """
    print("\n" + "=" * 80)
    print("예시 6: 새 컬렉션 동기화")
    print("=" * 80 + "\n")

    # 가상의 새로운 컬렉션 예시
    # 실제 사용 시 컬렉션명과 테이블 스키마를 맞춰주세요
    sync_collection_to_table(
        mongo_collection_name="신규서비스.신규데이터",
        psql_table_name="new_table",
        psql_pk=("id",),
        batch_size=10000,
    )


if __name__ == "__main__":
    print("\n" + "=" * 80)
    print("SimpleSync 사용 예시")
    print("=" * 80)
    print("\n⚠️  이 스크립트는 예시용입니다.")
    print("⚠️  실제 실행 전에 PostgreSQL 테이블이 생성되어 있는지 확인하세요!\n")

    # 원하는 예시 함수를 주석 해제하여 실행하세요
    # example1_basic_sync()
    # example2_composite_key()
    # example3_field_mapping()
    # example4_custom_sync_flag()
    # example5_class_usage()
    # example6_new_collection()

    print("\n실행할 예시 함수의 주석을 해제하세요.\n")
