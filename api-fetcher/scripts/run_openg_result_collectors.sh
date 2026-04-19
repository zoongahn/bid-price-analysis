#!/bin/bash
# 개찰결과 API 수집기 실행 스크립트 (DataCollector 사용)
# 2010년~2026년, 4개 카테고리 (물품/공사/용역/외자)
#
# DataCollector의 재시도 로직을 활용하여 타임아웃 발생 시에도 누락 없이 수집
#
# 카테고리별 operation_number:
#   - 물품: 5 (개찰결과물품목록조회)
#   - 공사: 6 (개찰결과공사목록조회)
#   - 용역: 7 (개찰결과용역목록조회)
#   - 외자: 8 (개찰결과외자목록조회)

cd /data/dev/bid-price-analysis/api-fetcher
source .venv/bin/activate

# 카테고리 -> operation_number 매핑
declare -A CATEGORY_OP_MAP
CATEGORY_OP_MAP["물품"]=5
CATEGORY_OP_MAP["공사"]=6
CATEGORY_OP_MAP["용역"]=7
CATEGORY_OP_MAP["외자"]=8

CATEGORIES=("물품" "공사" "용역" "외자")
START_YEAR=2010
END_YEAR=2026

for year in $(seq $START_YEAR $END_YEAR); do
    for category in "${CATEGORIES[@]}"; do
        op_num=${CATEGORY_OP_MAP[$category]}
        session_name="FETCH-개찰결과-${category}_${year}"

        echo "Starting: $session_name (operation_number=$op_num)"

        screen -dmS "$session_name" bash -c "
            cd /data/dev/bid-price-analysis/api-fetcher
            source .venv/bin/activate
            export DJANGO_ENV=local

            python -c \"
from fetch_data.src.data_collector import DataCollector

collector = DataCollector(
    service_name='낙찰정보서비스',
    operation_number=$op_num,
    year=$year,
)
collector.execute()
print('수집 완료: $category $year')
\"
            echo '완료: $session_name'
            exec bash
        "

        # 세션 간 약간의 딜레이
        sleep 0.3
    done
done

echo ""
echo "=== 실행된 세션 목록 ==="
screen -ls | grep "개찰결과" | wc -l
echo "개 세션 실행됨"
