# Airflow 스케줄러 - 나라장터 데이터 자동 수집

매일 새벽 2시에 나라장터 공공데이터를 자동 수집하는 Airflow DAG입니다.

---

## 📁 디렉토리 구조

```
scheduler/
├── README.md                # 이 파일
├── airflow.cfg              # Airflow 설정
├── airflow.db               # Airflow 메타데이터 (SQLite)
├── start_scheduler.sh       # 스케줄러 시작 스크립트
├── webserver_config.py      # 웹서버 설정
├── dags/
│   ├── data_collection_dag.py  # 데이터 수집 DAG
│   └── sync_data_dag.py        # 데이터 동기화 DAG
├── logs/                    # Airflow 로그
├── config/
└── plugins/
```

---

## 🎯 DAG 정보

| 항목 | 값 |
|------|-----|
| DAG ID | `collect_g2b_data_daily` |
| 스케줄 | `0 17 * * *` (UTC 17:00 = KST 02:00, 매일 새벽 2시) |
| 실행 방식 | 17개 Task 병렬 실행 → 완료 후 sync DAG 트리거 |
| Executor | SequentialExecutor |
| catchup | False (과거 미실행분 실행 안함) |

---

## 📋 Task 목록 및 수집 설정

### 입찰공고정보서비스 (9개 Task)

| Task ID | 오퍼레이션 | op# | 대분류 | 수집 기준 필드 |
|---------|-----------|-----|--------|---------------|
| collect_notice_cnstwk | 입찰공고목록정보에대한공사조회 | 1 | 공사 | `bidNtceDt` |
| collect_notice_service | 입찰공고목록정보에대한용역조회 | 2 | 용역 | `bidNtceDt` |
| collect_notice_foreign | 입찰공고목록정보에대한외자조회 | 3 | 외자 | `bidNtceDt` |
| collect_notice_goods | 입찰공고목록정보에대한물품조회 | 4 | 물품 | `bidNtceDt` |
| collect_notice_goods_bssamt | 입찰공고목록정보에대한물품기초금액조회 | 5 | 물품 | `bssamtOpenDt` |
| collect_notice_bssamt | 입찰공고목록정보에대한공사기초금액조회 | 6 | 공사 | `bssamtOpenDt` |
| collect_notice_service_bssamt | 입찰공고목록정보에대한용역기초금액조회 | 7 | 용역 | `bssamtOpenDt` |
| collect_notice_license | 입찰공고목록정보에대한면허제한정보조회 | 15 | 전체 | `rgstDt` |
| collect_notice_region | 입찰공고목록정보에대한참가가능지역정보조회 | 16 | 전체 | `rgstDt` |

### 사용자정보서비스 (3개 Task)

| Task ID | 오퍼레이션 | op# | 수집 기준 필드 |
|---------|-----------|-----|---------------|
| collect_institution | 수요기관정보조회 | 1 | `chgDt` |
| collect_company_basic | 조달업체기본정보 | 2 | `chgDt` |
| collect_company_industry | 조달업체업종정보조회 | 3 | `systmChgDt` |

### 낙찰정보서비스 (1개 Task)

| Task ID | 오퍼레이션 | op# | 수집 기준 필드 |
|---------|-----------|-----|---------------|
| collect_reserve_price | 개찰결과공사예비가격상세목록조회 | 10 | `inptDt` |

### 공공데이터개방표준서비스 - 투찰/낙찰정보 (4개 Task)

| Task ID | 오퍼레이션 | op# | bsns_div_cd | MongoDB 컬렉션 |
|---------|-----------|-----|-------------|----------------|
| collect_bid_data_goods | 데이터셋개방표준에따른낙찰정보 | 2 | 1 (물품) | `...낙찰정보-물품` |
| collect_bid_data_foreign | 데이터셋개방표준에따른낙찰정보 | 2 | 2 (외자) | `...낙찰정보-외자` |
| collect_bid_data_cnstwk | 데이터셋개방표준에따른낙찰정보 | 2 | 3 (공사) | `...낙찰정보-공사` |
| collect_bid_data_service | 데이터셋개방표준에따른낙찰정보 | 2 | 5 (용역) | `...낙찰정보-용역` |

> **Note**: 투찰/낙찰정보는 사업구분코드(bsns_div_cd)별로 분리하여 4개 컬렉션에 저장됩니다.

### 후속 처리 (1개 Task)

| Task ID | 설명 |
|---------|------|
| trigger_sync_dag | 모든 수집 완료 후 `sync_g2b_data_daily` DAG 트리거 |

---

## 📅 컬렉션별 날짜 필드 형식

### 입찰공고정보서비스

| 컬렉션 | 수집 기준 필드 | 날짜 형식 | 조회 예시 |
|--------|---------------|-----------|----------|
| 입찰공고정보서비스.입찰공고목록정보에대한공사조회 | `bidNtceDt` | `YYYY-MM-DD HH:MM:SS` | `{bidNtceDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한용역조회 | `bidNtceDt` | `YYYY-MM-DD HH:MM:SS` | `{bidNtceDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한외자조회 | `bidNtceDt` | `YYYY-MM-DD HH:MM:SS` | `{bidNtceDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한물품조회 | `bidNtceDt` | `YYYY-MM-DD HH:MM:SS` | `{bidNtceDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회 | `bssamtOpenDt` | `YYYY-MM-DD HH:MM:SS` | `{bssamtOpenDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한물품기초금액조회 | `bssamtOpenDt` | `YYYY-MM-DD HH:MM:SS` | `{bssamtOpenDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한용역기초금액조회 | `bssamtOpenDt` | `YYYY-MM-DD HH:MM:SS` | `{bssamtOpenDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회 | `rgstDt` | `YYYY-MM-DD HH:MM:SS` | `{rgstDt: {$regex: "^2025-12-13"}}` |
| 입찰공고정보서비스.입찰공고목록정보에대한참가가능지역정보조회 | `rgstDt` | `YYYY-MM-DD HH:MM:SS` | `{rgstDt: {$regex: "^2025-12-13"}}` |

### 사용자정보서비스

| 컬렉션 | 수집 기준 필드 | 날짜 형식 | 조회 예시 |
|--------|---------------|-----------|----------|
| 사용자정보서비스.수요기관정보조회 | `chgDt` | `YYYY-MM-DD HH:MM:SS` | `{chgDt: {$regex: "^2025-12-13"}}` |
| 사용자정보서비스.조달업체기본정보 | `chgDt` | `YYYY-MM-DD HH:MM:SS` | `{chgDt: {$regex: "^2025-12-13"}}` |
| 사용자정보서비스.조달업체업종정보조회 | `systmChgDt` | `YYYY-MM-DD HH:MM:SS` | `{systmChgDt: {$regex: "^2025-12-13"}}` |

### 낙찰정보서비스

| 컬렉션 | 수집 기준 필드 | 날짜 형식 | 조회 예시 |
|--------|---------------|-----------|----------|
| 낙찰정보서비스.개찰결과공사예비가격상세목록조회 | `inptDt` | `YYYY-MM-DD HH:MM:SS` | `{inptDt: {$regex: "^2025-12-13"}}` |

### 공공데이터개방표준서비스 (사업구분별 분리)

| 컬렉션 | 수집 기준 필드 | 날짜 형식 | 조회 예시 |
|--------|---------------|-----------|----------|
| 공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품 | `opengDate` | `YYYY-MM-DD` | `{opengDate: "2025-12-13"}` |
| 공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자 | `opengDate` | `YYYY-MM-DD` | `{opengDate: "2025-12-13"}` |
| 공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사 | `opengDate` | `YYYY-MM-DD` | `{opengDate: "2025-12-13"}` |
| 공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역 | `opengDate` | `YYYY-MM-DD` | `{opengDate: "2025-12-13"}` |

---

## 🚀 실행 방법

### 1. 스케줄러 시작 (필수)

```bash
cd /data/dev/bid-price-analysis/api-fetcher

# 백그라운드 실행
nohup scheduler/start_scheduler.sh > scheduler/logs/scheduler_run.log 2>&1 &

# 또는 screen 사용
screen -S airflow-scheduler
scheduler/start_scheduler.sh
# Ctrl+A, D로 detach
```

### 2. 웹서버 시작 (선택 - 모니터링용)

```bash
AIRFLOW_HOME=/data/dev/bid-price-analysis/api-fetcher/scheduler \
nohup .venv/bin/airflow webserver --port 8080 > scheduler/logs/webserver_run.log 2>&1 &
```

- 접속 URL: `http://localhost:8080`
- 계정: `admin` (비밀번호 분실 시 재설정 필요)

### 3. 프로세스 확인

```bash
ps aux | grep "airflow" | grep -v grep
```

---

## 🔧 CLI 명령어

```bash
# 환경 변수 설정 (모든 명령어 실행 전 필요)
export AIRFLOW_HOME=/data/dev/bid-price-analysis/api-fetcher/scheduler

# DAG 목록 확인
airflow dags list

# DAG 활성화/비활성화
airflow dags unpause collect_g2b_data_daily
airflow dags pause collect_g2b_data_daily

# DAG 수동 트리거
airflow dags trigger collect_g2b_data_daily

# DAG 실행 기록 확인
airflow dags list-runs -d collect_g2b_data_daily

# 특정 날짜로 단일 Task 테스트 (DB 기록 안함)
airflow tasks test collect_g2b_data_daily collect_notice_cnstwk 2024-12-01

# 실패한 Task 재실행 (clear)
airflow tasks clear collect_g2b_data_daily -s 2025-12-13 -e 2025-12-14 -y

# 사용자 비밀번호 재설정
airflow users reset-password -u admin
```

---

## ⚠️ 주의사항

### 1. PATH 설정 필수

SequentialExecutor가 subprocess로 task를 실행할 때 `airflow` 명령어를 찾을 수 있어야 합니다.

```bash
# 심볼릭 링크 생성 (최초 1회)
sudo ln -s /data/dev/bid-price-analysis/api-fetcher/.venv/bin/airflow /usr/local/bin/airflow
```

### 2. Airflow 환경에서 colorlog 비활성화

Airflow 로깅과 colorlog가 충돌하여 RecursionError가 발생할 수 있습니다.
`common/logger.py`에서 `AIRFLOW_CTX_DAG_ID` 환경변수 감지 시 colorlog를 비활성화합니다.

### 3. airflow.db 권한

```bash
# gfdev 그룹 사용자가 쓸 수 있도록 권한 설정
chmod 664 scheduler/airflow.db
```

### 4. Example DAG 비활성화

`airflow.cfg`에서 설정:
```ini
load_examples = False
```

---

## 🐛 트러블슈팅

### Q1. Task가 up_for_retry / restarting 상태로 반복됨

**원인**: colorlog와 Airflow 로깅 충돌 (RecursionError)

**해결**: `common/logger.py`에서 Airflow 환경 감지하여 colorlog 비활성화
```python
if name == "application" and not os.getenv("AIRFLOW_CTX_DAG_ID"):
    # colorlog 설정
```

### Q2. FileNotFoundError: 'airflow' not found

**원인**: PATH에 airflow 바이너리 없음

**해결**:
```bash
sudo ln -s /data/dev/bid-price-analysis/api-fetcher/.venv/bin/airflow /usr/local/bin/airflow
```

### Q3. airflow.db readonly 에러

**원인**: DB 파일 권한 문제

**해결**:
```bash
chmod 664 scheduler/airflow.db
```

### Q4. DAG가 목록에 안 보임

**원인**: DAG 파일 import 에러

**확인**:
```bash
airflow dags list-import-errors
```

---

## 📊 수집 현황 확인 (MongoDB)

```javascript
// 특정 날짜 수집 현황 확인 (공사조회 - bidNtceDt 기준)
db.getCollection("입찰공고정보서비스.입찰공고목록정보에대한공사조회").countDocuments({
  bidNtceDt: { $regex: "^2025-12-13" }
})

// 최근 1시간 내 추가된 문서 수 확인
var oneHourAgo = new Date(Date.now() - 60*60*1000);
var oid = ObjectId.fromDate(oneHourAgo);
db.getCollection("입찰공고정보서비스.입찰공고목록정보에대한공사조회").countDocuments({
  _id: { $gte: oid }
})
```

---

## 🔗 관련 파일

- `dags/data_collection_dag.py` - DAG 정의
- `../fetch_data/src/data_collector.py` - 데이터 수집 로직
- `../fetch_data/src/params_builder.py` - API 파라미터 설정 (inqryDiv 등)
- `../common/logger.py` - 로깅 설정 (colorlog 비활성화 로직)
