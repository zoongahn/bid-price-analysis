# bid-company FK 핸들링 프로세스

bid 테이블 동기화 시 company FK 오류를 방지하기 위한 프로세스입니다.

## 문제 상황

bid 테이블의 `bidprccorpbizrno` 컬럼이 company 테이블의 `bizno`를 참조하는데,
bid에 있는 사업자등록번호가 company에 없으면 FK 오류 발생.

## 해결 프로세스 (4단계)

### Step 1: 누락된 bizrno 조사
- **시점**: bid 동기화 전
- **내용**: bid 컬렉션(is_synced!=True)의 bizrno 중 company 테이블에 없는 것 조회
- **구현**:
  - `collect_missing_companies.py` - MongoDB 기준 조사
  - `handle_missing_companies.py` - PostgreSQL 기준 조사

### Step 2: 누락된 company API 수집 및 동기화
- **시점**: 누락된 bizrno가 있는 경우
- **내용**:
  1. 해당 bizrno로 조달업체기본정보 API 호출 → MongoDB 저장
  2. company 동기화 (MongoDB → PostgreSQL)
- **구현**:
  - `DataCollector.collect_company_by_bizno()` - API 수집
  - `CompanySyncer.sync()` - 동기화

### Step 3: 더미/테스트 bizrno → __UNKNOWN__ 처리
- **시점**: company 동기화 후에도 누락된 bizrno가 있는 경우
- **내용**: API에서 조회되지 않는 bizrno(더미/테스트 값)를 company 테이블에 `corpnm='__UNKNOWN__'`으로 INSERT
- **구현**: `MissingCompanyHandler.insert_missing_as_unknown_companies()`

### Step 4: bizrno 존재 확인 후 bid 동기화
- **시점**: bid 동기화 직전
- **내용**: bid의 모든 bizrno가 company에 존재하는지 확인 후 동기화 진행
- **구현**: `verify_all_bizrno_exist()` (sync_data_dag.py)

## 구현 현황

| 단계 | 위치 | 구현 상태 | 비고 |
|------|------|----------|------|
| Step 1 (MongoDB) | `data_collection_dag.py` → `collect_missing_companies` | ✅ 구현됨 | 데이터 수집 시 |
| Step 1 (PostgreSQL) | `handle_missing_companies.py` → `get_missing_bizno_from_psql()` | ✅ 구현됨 | 수동 실행용 |
| Step 2 (API 수집) | `DataCollector.collect_company_by_bizno()` | ✅ 구현됨 | |
| Step 2 (동기화) | `sync_data_dag.py` → `sync_company` | ✅ 구현됨 | |
| Step 3 | `sync_data_dag.py` → `handle_unknown_companies` | ✅ 구현됨 | 2025-01-07 추가 |
| Step 4 | `sync_data_dag.py` → `verify_bizrno_before_bid_sync` | ✅ 구현됨 | 2025-01-07 추가 |

## DAG 흐름

```
[data_collection_dag - 데이터 수집]
bid 수집 → collect_missing_companies (누락 company API 수집)

[sync_data_dag - 데이터 동기화]
notice → company → handle_unknown_companies → verify_bizrno → bid → ...
```

## 실행 방법 (수동)

```bash
# 1. 누락된 company 수집 (MongoDB 기준)
python sync_data/prefetch/collect_missing_companies.py

# 2. company 동기화
python -c "from sync_data.sync.syncers.company_syncer import CompanySyncer; CompanySyncer(schema='tmp').sync()"

# 3. 더미 bizrno → __UNKNOWN__ 처리
python sync_data/prefetch/handle_missing_companies.py --schema tmp --step after-company-sync

# 4. 검증
python -c "
from sync_data.prefetch.handle_missing_companies import MissingCompanyHandler
handler = MissingCompanyHandler(schema='tmp')
print(handler.get_summary())
handler.close_connections()
"
```

## 관련 파일

- `sync_data/prefetch/collect_missing_companies.py` - MongoDB 기준 누락 company 수집
- `sync_data/prefetch/handle_missing_companies.py` - PostgreSQL 기준 누락 처리
- `fetch_data/src/missing_company_collector.py` - DAG용 누락 company 수집
- `scheduler/dags/sync_data_dag.py` - 동기화 DAG
- `scheduler/dags/data_collection_dag.py` - 수집 DAG
