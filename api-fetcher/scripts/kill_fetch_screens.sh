#!/bin/bash
# FETCH-로 시작하는 모든 screen 세션 종료 스크립트

echo "=========================================="
echo "FETCH- 스크린 세션 종료"
echo "=========================================="

# FETCH-로 시작하는 세션 목록 확인
SESSIONS=$(screen -ls | grep -oP '\d+\.FETCH-\S+')

if [ -z "$SESSIONS" ]; then
    echo "⚠️  종료할 FETCH- 세션이 없습니다."
    exit 0
fi

echo "종료 대상 세션:"
echo "$SESSIONS"
echo ""

# 각 세션 종료
COUNT=0
for SESSION in $SESSIONS; do
    screen -S "$SESSION" -X quit
    echo "✅ ${SESSION} 종료"
    ((COUNT++))
done

echo ""
echo "=========================================="
echo "총 ${COUNT}개 세션 종료 완료!"
echo "=========================================="

# 남은 세션 확인
echo ""
echo "남은 screen 세션:"
screen -ls
