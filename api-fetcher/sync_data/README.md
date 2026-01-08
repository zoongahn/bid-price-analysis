# sync_data - MongoDB → PostgreSQL 동기화 시스템

MongoDB(gfcon_raw)에서 PostgreSQL로 데이터를 동기화하는 시스템입니다.

---

## 컬렉션-테이블 매핑

### 1. notice 테이블

4개 대분류(공사/물품/외자/용역)별로 3개 컬렉션을 병합하여 동기화합니다.

| 카테고리 | MongoDB 컬렉션 | 역할 | sync_flag |
|---------|---------------|------|-----------|
| **공사** | `입찰공고정보서비스.입찰공고목록정보에대한공사조회` | Primary | `is_synced` |
| | `입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회` | 병합 (기초금액) | `is_synced` |
| | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사` | 병합 (낙찰정보) | `notice_is_synced` |
| **물품** | `입찰공고정보서비스.입찰공고목록정보에대한물품조회` | Primary | `is_synced` |
| | `입찰공고정보서비스.입찰공고목록정보에대한물품기초금액조회` | 병합 (기초금액) | `is_synced` |
| | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품` | 병합 (낙찰정보) | `notice_is_synced` |
| **외자** | `입찰공고정보서비스.입찰공고목록정보에대한외자조회` | Primary | `is_synced` |
| | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자` | 병합 (낙찰정보) | `notice_is_synced` |
| **용역** | `입찰공고정보서비스.입찰공고목록정보에대한용역조회` | Primary | `is_synced` |
| | `입찰공고정보서비스.입찰공고목록정보에대한용역기초금액조회` | 병합 (기초금액) | `is_synced` |
| | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역` | 병합 (낙찰정보) | `notice_is_synced` |

> 외자는 기초금액 컬렉션이 없습니다.

### 2. bid 테이블

4개 대분류별 낙찰정보 컬렉션에서 이중 병렬로 동기화합니다.

| 카테고리 | MongoDB 컬렉션 | sync_flag |
|---------|---------------|-----------|
| 공사 | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사` | `is_synced` |
| 물품 | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품` | `is_synced` |
| 외자 | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자` | `is_synced` |
| 용역 | `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역` | `is_synced` |

### 3. reserve_price_range 테이블

4개 대분류(공사/물품/외자/용역)별 예비가격 컬렉션을 병합하여 동기화합니다.

| 카테고리 | MongoDB 컬렉션 | sync_flag |
|---------|---------------|-----------|
| 공사 | `낙찰정보서비스.개찰결과공사예비가격상세목록조회` | `is_synced` |
| 물품 | `낙찰정보서비스.개찰결과물품예비가격상세목록조회` | `is_synced` |
| 용역 | `낙찰정보서비스.개찰결과용역예비가격상세목록조회` | `is_synced` |
| 외자 | `낙찰정보서비스.개찰결과외자예비가격상세목록조회` | `is_synced` |

> `bsns_div` 컬럼으로 카테고리(공사/물품/용역/외자)를 구분합니다.

### 4. 기타 테이블

| PostgreSQL 테이블 | MongoDB 컬렉션 | sync_flag |
|------------------|---------------|-----------|
| `company` | `사용자정보서비스.조달업체기본정보` | `is_synced` |
| `institution` | `사용자정보서비스.수요기관정보조회` | `is_synced` |
| `notice_industry_type` | `입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회` | `is_synced` |
| `notice_region` | `입찰공고정보서비스.입찰공고목록정보에대한참가가능지역정보조회` | `is_synced` |
| `company_industry_type` | `사용자정보서비스.조달업체업종정보조회` | `is_synced` |

---

## 동기화 구조

### 전체 아키텍처

```
MongoDB (gfcon_raw)
    │
    ├── [notice_unified] 4개 카테고리 병렬
    │   ├── 공사: 3개 컬렉션 병합 → notice
    │   ├── 물품: 3개 컬렉션 병합 → notice
    │   ├── 외자: 2개 컬렉션 병합 → notice
    │   └── 용역: 3개 컬렉션 병합 → notice
    │
    ├── [bid] 이중 병렬 (4개 카테고리 × N개 워커)
    │   ├── 공사 → bid
    │   ├── 물품 → bid
    │   ├── 외자 → bid
    │   └── 용역 → bid
    │
    ├── [reserve_price_range] 4개 카테고리 병렬
    │   ├── 공사 → reserve_price_range
    │   ├── 물품 → reserve_price_range
    │   ├── 외자 → reserve_price_range
    │   └── 용역 → reserve_price_range
    │
    └── [기타] 단일 프로세스
        ├── company
        ├── institution
        ├── notice_industry_type
        ├── notice_region
        └── company_industry_type
            │
            ▼
    PostgreSQL (data/tmp 스키마)
```

### Syncer 클래스 구조

| Syncer | 테이블 | 처리 방식 |
|--------|-------|----------|
| `NoticeSyncer` | notice | 단일 프로세스 (공사만) |
| `NoticeUnifiedSyncer` | notice | 4개 카테고리 병렬 |
| `BidSyncer` | bid | 이중 병렬 (카테고리 × ObjectId 분할) |
| `ReservePriceRangeSyncer` | reserve_price_range | 4개 카테고리 병렬 (FK 체크 포함) |
| `CompanySyncer` | company | 단일 프로세스 |
| `InstitutionSyncer` | institution | 단일 프로세스 |
| `NoticeIndustryTypeSyncer` | notice_industry_type | 단일 프로세스 |
| `NoticeRegionSyncer` | notice_region | 단일 프로세스 |
| `CompanyIndustryTypeSyncer` | company_industry_type | 단일 프로세스 |

---

## 사용법

### 기본 실행

```bash
cd /data/dev/bid-price-analysis/api-fetcher

# 단일 테이블 동기화
python -m sync_data.main_sync notice              # 공사만
python -m sync_data.main_sync notice_unified      # 4개 대분류 통합
python -m sync_data.main_sync bid                 # 투찰 (이중 병렬)
python -m sync_data.main_sync company
python -m sync_data.main_sync institution
python -m sync_data.main_sync reserve_price_range
python -m sync_data.main_sync notice_industry_type
python -m sync_data.main_sync notice_region
python -m sync_data.main_sync company_industry_type

# 모든 테이블 (FK 순서대로)
python -m sync_data.main_sync all
```

### 스키마 지정

```bash
# tmp 스키마 (테스트용)
python -m sync_data.main_sync bid --schema tmp

# data 스키마 (운영)
python -m sync_data.main_sync bid --schema data
```

### 테스트 모드

```bash
# 각 카테고리당 10,000건만 동기화
python -m sync_data.main_sync bid --schema tmp --test

# 제한 건수 조정
python -m sync_data.main_sync bid --schema tmp --test --test-limit 5000
```

---

## 동기화 순서

FK 의존성에 따라 다음 순서로 실행해야 합니다:

```
1. notice_unified        (PK: bidntceno, bidntceord) - 4개 카테고리 통합
2. company               (PK: bizno)
3. institution           (PK: dminsttcd)
4. bid                   (FK: notice, company)
5. reserve_price_range   (FK: notice)
6. notice_industry_type  (FK: notice)
7. notice_region         (FK: notice)
8. company_industry_type (FK: company)
```

`python -m sync_data.main_sync all` 명령은 자동으로 올바른 순서로 실행합니다.

### DAG 실행 흐름

DAG (`scheduler/dags/sync_data_dag.py`)에서는 FK 핸들링과 후처리가 추가됩니다:

```
notice_unified → company → [FK 핸들링] → institution → bid → reserve_price_range
    → notice_industry_type → notice_region → company_industry_type → [후처리]
```

| Task | 설명 |
|------|------|
| `sync_notice_unified` | 공고 동기화 (4개 카테고리) |
| `sync_company` | 업체 동기화 |
| `handle_unknown_companies` | 누락 bizno → `__UNKNOWN__` 업체로 추가 |
| `verify_bizrno_before_bid_sync` | bid의 모든 bizrno가 company에 존재하는지 검증 |
| `sync_institution` ~ `sync_company_industry_type` | 나머지 테이블 동기화 |
| `postprocess_calculated_columns` | 후처리 UPDATE (bid_count, answer_rate 등) |

---

## is_synced 플래그 전략

### 단일 컬렉션 → 단일 테이블
```
company: 조달업체기본정보.is_synced
```

### 다중 컬렉션 → 단일 테이블
```
notice: 공사조회.is_synced + 기초금액.is_synced + 낙찰정보.notice_is_synced
```

### 단일 컬렉션 → 다중 테이블
```
낙찰정보-공사:
  ├── is_synced         (bid 테이블용)
  └── notice_is_synced  (notice 테이블용)
```

---

## 후처리 컬럼

동기화 후 별도 UPDATE 쿼리로 계산되는 컬럼들:

| 테이블 | 컬럼 | 설명 |
|-------|------|------|
| `notice` | `bid_count` | 참여업체수 (bid 테이블 COUNT) |
| `notice` | `answer_rate` | 사정률 (예정가격/기초금액) |
| `notice` | `min_winning_price` | 낙찰하한가 |
| `bid` | `bid_rate` | 투찰율 |
| `bid` | `bid_rate_diff` | 투찰율 편차 |
| `company` | `has_bid` | 입찰 참여 이력 여부 |
| `company` | `bid_count` | 투찰 횟수 |
| `notice_industry_type` | `classification_code` | 업종 분류 코드 |
| `notice_industry_type` | `classification_name` | 업종 분류명 |

### GENERATED 컬럼

PostgreSQL에서 자동 계산되는 컬럼들:

| 테이블 | 컬럼 | 설명 |
|-------|------|------|
| `notice` | `a_value` | A값 (8개 필드 합산) |
| `reserve_price_range` | `bssamt_to_bsisplnprc_ratio` | 기초금액 대비 비율 |

---

## 디렉토리 구조

```
sync_data/
├── README.md                    # 이 파일
├── sync_config.py               # 동기화 설정 (컬렉션-테이블 매핑)
├── main_sync.py                 # CLI 실행 스크립트
│
├── sync/
│   ├── base_syncer.py           # BaseSyncer 추상 클래스
│   ├── syncer_factory.py        # SyncerFactory
│   ├── sync_strategies.py       # 동기화 전략 (Single/Parallel)
│   ├── transform_document.py    # MongoDB → PostgreSQL 변환
│   ├── syncers/                 # 테이블별 Syncer 구현
│   │   ├── notice_syncer.py
│   │   ├── notice_unified_syncer.py
│   │   ├── bid_syncer.py
│   │   ├── reserve_price_range_syncer.py
│   │   └── ...
│   └── utils/
│       ├── type_converter.py    # 타입 변환
│       └── postgres_meta.py     # PostgreSQL 메타데이터
│
├── create/                      # PostgreSQL 테이블 DDL
│   ├── user-defined-func.sql    # 사용자 정의 함수 (floor_5dp 등)
│   ├── notice.sql
│   ├── bid.sql
│   ├── company.sql
│   ├── reserve_price_range.sql
│   └── ...
│
├── scripts/                     # 유틸리티 스크립트
│   ├── reset_sync_flags.py      # 동기화 플래그 초기화
│   ├── count_sync_flags.py      # 플래그 카운트 확인
│   ├── verify_sync.py           # 동기화 상태 검증
│   └── ...
│
├── prefetch/                    # 동기화 전 사전 작업
│   ├── collect_missing_companies.py    # MongoDB 기반 누락 company 수집
│   └── handle_missing_companies.py     # FK 관리 (누락 bizno 처리)
│
├── postprocess/                 # 후처리 스크립트
│   ├── run_all.py               # 전체 후처리 실행
│   ├── update_notice_stats.py
│   ├── update_bid_rates.py
│   ├── update_company_stats.py
│   └── update_industry_type_classification.py
│
└── migrations/                  # 스키마 마이그레이션 스크립트
    └── ...
```

---

## 설정 파일 (sync_config.py)

각 테이블별 동기화 설정을 정의합니다:

```python
SYNC_CONFIGS = {
    "테이블명": {
        "psql_table": "PostgreSQL 테이블명",
        "psql_pk": ("pk1", "pk2"),           # Primary Key
        "multi_source": True/False,           # 다중 카테고리 모드
        "categories": [...],                  # multi_source=True일 때
        "merge_sources": [...],               # 병합할 컬렉션들
        "batch_size": 10000,
        "parallel": True/False,
        "num_workers": "auto",
        "foreign_key_check": {...},           # FK 체크 설정 (bid)
    }
}
```

---

## 성능 최적화

### 배치 처리
- MongoDB 커서: 1,000건씩 fetch
- PostgreSQL 삽입: 10,000건씩 bulk insert (bid: 1,000건)
- 메모리 관리: 100,000건마다 PostgreSQL 연결 재생성

### 병렬 처리

**bid 테이블 (이중 병렬):**
```
4개 카테고리 × N개 워커 (auto = CPU × 2)
= 최대 4 × 16 = 64개 동시 처리
```

**notice_unified (카테고리 병렬):**
```
4개 카테고리 동시 처리
```

**reserve_price_range (카테고리 병렬):**
```
4개 카테고리 동시 처리 + FK 체크 (notice 테이블)
```

---

## 테이블 자동 생성

스키마에 테이블이 없으면 `sync_data/create/{테이블명}.sql` 파일을 읽어 자동 생성합니다.

```
BaseSyncer.__init__()
    └── _verify_table_exists()
        └── 없으면 → _create_table_from_sql()
            ├── CREATE SCHEMA IF NOT EXISTS {schema}
            └── {테이블}.sql 실행 (스키마 자동 치환)
```

---

## 주의사항

1. **동기화 순서**: FK 의존성 때문에 notice/company를 먼저 동기화
2. **bid FK 체크**: notice에 없는 공고는 자동 skip
3. **reserve_price_range FK 체크**: notice에 없는 공고는 자동 skip
4. **bizno 예외 처리**:
   - `__DEFAULT__`: bid에서 사업자등록번호가 빈 값("")인 경우 (유찰 등)
   - `__UNKNOWN__`: API로 조회되지 않는 사업자등록번호 (폐업, 데이터 오류 등)
5. **재실행 안전**: `is_synced=True` 문서는 자동 skip
6. **테스트 시**: `--schema tmp` 사용 권장

---

## 동기화 플래그 초기화

재동기화가 필요할 때 MongoDB의 `is_synced` 플래그를 초기화합니다.

### 사용법

```bash
# 특정 테이블 관련 플래그 초기화
python -m sync_data.scripts.reset_sync_flags notice
python -m sync_data.scripts.reset_sync_flags bid company

# 모든 플래그 초기화
python -m sync_data.scripts.reset_sync_flags all

# 확인만 (실제 초기화 없이)
python -m sync_data.scripts.reset_sync_flags notice --dry-run

# 현재 플래그 상태 확인
python -m sync_data.scripts.reset_sync_flags --verify

# 확인 프롬프트 없이 바로 실행
python -m sync_data.scripts.reset_sync_flags all --force
```

### 플래그 매핑

테이블별로 관련된 컬렉션의 플래그가 초기화됩니다:

| 테이블 | 컬렉션 | 플래그 |
|--------|--------|--------|
| `notice_unified` | 공고조회 4개 | `is_synced` |
| | 기초금액조회 3개 | `is_synced` |
| | 낙찰정보 4개 | `notice_is_synced` |
| `bid` | 낙찰정보 4개 | `is_synced` |
| `reserve_price_range` | 예비가격상세 4개 | `is_synced` |

> 낙찰정보 컬렉션은 `is_synced`(bid용)와 `notice_is_synced`(notice용) 두 플래그를 가집니다.

---

## scripts/ 유틸리티

| 스크립트 | 설명 |
|----------|------|
| `reset_sync_flags.py` | 동기화 플래그 초기화 (통합) |
| `count_sync_flags.py` | 플래그 카운트 확인 |
| `verify_sync.py` | 동기화 상태 검증 |
| `resync_industry_type.py` | notice_industry_type 재동기화 |
| `insert_industry_type_info.py` | 업종 분류 정보 테이블 초기화 |
| `update_industry_type_classification.py` | 업종 분류 코드/명 업데이트 |

---

## prefetch/ 사전 작업

동기화 전 FK 위반 방지를 위한 사전 데이터 수집 스크립트입니다.

### handle_missing_companies.py

기존 데이터의 누락된 company 처리를 위한 Phase 1 스크립트입니다.

**사용법:**

```bash
cd /data/dev/bid-price-analysis/api-fetcher

# Step 1: FK 제약 해제
python -m sync_data.prefetch.handle_missing_companies --step disable-fk --schema tmp

# Step 2: bid 동기화 실행 (별도)
python -m sync_data.main_sync bid --schema tmp

# Step 3: 누락 bizno 조회 → API 수집
python -m sync_data.prefetch.handle_missing_companies --step after-bid-sync --schema tmp

# Step 4: company 동기화 실행 (별도)
python -m sync_data.main_sync company --schema tmp

# Step 5: 여전히 없는 bizno → __UNKNOWN__ 처리 및 FK 활성화
python -m sync_data.prefetch.handle_missing_companies --step after-company-sync --schema tmp

# 현재 상태 확인
python -m sync_data.prefetch.handle_missing_companies --step status --schema tmp
```

**단계별 처리:**

| Step | 설명 |
|------|------|
| `disable-fk` | bid 테이블의 company FK 제약 해제 |
| `after-bid-sync` | PostgreSQL에서 누락 bizno 조회 → API 수집 |
| `after-company-sync` | 여전히 없는 bizno → `__UNKNOWN__`으로 UPDATE, FK 활성화 |
| `enable-fk` | FK 제약만 활성화 |
| `status` | 현재 상태 확인 |

> **Note**: Phase 2(신규 데이터)는 `data_collection_dag.py`에서 bid 수집 후 자동으로 누락 company를 수집합니다.
