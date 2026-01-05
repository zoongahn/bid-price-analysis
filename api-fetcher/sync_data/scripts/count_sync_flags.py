#!/usr/bin/env python3
"""
MongoDB 컬렉션별 동기화 플래그 카운트 스크립트

Usage:
    python count_sync_flags.py                    # 모든 주요 컬렉션 조회
    python count_sync_flags.py --collection 낙찰정보  # 특정 컬렉션만 조회
    python count_sync_flags.py -c bid             # 별칭으로 조회
"""

import argparse
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../.."))

from common.init_mongodb import init_mongodb


# 컬렉션 설정: (컬렉션명, [체크할 플래그들])
COLLECTIONS = {
    # 공공데이터개방표준서비스 - 낙찰정보 (4가지 사업구분)
    "bid_goods": (
        "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품",
        ["is_synced", "notice_is_synced"],
    ),
    "bid_foreign": (
        "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자",
        ["is_synced", "notice_is_synced"],
    ),
    "bid_cnstwk": (
        "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사",
        ["is_synced", "notice_is_synced"],
    ),
    "bid_service": (
        "공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역",
        ["is_synced", "notice_is_synced"],
    ),
    "notice": (
        "입찰공고정보서비스.입찰공고목록정보에대한공사조회",
        ["is_synced"],
    ),
    "notice_base": (
        "입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회",
        ["is_synced"],
    ),
    "company": (
        "사용자정보서비스.조달업체기본정보",
        ["is_synced"],
    ),
    "company_industry": (
        "사용자정보서비스.조달업체업종정보조회",
        ["is_synced"],
    ),
    "institution": (
        "사용자정보서비스.수요기관정보조회",
        ["is_synced"],
    ),
    "reserve_price": (
        "낙찰정보서비스.개찰결과공사예비가격상세목록조회",
        ["is_synced"],
    ),
    "notice_industry": (
        "입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회",
        ["is_synced"],
    ),
}

# 별칭 매핑
ALIASES = {
    # 낙찰정보 (4가지 사업구분)
    "낙찰물품": "bid_goods",
    "낙찰-물품": "bid_goods",
    "물품": "bid_goods",
    "낙찰외자": "bid_foreign",
    "낙찰-외자": "bid_foreign",
    "외자": "bid_foreign",
    "낙찰공사": "bid_cnstwk",
    "낙찰-공사": "bid_cnstwk",
    "낙찰정보": "bid_cnstwk",
    "낙찰": "bid_cnstwk",
    "bid": "bid_cnstwk",
    "낙찰용역": "bid_service",
    "낙찰-용역": "bid_service",
    "용역": "bid_service",
    # 공고
    "공고": "notice",
    "공고정보": "notice",
    "기초금액": "notice_base",
    # 업체
    "업체": "company",
    "업체기본": "company",
    "업체업종": "company_industry",
    # 기타
    "수요기관": "institution",
    "예비가격": "reserve_price",
    "면허제한": "notice_industry",
}


def count_sync_flags(db, collection_name: str, flags: list[str]) -> dict:
    """
    컬렉션의 동기화 플래그 카운트 (인덱스 활용 최적화)

    $group aggregation을 사용하여 한 번의 인덱스 스캔으로 모든 값 카운트.

    Returns:
        {
            "total": 전체 문서 수,
            "flags": {
                "is_synced": {"true": N, "false": N, "missing": N},
                ...
            }
        }
    """
    coll = db.get_collection(collection_name)

    result = {
        "total": coll.estimated_document_count(),
        "flags": {},
    }

    for flag in flags:
        # $group으로 한번에 true/false/null 카운트 (인덱스 활용)
        pipeline = [
            {
                "$group": {
                    "_id": f"${flag}",
                    "count": {"$sum": 1}
                }
            }
        ]

        # hint로 인덱스 강제 사용 (인덱스 없으면 fallback)
        try:
            agg_result = list(coll.aggregate(pipeline, hint=f"{flag}_1", allowDiskUse=True))
        except Exception:
            # 인덱스 없으면 hint 없이 실행
            agg_result = list(coll.aggregate(pipeline, allowDiskUse=True))

        counts = {"true": 0, "false": 0, "missing": 0}
        for doc in agg_result:
            if doc["_id"] is True:
                counts["true"] = doc["count"]
            elif doc["_id"] is False:
                counts["false"] = doc["count"]
            else:  # None or missing
                counts["missing"] = doc["count"]

        result["flags"][flag] = counts

    return result


def format_number(n: int) -> str:
    """숫자를 읽기 쉬운 형식으로 포맷"""
    return f"{n:,}"


def print_collection_stats(name: str, collection_name: str, stats: dict):
    """컬렉션 통계 출력"""
    print(f"\n{'=' * 70}")
    print(f"  {name} ({collection_name})")
    print(f"{'=' * 70}")
    print(f"  총 문서 수: {format_number(stats['total'])}")
    print()

    for flag, counts in stats["flags"].items():
        total_flagged = counts["true"] + counts["false"]
        sync_pct = (counts["true"] / total_flagged * 100) if total_flagged > 0 else 0

        print(f"  [{flag}]")
        print(f"    - true:    {format_number(counts['true']):>15} ({sync_pct:.1f}%)")
        print(f"    - false:   {format_number(counts['false']):>15} ({100 - sync_pct:.1f}%)")
        if counts["missing"] > 0:
            print(f"    - missing: {format_number(counts['missing']):>15}")
        print()


def main():
    parser = argparse.ArgumentParser(
        description="MongoDB 컬렉션별 동기화 플래그 카운트"
    )
    parser.add_argument(
        "-c", "--collection",
        help="조회할 컬렉션 (bid, notice, company 등 또는 한글 별칭)",
        default=None,
    )
    parser.add_argument(
        "-l", "--list",
        action="store_true",
        help="사용 가능한 컬렉션 목록 출력",
    )
    args = parser.parse_args()

    if args.list:
        print("\n사용 가능한 컬렉션:")
        print("-" * 50)
        for key, (coll_name, flags) in COLLECTIONS.items():
            aliases = [k for k, v in ALIASES.items() if v == key]
            alias_str = f" (별칭: {', '.join(aliases)})" if aliases else ""
            print(f"  {key}{alias_str}")
            print(f"    → {coll_name}")
            print(f"    플래그: {', '.join(flags)}")
            print()
        return

    # MongoDB 연결
    print("MongoDB 연결 중...")
    server, client = init_mongodb()
    db = client.get_database("gfcon_raw")

    try:
        # 조회할 컬렉션 결정
        if args.collection:
            # 별칭 변환
            key = ALIASES.get(args.collection, args.collection)
            if key not in COLLECTIONS:
                print(f"오류: 알 수 없는 컬렉션 '{args.collection}'")
                print("사용 가능한 컬렉션: " + ", ".join(COLLECTIONS.keys()))
                sys.exit(1)
            collections_to_check = {key: COLLECTIONS[key]}
        else:
            collections_to_check = COLLECTIONS

        # 각 컬렉션 조회
        print(f"\n동기화 플래그 카운트 ({len(collections_to_check)}개 컬렉션)")

        for key, (coll_name, flags) in collections_to_check.items():
            try:
                stats = count_sync_flags(db, coll_name, flags)
                print_collection_stats(key, coll_name, stats)
            except Exception as e:
                print(f"\n오류 ({key}): {e}")

        print("=" * 70)
        print("완료")

    finally:
        client.close()


if __name__ == "__main__":
    main()
