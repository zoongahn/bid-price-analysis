#!/bin/bash
# 공공데이터개방표준서비스 낙찰정보 연도별 병렬 수집 스크립트
# 물품(1), 외자(2), 용역(5)에 대해 각 연도별로 screen 세션을 생성하여 병렬 수집
# 공사(3)는 기존에 수집 완료되어 제외

PROJECT_DIR="/data/dev/bid-price-analysis/api-fetcher"
SERVICE_NAME="공공데이터개방표준서비스"
OPER_NUM=2

# 수집할 연도 범위
START_YEAR=2010
END_YEAR=2025

# 수집할 사업구분 (공사=3 제외)
# 1=물품, 2=외자, 5=용역
BSNS_DIV_LIST=(1 2 5)

# 사업구분 코드 -> 이름 매핑
declare -A BSNS_DIV_NAME
BSNS_DIV_NAME[1]="물품"
BSNS_DIV_NAME[2]="외자"
BSNS_DIV_NAME[5]="용역"

echo "=========================================="
echo "낙찰정보 연도별 병렬 수집 시작"
echo "기간: ${START_YEAR} ~ ${END_YEAR}"
echo "사업구분: 물품(1), 외자(2), 용역(5)"
echo "=========================================="

for BSNS_DIV in "${BSNS_DIV_LIST[@]}"; do
    BSNS_NAME=${BSNS_DIV_NAME[$BSNS_DIV]}

    echo ""
    echo "----------------------------------------"
    echo "📦 ${BSNS_NAME} (bsnsDivCd=${BSNS_DIV}) 수집 시작"
    echo "----------------------------------------"

    for YEAR in $(seq $START_YEAR $END_YEAR); do
        SESSION_NAME="FETCH-${BSNS_NAME}_${YEAR}"

        # 이미 해당 세션이 있으면 스킵
        if screen -list | grep -q "${SESSION_NAME}"; then
            echo "⚠️  ${SESSION_NAME} 세션이 이미 존재합니다. 스킵."
            continue
        fi

        echo "🚀 ${BSNS_NAME} ${YEAR}년도 수집 시작 (세션: ${SESSION_NAME})"

        screen -dmS "${SESSION_NAME}" bash -c "
            cd ${PROJECT_DIR}
            PYTHONPATH=. .venv/bin/python fetch_data/main.py --service '${SERVICE_NAME}' --oper ${OPER_NUM} --year ${YEAR} --bsns-div ${BSNS_DIV}
            echo '✅ ${BSNS_NAME} ${YEAR}년도 수집 완료'
            exec bash
        "

        # API 부하 방지를 위한 짧은 딜레이
        sleep 1
    done
done

echo ""
echo "=========================================="
echo "모든 screen 세션 생성 완료!"
echo "=========================================="
echo ""
echo "세션 확인: screen -ls | grep FETCH-"
echo "세션 접속: screen -r FETCH-<사업구분>_<년도>"
echo "세션 종료: ./scripts/kill_fetch_screens.sh"
echo ""
echo "현재 실행 중인 세션:"
screen -ls | grep FETCH-
