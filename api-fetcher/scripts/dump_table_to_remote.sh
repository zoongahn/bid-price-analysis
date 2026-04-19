#!/bin/bash
# 특정 테이블을 원격 서버로 덤프/전송하는 스크립트
# ⚠️  주의: 내부망(LAN) 전용 스크립트입니다. 192.168.0.x 네트워크에서만 동작합니다.
#
# 사용법: ./dump_table_to_remote.sh <src_schema.table> [dst_schema.table] [method]
# 예시: ./dump_table_to_remote.sh data.company                          # 동일 스키마로 전송
#       ./dump_table_to_remote.sh data.company public.company           # 다른 스키마로 전송
#       ./dump_table_to_remote.sh data.company public.company scp       # 다른 스키마 + scp 방식

set -e

# ============ 설정 ============
# 소스 DB (로컬)
SRC_HOST="localhost"
SRC_PORT="5432"
SRC_DB="GFCON_PSQL"
SRC_USER="postgres"
SRC_PASSWORD="0000"

# 대상 서버 (SSH) - 내부망 전용
REMOTE_HOST="192.168.0.101"
REMOTE_USER="ajh"
REMOTE_SSH_PORT="22"
REMOTE_SSH_KEY="$HOME/.ssh/gfcon-ai-ajh"

# 대상 DB (원격)
DST_HOST="localhost"
DST_PORT="5432"
DST_DB="GFCON"
DST_USER="postgres"
DST_PASSWORD="0000"

# 덤프 디렉토리
DUMP_DIR="/tmp"
# ==============================

# 인자 파싱
SRC_TABLE="$1"

# 두 번째 인자가 method인지 dst_table인지 판별
if [[ "$2" == "pipe" || "$2" == "scp" || "$2" == "rsync" || -z "$2" ]]; then
    DST_TABLE="$SRC_TABLE"
    METHOD="${2:-pipe}"
else
    DST_TABLE="$2"
    METHOD="${3:-pipe}"
fi

if [ -z "$SRC_TABLE" ]; then
    echo "사용법: $0 <src_schema.table> [dst_schema.table] [method]"
    echo "  method: pipe (기본값, 가장 빠름), scp, rsync"
    echo ""
    echo "예시:"
    echo "  $0 data.company                        # 동일 스키마로 전송"
    echo "  $0 data.company public.company         # 다른 스키마로 전송"
    echo "  $0 data.company public.company scp     # 다른 스키마 + scp 방식"
    exit 1
fi

# 소스 스키마와 테이블 분리
SRC_SCHEMA=$(echo "$SRC_TABLE" | cut -d'.' -f1)
SRC_TABLE_NAME=$(echo "$SRC_TABLE" | cut -d'.' -f2)

# 대상 스키마와 테이블 분리
DST_SCHEMA=$(echo "$DST_TABLE" | cut -d'.' -f1)
DST_TABLE_NAME=$(echo "$DST_TABLE" | cut -d'.' -f2)

# SSH 옵션 구성
SSH_OPTS="-p $REMOTE_SSH_PORT"
if [ -n "$REMOTE_SSH_KEY" ]; then
    SSH_OPTS="$SSH_OPTS -i $REMOTE_SSH_KEY"
fi

echo "=========================================="
echo "테이블 덤프 및 전송"
echo "=========================================="
echo "소스: $SRC_HOST:$SRC_PORT/$SRC_DB ($SRC_TABLE)"
echo "대상: $REMOTE_HOST -> $DST_HOST:$DST_PORT/$DST_DB ($DST_TABLE)"
echo "방식: $METHOD"
echo "=========================================="

case "$METHOD" in
    pipe)
        # 가장 빠른 방식: pg_dump | ssh | psql 파이프라인
        echo "[1/1] 파이프라인으로 직접 전송 중..."

        PGPASSWORD="${SRC_PASSWORD}" pg_dump \
            -h "$SRC_HOST" \
            -p "$SRC_PORT" \
            -U "$SRC_USER" \
            -d "$SRC_DB" \
            -t "$SRC_TABLE" \
            --no-owner \
            --no-acl \
            --clean \
            --if-exists \
        | sed "s/${SRC_SCHEMA}\./${DST_SCHEMA}./g; s/SCHEMA ${SRC_SCHEMA}/SCHEMA ${DST_SCHEMA}/g" \
        | ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" \
            "PGPASSWORD='${DST_PASSWORD}' psql \
                -h '$DST_HOST' \
                -p '$DST_PORT' \
                -U '$DST_USER' \
                -d '$DST_DB' \
                -v ON_ERROR_STOP=1"
        ;;

    scp)
        # 덤프 파일 생성 후 SCP 전송
        DUMP_FILE="$DUMP_DIR/${SRC_SCHEMA}_${SRC_TABLE_NAME}_$(date +%Y%m%d_%H%M%S).sql"

        echo "[1/3] 덤프 파일 생성 중: $DUMP_FILE"
        PGPASSWORD="${SRC_PASSWORD}" pg_dump \
            -h "$SRC_HOST" \
            -p "$SRC_PORT" \
            -U "$SRC_USER" \
            -d "$SRC_DB" \
            -t "$SRC_TABLE" \
            --no-owner \
            --no-acl \
            --clean \
            --if-exists \
        | sed "s/${SRC_SCHEMA}\./${DST_SCHEMA}./g; s/SCHEMA ${SRC_SCHEMA}/SCHEMA ${DST_SCHEMA}/g" \
        > "$DUMP_FILE"

        echo "[2/3] 원격 서버로 전송 중..."
        scp $SSH_OPTS "$DUMP_FILE" "$REMOTE_USER@$REMOTE_HOST:$DUMP_DIR/"

        echo "[3/3] 원격 서버에서 복원 중..."
        REMOTE_DUMP_FILE="$DUMP_DIR/$(basename $DUMP_FILE)"
        ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" \
            "PGPASSWORD='${DST_PASSWORD}' psql \
                -h '$DST_HOST' \
                -p '$DST_PORT' \
                -U '$DST_USER' \
                -d '$DST_DB' \
                -f '$REMOTE_DUMP_FILE' && rm -f '$REMOTE_DUMP_FILE'"

        # 로컬 덤프 파일 삭제
        rm -f "$DUMP_FILE"
        ;;

    rsync)
        # 덤프 파일 생성 후 rsync 전송 (대용량/재시도 필요 시)
        DUMP_FILE="$DUMP_DIR/${SRC_SCHEMA}_${SRC_TABLE_NAME}_$(date +%Y%m%d_%H%M%S).sql"

        echo "[1/3] 덤프 파일 생성 중: $DUMP_FILE"
        PGPASSWORD="${SRC_PASSWORD}" pg_dump \
            -h "$SRC_HOST" \
            -p "$SRC_PORT" \
            -U "$SRC_USER" \
            -d "$SRC_DB" \
            -t "$SRC_TABLE" \
            --no-owner \
            --no-acl \
            --clean \
            --if-exists \
        | sed "s/${SRC_SCHEMA}\./${DST_SCHEMA}./g; s/SCHEMA ${SRC_SCHEMA}/SCHEMA ${DST_SCHEMA}/g" \
        > "$DUMP_FILE"

        echo "[2/3] rsync로 전송 중..."
        rsync -avz --progress \
            -e "ssh $SSH_OPTS" \
            "$DUMP_FILE" \
            "$REMOTE_USER@$REMOTE_HOST:$DUMP_DIR/"

        echo "[3/3] 원격 서버에서 복원 중..."
        REMOTE_DUMP_FILE="$DUMP_DIR/$(basename $DUMP_FILE)"
        ssh $SSH_OPTS "$REMOTE_USER@$REMOTE_HOST" \
            "PGPASSWORD='${DST_PASSWORD}' psql \
                -h '$DST_HOST' \
                -p '$DST_PORT' \
                -U '$DST_USER' \
                -d '$DST_DB' \
                -f '$REMOTE_DUMP_FILE' && rm -f '$REMOTE_DUMP_FILE'"

        # 로컬 덤프 파일 삭제
        rm -f "$DUMP_FILE"
        ;;

    *)
        echo "알 수 없는 방식: $METHOD"
        echo "사용 가능: pipe, scp, rsync"
        exit 1
        ;;
esac

echo "=========================================="
echo "완료!"
echo "=========================================="
