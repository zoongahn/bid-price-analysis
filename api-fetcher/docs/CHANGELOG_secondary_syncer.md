# 보조 컬렉션 동기화 (Secondary Syncer) 변경 사항

## 개요

메인 공고가 먼저 동기화된 후, 보조 데이터(기초금액, 낙찰정보, 사업자상태 등)가 나중에 수집된 경우를 처리하는 기능 추가.

## 변경 일자
2026-01-12

---

## 문제 상황

### 기존 동기화 로직의 한계

기존 notice 동기화는 **메인 공고 컬렉션(`is_synced`)만 기준**으로 동작:

```
MongoDB                         PostgreSQL
┌──────────────────┐           ┌──────────────────┐
│ 공사조회         │           │                  │
│ is_synced=True   │──────────>│ notice 테이블    │
└──────────────────┘           │ bssamt = NULL    │ (!)
                               └──────────────────┘
┌──────────────────┐
│ 공사기초금액조회 │
│ is_synced=False  │──── X ────> 동기화 안됨!
└──────────────────┘
```

**시나리오:**
1. Day 1: 메인 공고 수집 + 동기화 (`is_synced=True`)
2. Day 3: 기초금액 API에 데이터 추가 → 수집됨
3. 메인 공고가 이미 `is_synced=True`이므로, 기초금액이 PostgreSQL에 반영되지 않음

### 영향받는 보조 컬렉션

| 테이블 | 보조 컬렉션 | synced_at 컬럼 |
|--------|------------|---------------|
| notice | 기초금액 (공사/물품/용역) | `bssamt_synced_at` |
| notice | 낙찰정보 (공사/물품/용역/외자) | `win_synced_at` |
| company | 사업자등록상태정보 | `bizstt_status_updated_at` |

---

## 해결책: SecondarySyncer

### 동작 원리

1. `sync_config.py`에서 `is_primary=False`인 모든 소스 자동 추출
2. 각 보조 컬렉션에서 `is_synced=False`인 문서 조회
3. `join_keys`(bidNtceNo, bidNtceOrd)로 PostgreSQL 레코드 찾기
4. 해당 컬렉션의 필드들만 UPDATE
5. `synced_at_column` 설정 (bssamt_synced_at, win_synced_at 등)
6. MongoDB `is_synced=True` 마킹

### 설계 특징

- **범용 설계**: sync_config.py 설정 기반으로 자동 처리
- **개별 syncer 불필요**: 하나의 SecondarySyncer로 모든 보조 컬렉션 처리
- **확장 가능**: 새 보조 컬렉션 추가 시 sync_config.py에만 설정 추가

---

## 변경 파일

### 1. 신규 파일

#### `sync_data/sync/syncers/secondary_syncer.py`

- `SecondarySyncer` 클래스 구현
- `extract_secondary_sources()`: sync_config에서 보조 컬렉션 자동 추출
- `sync_all()`: 모든 보조 컬렉션 동기화
- `sync_table(table_name)`: 특정 테이블의 보조 컬렉션만
- `sync_collection(collection_name)`: 특정 컬렉션만
- CLI 지원: `--table`, `--collection`, `--list` 옵션

### 2. 수정 파일

#### `sync_data/README.md`

- Syncer 클래스 구조 표에 `SecondarySyncer` 추가
- "보조 컬렉션 동기화" 섹션 추가 (사용법, 동작 흐름 설명)
- 디렉토리 구조에 `secondary_syncer.py` 추가

---

## 사용법

```bash
cd /data/dev/bid-price-analysis/api-fetcher

# 모든 보조 컬렉션 동기화
python -m sync_data.sync.syncers.secondary_syncer

# 특정 테이블의 보조 컬렉션만
python -m sync_data.sync.syncers.secondary_syncer --table notice

# 특정 컬렉션만
python -m sync_data.sync.syncers.secondary_syncer --collection "입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회"

# 보조 컬렉션 목록 확인
python -m sync_data.sync.syncers.secondary_syncer --list
```

---

## 발견 계기: 2025년 기초금액 수집 누락

### 분석 결과

PostgreSQL `data.notice` 테이블에서 `bssamt=NULL` 비율 조사:

| 카테고리 | 전체 기준 NULL% | 최종공고 기준 NULL% |
|---------|----------------|-------------------|
| 공사 | 22.8% | 13.8% |
| 물품 | 33.7% | 25.3% |
| 용역 | 46.4% | 38.3% |
| 외자 | 100% | 100% (API 없음) |

### 2025년 공사 기초금액 수집 누락 발견

MongoDB `inptDt` 필드 분석 결과:

```
2025년 공사 기초금액 월별 수집 현황:
  2025-01: 4,615
  2025-02: 9,758
  2025-03: 780
  2025-04 ~ 2025-10: ❌ 수집 없음 (약 8개월 공백!)
  2025-11: 5,532
  2025-12: 4,562
```

### 재수집 실행

```bash
python -m fetch_data.main \
  --service "입찰공고정보서비스" \
  --oper 6 \
  --start-date 2025-04-01 \
  --end-date 2025-10-31
```

**결과:** 67,489건 신규 수집

### 동기화

```bash
python -m sync_data.sync.syncers.secondary_syncer --table notice
```

---

## 향후 계획

1. **DAG 연동**: notice 동기화 후 자동으로 보조 컬렉션 동기화 실행
2. **모니터링**: 보조 컬렉션 `is_synced=False` 건수 모니터링 추가
3. **스케줄링**: 일일 배치로 보조 컬렉션 동기화 자동 실행
