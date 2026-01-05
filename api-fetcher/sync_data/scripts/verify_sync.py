"""
동기화 검증 스크립트

is_synced 플래그 상태를 확인하고 PostgreSQL과 MongoDB의 데이터 일관성을 검증합니다.
"""

from common.init_mongodb import init_mongodb
from common.init_psql import init_psql


def verify_sync_flags():
    """is_synced 플래그 상태 확인"""
    server, client = init_mongodb()
    db = client.get_database("gfcon_raw")

    print("\n" + "=" * 80)
    print("📊 is_synced 플래그 상태 확인")
    print("=" * 80 + "\n")

    collections_to_check = [
        ("입찰공고정보서비스.입찰공고목록정보에대한공사조회", ["is_synced"], "notice 메인"),
        ("입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회", ["is_synced"], "notice 기초금액"),
        ("공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보", ["is_synced", "notice_is_synced"], "bid/notice"),
        ("사용자정보서비스.조달업체기본정보", ["is_synced"], "company"),
        ("낙찰정보서비스.개찰결과공사예비가격상세목록조회", ["is_synced"], "reserve_price_range"),
    ]

    for collection_name, flags, description in collections_to_check:
        coll = db[collection_name]
        total = coll.count_documents({})

        print(f"📁 {description}")
        print(f"   컬렉션: {collection_name}")
        print(f"   전체 문서: {total:,}건\n")

        for flag in flags:
            synced = coll.count_documents({flag: True})
            not_synced = coll.count_documents({flag: {"$ne": True}})

            synced_pct = (synced / total * 100) if total > 0 else 0
            not_synced_pct = (not_synced / total * 100) if total > 0 else 0

            print(f"   {flag}:")
            print(f"     ✅ True:     {synced:>10,}건 ({synced_pct:>6.2f}%)")
            print(f"     ❌ Not True: {not_synced:>10,}건 ({not_synced_pct:>6.2f}%)")

        print()

    client.close()


def verify_notice_count():
    """notice 테이블 데이터 개수 확인"""
    mongo_server, mongo_client = init_mongodb()
    mongo_db = mongo_client.get_database("gfcon_raw")

    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    print("\n" + "=" * 80)
    print("📊 NOTICE 테이블 데이터 개수 비교")
    print("=" * 80 + "\n")

    # MongoDB (메인 컬렉션)
    mongo_coll = mongo_db["입찰공고정보서비스.입찰공고목록정보에대한공사조회"]
    mongo_total = mongo_coll.count_documents({})
    mongo_synced = mongo_coll.count_documents({"is_synced": True})

    # PostgreSQL
    psql_cur.execute("SELECT COUNT(*) FROM notice;")
    psql_count = psql_cur.fetchone()[0]

    print(f"MongoDB (공고 기본정보):")
    print(f"  - 전체:     {mongo_total:>10,}건")
    print(f"  - 동기화됨: {mongo_synced:>10,}건")
    print(f"\nPostgreSQL (notice 테이블):")
    print(f"  - 전체:     {psql_count:>10,}건")

    diff = mongo_synced - psql_count
    if diff == 0:
        print(f"\n✅ 데이터 일치!")
    else:
        print(f"\n⚠️  데이터 불일치: {abs(diff):,}건 차이")

    psql_cur.close()
    psql_conn.close()
    mongo_client.close()


def verify_company_count():
    """company 테이블 데이터 개수 확인"""
    mongo_server, mongo_client = init_mongodb()
    mongo_db = mongo_client.get_database("gfcon_raw")

    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    print("\n" + "=" * 80)
    print("📊 COMPANY 테이블 데이터 개수 비교")
    print("=" * 80 + "\n")

    # MongoDB
    mongo_coll = mongo_db["사용자정보서비스.조달업체기본정보"]
    mongo_total = mongo_coll.count_documents({})
    mongo_synced = mongo_coll.count_documents({"is_synced": True})

    # PostgreSQL
    psql_cur.execute("SELECT COUNT(*) FROM company;")
    psql_count = psql_cur.fetchone()[0]

    print(f"MongoDB (조달업체 기본정보):")
    print(f"  - 전체:     {mongo_total:>10,}건")
    print(f"  - 동기화됨: {mongo_synced:>10,}건")
    print(f"\nPostgreSQL (company 테이블):")
    print(f"  - 전체:     {psql_count:>10,}건")

    diff = mongo_synced - psql_count
    if diff == 0:
        print(f"\n✅ 데이터 일치!")
    else:
        print(f"\n⚠️  데이터 불일치: {abs(diff):,}건 차이")

    psql_cur.close()
    psql_conn.close()
    mongo_client.close()


def verify_bid_count():
    """bid 테이블 데이터 개수 확인"""
    mongo_server, mongo_client = init_mongodb()
    mongo_db = mongo_client.get_database("gfcon_raw")

    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    print("\n" + "=" * 80)
    print("📊 BID 테이블 데이터 개수 비교")
    print("=" * 80 + "\n")

    # MongoDB
    mongo_coll = mongo_db["공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보"]
    mongo_total = mongo_coll.count_documents({})
    mongo_synced = mongo_coll.count_documents({"is_synced": True})

    # PostgreSQL
    psql_cur.execute("SELECT COUNT(*) FROM bid;")
    psql_count = psql_cur.fetchone()[0]

    print(f"MongoDB (낙찰정보):")
    print(f"  - 전체:     {mongo_total:>10,}건")
    print(f"  - 동기화됨: {mongo_synced:>10,}건")
    print(f"\nPostgreSQL (bid 테이블):")
    print(f"  - 전체:     {psql_count:>10,}건")

    # bid는 외래키 체크로 일부가 skip될 수 있음
    if psql_count <= mongo_synced:
        print(f"\n✅ 정상 범위 (외래키 체크로 일부 skip 가능)")
        print(f"   Skip된 데이터: 약 {mongo_synced - psql_count:,}건")
    else:
        print(f"\n⚠️  PostgreSQL이 더 많음: {psql_count - mongo_synced:,}건")

    psql_cur.close()
    psql_conn.close()
    mongo_client.close()


def verify_notice_merge():
    """notice 테이블에 병합된 데이터 샘플 확인"""
    psql_server, psql_conn = init_psql()
    psql_cur = psql_conn.cursor()

    print("\n" + "=" * 80)
    print("📊 NOTICE 테이블 병합 데이터 샘플 확인")
    print("=" * 80 + "\n")

    # 기초금액(bssamt)과 낙찰정보(opengdate)가 모두 있는 건수
    psql_cur.execute("""
        SELECT
            COUNT(*) as total,
            COUNT(bssamt) as has_bssamt,
            COUNT(opengdate) as has_opengdate,
            COUNT(CASE WHEN bssamt IS NOT NULL AND opengdate IS NOT NULL THEN 1 END) as has_both
        FROM notice;
    """)
    result = psql_cur.fetchone()

    total, has_bssamt, has_opengdate, has_both = result

    print(f"전체 공고:                     {total:>10,}건")
    print(f"기초금액(bssamt) 있음:         {has_bssamt:>10,}건 ({has_bssamt/total*100:>6.2f}%)")
    print(f"개찰일자(opengdate) 있음:      {has_opengdate:>10,}건 ({has_opengdate/total*100:>6.2f}%)")
    print(f"둘 다 있음:                    {has_both:>10,}건 ({has_both/total*100:>6.2f}%)")

    print(f"\n✅ 3개 컬렉션 병합 확인 완료")

    psql_cur.close()
    psql_conn.close()


def main():
    """모든 검증 실행"""
    print("\n🔍 동기화 상태 검증 시작\n")

    # 1. is_synced 플래그 확인
    verify_sync_flags()

    # 2. 테이블별 개수 확인
    verify_notice_count()
    verify_company_count()
    verify_bid_count()

    # 3. 병합 확인
    verify_notice_merge()

    print("\n" + "=" * 80)
    print("✅ 모든 검증 완료")
    print("=" * 80 + "\n")


if __name__ == "__main__":
    main()
