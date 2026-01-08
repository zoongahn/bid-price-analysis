#!/bin/bash
# 낙찰정보서비스 예비가격상세 연도별 병렬 수집 스크립트
# 오퍼레이션 9 (물품), 10 (공사), 11 (용역), 12 (외자)에 대해 수집
#
# - 오퍼레이션 10 (공사): 2025-01 ~ 2025-11 만 수집
# - 오퍼레이션 9, 11, 12: 2010-01-01 ~ 2026-01-08 연도별 병렬 수집

PROJECT_DIR="/data/dev/bid-price-analysis/api-fetcher"
SERVICE_NAME="낙찰정보서비스"

# 수집할 연도 범위 (9, 11, 12용)
START_YEAR=2010
END_YEAR=2026

# 오퍼레이션 정보
declare -A OPER_NAME
OPER_NAME[9]="물품"
OPER_NAME[10]="공사"
OPER_NAME[11]="용역"
OPER_NAME[12]="외자"

echo "=========================================="
echo "낙찰정보서비스 예비가격상세 연도별 병렬 수집 시작"
echo "=========================================="

# ------------------------------------------------------------------
# 오퍼레이션 10 (공사): 2025-01 ~ 2025-11 단일 수집
# ------------------------------------------------------------------
OPER_NUM=10
OPER_NAME_STR=${OPER_NAME[$OPER_NUM]}
SESSION_NAME="FETCH-예비가격-${OPER_NAME_STR}_2025"

echo ""
echo "----------------------------------------"
echo "오퍼레이션 ${OPER_NUM} (${OPER_NAME_STR}) 수집 시작"
echo "기간: 2025-01-01 ~ 2025-11-30"
echo "----------------------------------------"

if screen -list | grep -q "${SESSION_NAME}"; then
    echo "  ${SESSION_NAME} 세션이 이미 존재합니다. 스킵."
else
    echo "  ${SESSION_NAME} 수집 시작"
    screen -dmS "${SESSION_NAME}" bash -c "
        cd ${PROJECT_DIR}
        PYTHONPATH=. .venv/bin/python fetch_data/main.py --service '${SERVICE_NAME}' --oper ${OPER_NUM} --start-date 2025-01-01 --end-date 2025-11-30
        echo '${OPER_NAME_STR} 2025년 수집 완료'
        exec bash
    "
    sleep 1
fi

# ------------------------------------------------------------------
# 오퍼레이션 9, 11, 12: 2010 ~ 2026 연도별 병렬 수집
# ------------------------------------------------------------------
for OPER_NUM in 9 11 12; do
    OPER_NAME_STR=${OPER_NAME[$OPER_NUM]}

    echo ""
    echo "----------------------------------------"
    echo "오퍼레이션 ${OPER_NUM} (${OPER_NAME_STR}) 수집 시작"
    echo "기간: ${START_YEAR} ~ ${END_YEAR}"
    echo "----------------------------------------"

    for YEAR in $(seq $START_YEAR $END_YEAR); do
        SESSION_NAME="FETCH-예비가격-${OPER_NAME_STR}_${YEAR}"

        # 이미 해당 세션이 있으면 스킵
        if screen -list | grep -q "${SESSION_NAME}"; then
            echo "  ${SESSION_NAME} 세션이 이미 존재합니다. 스킵."
            continue
        fi

        # 2026년은 2026-01-08까지만 수집
        if [ "$YEAR" -eq 2026 ]; then
            START_DATE="${YEAR}-01-01"
            END_DATE="2026-01-08"
        else
            START_DATE="${YEAR}-01-01"
            END_DATE="${YEAR}-12-31"
        fi

        echo "  ${OPER_NAME_STR} ${YEAR}년도 수집 시작 (세션: ${SESSION_NAME})"

        screen -dmS "${SESSION_NAME}" bash -c "
            cd ${PROJECT_DIR}
            PYTHONPATH=. .venv/bin/python fetch_data/main.py --service '${SERVICE_NAME}' --oper ${OPER_NUM} --start-date ${START_DATE} --end-date ${END_DATE}
            echo '${OPER_NAME_STR} ${YEAR}년도 수집 완료'
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
echo "세션 확인: screen -ls | grep 'FETCH-예비가격'"
echo "세션 접속: screen -r FETCH-예비가격-<공종>_<년도>"
echo "세션 종료: screen -X -S <세션명> quit"
echo ""
echo "현재 실행 중인 세션:"
screen -ls | grep "FETCH-예비가격"
