# Notice 통합 테이블 변경 사항

## 개요
입찰공고 데이터를 4개 대분류(공사/물품/외자/용역)로 분리된 MongoDB 컬렉션에서
단일 PostgreSQL notice 테이블로 통합 동기화하는 기능 추가.

## 변경 일자
2025-12-18

## 변경 파일

### 1. 신규 파일

#### `sync_data/create/notice_v2_unified.sql`
- 통합 notice 테이블 스키마 (4개 대분류 통합)
- 총 ~213개 컬럼:
  - Primary Key: bidntceno, bidntceord
  - 업종구분: bsns_div (공사/물품/외자/용역)
  - 공통필드: 78개
  - 공사 전용: 46개
  - 물품/외자/용역 관련: ~40개
  - 기초금액: 28개
  - 낙찰정보: 14개
  - 메타/계산: 6개

#### `sync_data/sync/syncers/notice_unified_syncer.py`
- NoticeUnifiedSyncer 클래스 구현
- 4개 카테고리 병렬 처리 (multiprocessing)
- 각 카테고리를 독립 프로세스로 동시 실행
- bsns_div 필드 자동 설정
- Manager.dict()를 통한 결과 공유

#### `docs/입찰공고목록정보_필드명세서.csv`
- 4개 대분류 컬렉션의 필드 명세서
- 컬럼: 필드명, 대분류, 필드명(국문), 설명, 샘플값

### 2. 수정 파일

#### `sync_data/sync_config.py`
- `notice_unified` 설정 추가
- `multi_source: True` 모드로 4개 카테고리 병렬 동기화
- 각 카테고리별 merge_sources 정의:
  - 공사: 공사조회 + 공사기초금액조회 + 낙찰정보-공사 (3개 merge)
  - 물품: 물품조회 + 물품기초금액조회 + 낙찰정보-물품 (3개 merge)
  - 외자: 외자조회 + 낙찰정보-외자 (2개 merge, 기초금액 없음)
  - 용역: 용역조회 + 용역기초금액조회 + 낙찰정보-용역 (3개 merge)
- 기존 `notice` 설정의 낙찰정보 컬렉션명 수정:
  - `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보`
  - → `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사`

#### `sync_data/sync/syncers/__init__.py`
- NoticeUnifiedSyncer export 추가

#### `sync_data/sync/syncer_factory.py`
- `notice_unified` → `NoticeUnifiedSyncer` 매핑 추가

#### `sync_data/main_sync.py`
- `notice_unified` 옵션 추가
- choices에 notice_unified 포함

#### `sync_data/postprocess/update_bid_rates.py`
- bid_rate, bid_rate_diff 업데이트 시 `IS NULL` 조건 추가
- 신규 동기화된 행만 계산하여 성능 개선

#### `sync_data/sync/sync_strategies.py`
- `_merge_documents()`: source_synced_columns 반환 추가
- `_transform_to_psql_row()`: 소스별 synced_at 컬럼 설정 지원
- bssamt_synced_at, win_synced_at 자동 설정

## 데이터 구조

### MongoDB 컬렉션 (4개 대분류)
```
# Primary 컬렉션 (입찰공고 기본정보)
입찰공고정보서비스.입찰공고목록정보에대한공사조회  (primary)
입찰공고정보서비스.입찰공고목록정보에대한물품조회  (primary)
입찰공고정보서비스.입찰공고목록정보에대한외자조회  (primary)
입찰공고정보서비스.입찰공고목록정보에대한용역조회  (primary)

# 기초금액 컬렉션 (외자 제외)
입찰공고정보서비스.입찰공고목록정보에대한공사기초금액조회
입찰공고정보서비스.입찰공고목록정보에대한물품기초금액조회
입찰공고정보서비스.입찰공고목록정보에대한용역기초금액조회

# 낙찰정보 컬렉션
공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-공사
공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-물품
공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-외자
공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보-용역
```

### 카테고리별 Merge 구성
| 카테고리 | Primary | 기초금액 | 낙찰정보 |
|---------|---------|---------|---------|
| 공사 | 공사조회 | 공사기초금액조회 | 낙찰정보-공사 |
| 물품 | 물품조회 | 물품기초금액조회 | 낙찰정보-물품 |
| 외자 | 외자조회 | (없음) | 낙찰정보-외자 |
| 용역 | 용역조회 | 용역기초금액조회 | 낙찰정보-용역 |

### PostgreSQL 테이블
```
notice (통합)
  ├── bidntceno, bidntceord (PK)
  ├── bsns_div (공사/물품/외자/용역)
  ├── 공통 필드 78개
  ├── 대분류별 고유 필드
  ├── 기초금액 필드 (외자 제외)
  ├── 낙찰정보 필드
  └── 메타/계산 필드
```

## 사용법

### 테스트 실행
```bash
# tmp 스키마에서 테스트 (테이블 자동 생성)
python -m sync_data.main_sync notice_unified --schema tmp
```

### 운영 실행
```bash
# data 스키마에서 실행
python -m sync_data.main_sync notice_unified --schema data
```

## 구현 완료

### 1. NoticeUnifiedSyncer 클래스
- `sync_data/sync/syncers/notice_unified_syncer.py`
- 4개 카테고리 병렬 처리 (multiprocessing.Process)
- 각 워커가 독립적인 DB 연결 생성
- 진행률 모니터링 (tqdm)
- Manager.dict()를 통한 결과 공유

### 2. SyncerFactory 업데이트
- `notice_unified` → `NoticeUnifiedSyncer` 매핑 완료

### 3. 병렬 처리 아키텍처
```
Main Process
  ├── [공사] Worker Process (PID: xxx)
  ├── [물품] Worker Process (PID: xxx)
  ├── [외자] Worker Process (PID: xxx)
  └── [용역] Worker Process (PID: xxx)
```

## FK 영향

notice 테이블을 참조하는 FK:
- `bid.sql`: FOREIGN KEY (bidNtceNo, bidNtceOrd) REFERENCES notice
- `reserve_price_range.sql`: FOREIGN KEY REFERENCES notice

### DROP TABLE notice CASCADE 시:
- FK 제약조건만 삭제됨 (테이블 데이터 유지)
- 재생성 후 FK 다시 추가 필요

### CASCADE 없이 DROP 시:
- 에러 발생: "cannot drop table notice because other objects depend on it"
