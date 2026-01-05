#!/bin/bash
# 조달업체업종정보조회 연도별 병렬 수집 스크립트
# 각 연도별로 screen 세션을 생성하여 병렬로 데이터를 수집합니다.

PROJECT_DIR="/data/dev/bid-price-analysis/api-fetcher"
SERVICE_NAME="사용자정보서비스"
OPER_NUM=3

# 수집할 연도 범위
START_YEAR=2005
END_YEAR=2025

echo "=========================================="
echo "조달업체업종정보조회 연도별 병렬 수집 시작"
echo "기간: ${START_YEAR} ~ ${END_YEAR}"
echo "=========================================="

for YEAR in $(seq $START_YEAR $END_YEAR); do
    SESSION_NAME="industry_${YEAR}"

    # 이미 해당 세션이 있으면 스킵
    if screen -list | grep -q "${SESSION_NAME}"; then
        echo "⚠️  ${SESSION_NAME} 세션이 이미 존재합니다. 스킵."
        continue
    fi

    echo "🚀 ${YEAR}년도 수집 시작 (세션: ${SESSION_NAME})"

    screen -dmS "${SESSION_NAME}" bash -c "
        cd ${PROJECT_DIR}
        source .venv/bin/activate
        python fetch_data/main.py --service '${SERVICE_NAME}' --oper ${OPER_NUM} --year ${YEAR}
        echo '✅ ${YEAR}년도 수집 완료'
        exec bash
    "

    # API 부하 방지를 위한 짧은 딜레이
    sleep 1
done

echo ""
echo "=========================================="
echo "모든 screen 세션 생성 완료!"
echo "=========================================="
echo ""
echo "세션 확인: screen -ls"
echo "세션 접속: screen -r industry_<년도>"
echo "세션 종료: screen -X -S industry_<년도> quit"
echo ""
echo "현재 실행 중인 세션:"
screen -ls | grep industry_
