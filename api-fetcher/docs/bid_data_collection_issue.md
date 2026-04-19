# 투찰 데이터 수집 시스템 개선 계획

## 1. 현황 및 문제점

### 1.1 기존 수집 방식 (API A: 공공데이터개방표준서비스)

| 항목 | 내용 |
|------|------|
| API | 공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보 |
| 조회 기준 | 낙찰일자 (opengDate) |
| 일일 트래픽 | 100만 |
| 장점 | 대량 수집에 효율적 |
| **문제점** | **API 반영 지연으로 인한 누락 발생** |

### 1.2 누락 현황

```
수집 방식: 매일 새벽 2시 실행 → 전날 데이터만 수집
문제: API 반영 지연 시 해당 데이터 영구 미수집
```

**실제 사례: R26BK01268728**
- 개찰일시: 2026-01-21 18:00:00 KST
- 수집 시점: 2026-01-22 02:10:35 KST (개찰 후 약 8시간)
- 수집 시점 API 총 건수: 19,145건
- 이후 API 총 건수: 19,710건
- **누락: 565건**

**누적 누락 규모**

| 항목 | 건수 |
|------|------|
| 누락 공고 수 | 1,474,245건 |
| 예상 누락 투찰 row | 약 1.3억 건 |

---

## 2. 개선 계획

### 2.0 마이그레이션 (일회성)

1. **기존 bid 데이터 마이그레이션**
   - 기존에 잘 수집된 bid 데이터를 새로운 PostgreSQL bid 스키마에 맞게 변환
   - 데이터 손실 없이 필드 매핑 수행

2. **notice 테이블 낙찰 관련 컬럼 정리**
   - 기존 낙찰 관련 컬럼 삭제
   - 개찰결과 API (오퍼레이션 5,6,7,8)로 재수집하여 갱신

### 2.1 개찰결과 API로 변경 (낙찰정보서비스 오퍼레이션 5,6,7,8)

#### API 스펙

| 오퍼레이션 | 이름 | 영문명 | 카테고리 |
|-----------|------|--------|----------|
| 5 | 개찰결과 물품 목록 조회 | getOpengResultListInfoThng | 물품 |
| 6 | 개찰결과 공사 목록 조회 | getOpengResultListInfoCnstwk | 공사 |
| 7 | 개찰결과 용역 목록 조회 | getOpengResultListInfoServc | 용역 |
| 8 | 개찰결과 외자 목록 조회 | getOpengResultListInfoFrgcpt | 외자 |

#### 주요 응답 필드

| 필드명 | 설명 | 비고 |
|--------|------|------|
| bidNtceNo | 입찰공고번호 | PK |
| bidNtceOrd | 입찰공고차수 | PK |
| bidClsfcNo | 입찰분류번호 | |
| rbidNo | 재입찰번호 | |
| bidNtceNm | 입찰공고명 | |
| opengDt | 개찰일시 | |
| prtcptCnum | 참가업체수 | |
| opengCorpInfo | 개찰업체정보 | 업체명^사업자번호^대표자명^투찰금액^투찰율 |
| **progrsDivCdNm** | **진행구분코드명** | **유찰/개찰완료/재입찰** |
| ntceInsttNm | 공고기관명 | |
| dminsttNm | 수요기관명 | |
| opengRsltNtcCntnts | 개찰결과공지내용 | |

#### PostgreSQL 스키마 변경

- 4개 카테고리(물품/공사/용역/외자) 데이터 포함 가능하도록 컬럼 합집합 구성
- `progrsDivCdNm` 컬럼 추가 (유찰/개찰완료/재입찰)
- `bid_collected` 플래그 컬럼 추가 (투찰데이터 수집 완료 여부)

#### 조회구분 (inqryDiv) 옵션

| inqryDiv | 기준 | 용도 |
|----------|------|------|
| 1 | 입력일시 | 초기 일회성 수집 (과거 전량) |
| 2 | 공고일시 | - |
| 3 | 개찰일시 | - |
| 4 | 입찰공고번호 | **이후 매일 수집** |

#### 수집 방식

| 단계 | 조회 방식 | 설명 |
|------|----------|------|
| **초기 (일회성)** | inqryDiv=1 (입력일시) | 과거 데이터 전량 수집 |
| **이후 (매일)** | inqryDiv=4 (공고번호) | 개찰일자 도래한 공고만 조회 |

- **초기 수집**: 입력일시 기준으로 과거 데이터 전량 수집 (트래픽 문제 없음)
- **이후 수집**: 개찰일자가 도래한 공고에 대해 공고번호로 개찰결과 조회

### 2.2 새로운 투찰데이터 수집 방식

#### 투찰데이터 API (오퍼레이션 13,14,15)

| 오퍼레이션 | 이름 | progrsDivCdNm | 예상 row 수 |
|-----------|------|---------------|-------------|
| 13 | 개찰결과 개찰완료 목록 조회 | 개찰완료 | 참여업체 수만큼 |
| 14 | 개찰결과 유찰 목록 조회 | 유찰 | 1 row |
| 15 | 개찰결과 재입찰 목록 조회 | 재입찰 | 1 row |

#### 오퍼레이션 13 응답 필드 (개찰완료)

| 필드명 | 설명 |
|--------|------|
| opengRsltDivNm | 개찰결과구분명 |
| bidNtceNo | 입찰공고번호 |
| bidNtceOrd | 입찰공고차수 |
| bidClsfcNo | 입찰분류번호 |
| rbidNo | 재입찰번호 |
| opengRank | 개찰순위 |
| prcbdrBizno | 투찰업체사업자등록번호 |
| prcbdrNm | 투찰업체명 |
| prcbdrCeoNm | 투찰업체대표자명 |
| bidprcAmt | 투찰금액 |
| bidprcrt | 투찰률 |
| rmrk | 비고 |
| drwtNo1 | 추첨번호1 |
| drwtNo2 | 추첨번호2 |
| bidprcDt | 투찰일시 |

#### 오퍼레이션 14 응답 필드 (유찰)

| 필드명 | 설명 |
|--------|------|
| opengRsltDivNm | 개찰결과구분명 |
| bidNtceNo | 입찰공고번호 |
| bidNtceOrd | 입찰공고차수 |
| bidClsfcNo | 입찰분류번호 |
| rbidNo | 재입찰번호 |
| nobidRsn | 유찰사유 |

#### 오퍼레이션 15 응답 필드 (재입찰)

| 필드명 | 설명 |
|--------|------|
| opengRsltDivNm | 개찰결과구분명 |
| bidNtceNo | 입찰공고번호 |
| bidNtceOrd | 입찰공고차수 |
| bidClsfcNo | 입찰분류번호 |
| rbidNo | 재입찰번호 |
| bidClseDt | 입찰마감일시 |
| opengDt | 개찰일시 |
| rbidRsn | 재입찰사유 |
| cmmnSpldmdAgrmntClseDt | 공동수급협정마감일시 |

#### 수집 로직 플로우 (매일 수집)

```
┌─────────────────────────────────────────────────────────────────┐
│                    투찰데이터 수집 로직 (매일)                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  1. 수집 대상 공고 조회 (PostgreSQL)                              │
│     ├─ 조건: opengdt <= NOW()           (개찰일자 도래)          │
│     └─ 조건: bid_collected = FALSE      (미수집 건)             │
│                                                                 │
│  2. 개찰결과 API 호출 (오퍼레이션 5,6,7,8)                        │
│     ├─ inqryDiv=4 (공고번호 기준)                                │
│     ├─ bidNtceNo로 조회                                         │
│     └─ progrsDivCdNm 값 확인                                    │
│                                                                 │
│  3. progrsDivCdNm에 따라 투찰데이터 API 호출                      │
│     ├─ '개찰완료' → 오퍼레이션 13 호출 (투찰업체 목록)            │
│     ├─ '유찰'     → 오퍼레이션 14 호출 (유찰사유)                │
│     └─ '재입찰'   → 오퍼레이션 15 호출 (재입찰사유)              │
│                                                                 │
│  4. 수집 완료 처리                                               │
│     └─ bid_collected = TRUE 로 업데이트                         │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

#### PostgreSQL 쿼리 예시

```sql
-- 1. 투찰데이터 수집 대상 공고 조회
--    (개찰일자 도래 + 미수집)
SELECT bidntceno, bidntceord, bsns_div
FROM data.notice
WHERE opengdt <= NOW()           -- 개찰일자 도래
  AND bid_collected = FALSE      -- 미수집
ORDER BY opengdt;

-- 2. 개찰결과 API (5,6,7,8) 호출 후 progrsDivCdNm 업데이트
UPDATE data.notice
SET progrsdivcdnm = %s,          -- 유찰/개찰완료/재입찰
    prtcptcnum = %s,             -- 참가업체수
    opengcorpinfo = %s           -- 개찰업체정보
WHERE bidntceno = %s AND bidntceord = %s;

-- 3. 투찰데이터 수집 완료 후 플래그 업데이트
UPDATE data.notice
SET bid_collected = TRUE
WHERE bidntceno = %s AND bidntceord = %s;
```

---

## 3. 소요 시간 추정

### 3.1 트래픽 정보

| API | 오퍼레이션 | 일일 트래픽 (1키) |
|-----|-----------|-----------------|
| 개찰결과 API | 5,6,7,8 (각각) | 100,000건 |
| 투찰데이터 API (개찰완료) | 13 | 100,000건 |
| 투찰데이터 API (유찰) | 14 | 100,000건 |
| 투찰데이터 API (재입찰) | 15 | 100,000건 |

> 오퍼레이션별 트래픽이 **별도 계산**되므로, 13+14+15 = 일일 30만 건 사용 가능

### 3.2 초기 수집 (일회성)

**개찰결과 API (5,6,7,8)** - 입력일시 기준 수집
- 일시 기준 수집이므로 트래픽 문제 없음
- 과거 전량 수집 가능

**투찰데이터 API (13,14,15)** - 공고번호 기준 수집

| 항목 | 값 |
|------|-----|
| 누락 공고 수 | 1,474,245건 |
| 일일 트래픽 (1키, 13+14+15) | 300,000건 |
| 인증키 4개 일일 트래픽 | 1,200,000건 |
| **예상 소요 (4키)** | **약 2일** |

### 3.3 이후 매일 수집

- 하루 신규 공고 수: 약 5,000~10,000건
- 일일 트래픽 (30만) 대비 충분히 여유

---

## 4. 구현 작업 목록

### Phase 0: 스키마 변경 및 마이그레이션

**파일 위치**: `sync_data/migrations/004_bid_collection_schema_change.sql`

- [ ] **0.1 마이그레이션 SQL 실행**
  ```bash
  psql -d gfcon -f sync_data/migrations/004_bid_collection_schema_change.sql
  ```

- [ ] **0.2 notice 테이블 신규 컬럼 추가 확인**
  - `actual_opengdt` (실제 개찰일시 - 개찰결과 API의 opengDt)
  - `openg_result_inptdt` (개찰결과 입력일시 - 개찰결과 API의 inptDt)
  - `bidclsfcno` (입찰분류번호)
  - `rbidno` (재입찰번호)
  - `prtcptcnum` (참가업체수)
  - `opengcorpinfo` (개찰업체정보)
  - `progrsdivcdnm` (진행구분코드명)
  - `rsrvtnprcefileexistnceyn` (예비가격파일존재여부)
  - `opengrsltntccntnts` (개찰결과공지내용)
  - `bid_collected` (투찰데이터 수집 완료 여부)
  - `openg_result_synced_at` (개찰결과 동기화 시점)

  > **참고**: 동일 필드명이 다른 API에서 다른 의미로 사용됨
  > | API | MongoDB 필드 | PostgreSQL 컬럼 | 설명 |
  > |-----|-------------|-----------------|------|
  > | 입찰공고정보 | `opengDt` | `opengdt` | 예정 개찰일시 |
  > | 개찰결과 | `opengDt` | `actual_opengdt` | 실제 개찰일시 |
  > | 기초금액 | `inptDt` | `inptdt` | 기초금액 입력일시 |
  > | 개찰결과 | `inptDt` | `openg_result_inptdt` | 개찰결과 입력일시 |

- [ ] **0.3 bid 테이블 신규 컬럼 추가 확인**
  - `bidclsfcno`, `rbidno` (공고 식별 확장)
  - `opengrsltdivnm` (개찰결과구분명)
  - `prcbdrnm`, `prcbdrceonm` (투찰업체 정보)
  - `rmrk`, `cnsttyaccotbidamturl` (비고, URL)
  - `drwtno1`, `drwtno2` (추첨번호)
  - `bidprcdt` (투찰일시)
  - `nobidrsn` (유찰사유)
  - `rbidrsn`, `rbid_*` (재입찰 관련)

- [ ] **0.4 기존 데이터 마이그레이션**
  - 기존에 낙찰정보가 있는 공고: `bid_collected = TRUE` 설정
  - 기존 bid 데이터의 `bidprcdt` 컬럼 채우기

---

### Phase 1: MongoDB 컬렉션 설정

- [ ] **1.1 개찰결과 컬렉션 생성** (`gfcon_raw` DB)
  ```
  낙찰정보서비스.개찰결과물품목록조회
  낙찰정보서비스.개찰결과공사목록조회
  낙찰정보서비스.개찰결과용역목록조회
  낙찰정보서비스.개찰결과외자목록조회
  ```

- [ ] **1.2 투찰데이터 컬렉션 생성** (`gfcon_raw` DB)
  ```
  낙찰정보서비스.개찰결과개찰완료목록조회
  낙찰정보서비스.개찰결과유찰목록조회
  낙찰정보서비스.개찰결과재입찰목록조회
  ```

- [ ] **1.3 컬렉션 인덱스 설정**
  - `bidNtceNo`, `bidNtceOrd` 복합 인덱스
  - `collected_at` 인덱스

---

### Phase 2: 개찰결과 API 수집기 구현 (오퍼레이션 5,6,7,8)

**파일 위치**: `fetch_data/src/openg_result_collector.py`

- [ ] **2.1 API 호출 클래스 구현**
  - 엔드포인트: `낙찰정보서비스`
  - 오퍼레이션:
    - 5: `getOpengResultListInfoThng` (물품)
    - 6: `getOpengResultListInfoCnstwk` (공사)
    - 7: `getOpengResultListInfoServc` (용역)
    - 8: `getOpengResultListInfoFrgcpt` (외자)

- [ ] **2.2 조회 파라미터 설정**
  ```python
  # 초기 수집 (일회성)
  params = {
      'inqryDiv': '1',  # 입력일시 기준
      'inqryBgnDt': '200001010000',
      'inqryEndDt': 'YYYYMMDDHHMM',
  }

  # 이후 수집 (매일)
  params = {
      'inqryDiv': '4',  # 공고번호 기준
      'bidNtceNo': '{공고번호}',
  }
  ```

- [ ] **2.3 MongoDB 저장 로직**
  - 컬렉션명 매핑 (bsns_div → 컬렉션)
  - `collected_at` 타임스탬프 추가

- [ ] **2.4 에러 핸들링 및 재시도 로직**

---

### Phase 3: 투찰데이터 API 수집기 구현 (오퍼레이션 13,14,15)

**파일 위치**: `fetch_data/src/bid_data_collector.py`

- [ ] **3.1 API 호출 클래스 구현**
  - 오퍼레이션:
    - 13: `getOpengResultListInfoOpengCompt` (개찰완료)
    - 14: `getOpengResultListInfoFailing` (유찰)
    - 15: `getOpengResultListInfoRebid` (재입찰)

- [ ] **3.2 progrsDivCdNm 분기 로직**
  ```python
  def get_operation_by_progrs_div(progrsdivcdnm: str) -> int:
      mapping = {
          '개찰완료': 13,
          '유찰': 14,
          '재입찰': 15,
      }
      return mapping.get(progrsdivcdnm)
  ```

- [ ] **3.3 조회 파라미터 설정**
  ```python
  params = {
      'inqryDiv': '4',  # 공고번호 기준
      'bidNtceNo': '{공고번호}',
  }
  ```

- [ ] **3.4 응답 필드 매핑**
  | API 필드 | PostgreSQL 컬럼 |
  |---------|----------------|
  | prcbdrBizno | bidprccorpbizrno |
  | prcbdrNm | prcbdrnm |
  | prcbdrCeoNm | prcbdrceonm |
  | bidprcrt | bidprcrt |
  | bidprcAmt | bidprcamt |
  | opengRank | opengrank |
  | bidprcDt | bidprcdt |
  | drwtNo1/2 | drwtno1/2 |
  | nobidRsn | nobidrsn |
  | rbidRsn | rbidrsn |

- [ ] **3.5 MongoDB 저장 및 bid_collected 플래그 업데이트**

---

### Phase 4: PostgreSQL 동기화 로직

**파일 위치**: `sync_data/sync/syncers/openg_result_syncer.py`, `bid_syncer.py`

- [ ] **4.1 개찰결과 동기화 로직 구현**
  - MongoDB → PostgreSQL notice 테이블
  - 업데이트 필드: `progrsdivcdnm`, `prtcptcnum`, `opengcorpinfo` 등
  - 동기화 시점: `openg_result_synced_at`

- [ ] **4.2 투찰데이터 동기화 로직 구현**
  - MongoDB → PostgreSQL bid 테이블
  - UPSERT 로직 (INSERT ON CONFLICT UPDATE)
  - 동기화 시점: `synced_at`

- [ ] **4.3 bid_collected 플래그 업데이트 로직**
  ```sql
  UPDATE data.notice
  SET bid_collected = TRUE
  WHERE bidntceno = %s AND bidntceord = %s;
  ```

- [ ] **4.4 sync_config.py 업데이트**
  - 새로운 syncer 등록
  - 필드 매핑 설정

---

### Phase 5: 초기 데이터 수집 (일회성)

- [ ] **5.1 개찰결과 API 전량 수집**
  ```bash
  # 4개 카테고리 x 과거 전량 (입력일시 기준)
  python fetch_data/src/openg_result_collector.py --mode=initial
  ```

- [ ] **5.2 투찰데이터 API 누락분 수집**
  ```bash
  # 누락 공고 147만건 대상
  # 일일 120만건 (4키 x 30만) → 약 2일 소요
  python fetch_data/src/bid_data_collector.py --mode=initial
  ```

- [ ] **5.3 수집 결과 검증**
  ```sql
  -- 수집 완료 현황
  SELECT
      COUNT(*) FILTER (WHERE bid_collected = TRUE) AS collected,
      COUNT(*) FILTER (WHERE bid_collected = FALSE AND opengdt <= NOW()) AS pending
  FROM data.notice;
  ```

---

### Phase 6: Airflow DAG 구현

**파일 위치**: `scheduler/dags/bid_collection_dag.py`

- [ ] **6.1 DAG 구조 설계**
  ```
  bid_collection_dag
  ├── task_1: query_pending_notices
  │   └─ 조건: opengdt <= NOW() AND bid_collected = FALSE
  ├── task_2: fetch_openg_result (오퍼레이션 5,6,7,8)
  │   └─ progrsDivCdNm 값 확인
  ├── task_3: fetch_bid_data (오퍼레이션 13,14,15)
  │   └─ progrsDivCdNm에 따라 분기
  ├── task_4: sync_to_postgresql
  │   └─ MongoDB → PostgreSQL 동기화
  └── task_5: update_bid_collected_flag
      └─ bid_collected = TRUE 업데이트
  ```

- [ ] **6.2 스케줄 설정**
  - 실행 시간: 매일 KST 03:00 (UTC 18:00)
  - 기존 낙찰정보 수집 DAG와 병행 또는 대체

- [ ] **6.3 모니터링 및 알림**
  - 수집 실패 시 Slack 알림
  - 일일 수집 현황 리포트

---

### Phase 7: 기존 시스템 정리

- [ ] **7.1 기존 낙찰정보 수집 DAG 비활성화**
  - `공공데이터개방표준서비스.데이터셋개방표준에따른낙찰정보` 관련 태스크

- [ ] **7.2 레거시 컬럼 관리 방안 결정**
  - 즉시 삭제 vs 당분간 유지
  - `opengdate`, `opengtm`, `fnlsucsf*` 등

- [ ] **7.3 문서 업데이트**
  - README 업데이트
  - 데이터 딕셔너리 업데이트

---

### 체크포인트

| 단계 | 완료 기준 | 상태 |
|-----|---------|------|
| Phase 0 | 마이그레이션 SQL 실행 완료 | ✅ test.notice에 적용 완료 |
| Phase 1 | MongoDB 컬렉션 생성 완료 | ✅ 자동 생성됨 (수집 시) |
| Phase 2 | 개찰결과 API 수집기 구현 | ✅ DataCollector로 통합 |
| Phase 3 | 투찰데이터 API 수집기 구현 | ❌ 미착수 |
| Phase 4 | 동기화 로직 구현 | ✅ NoticeUnifiedSyncer 구현 완료 |
| Phase 5 | 누락 데이터 전량 수집 완료 | 🔄 재수집 진행 중 (2026-01-27) |
| Phase 6 | DAG 정상 동작 확인 | ✅ 개찰결과 태스크 추가 완료 |
| Phase 7 | 기존 시스템 정리 완료 | 🔄 레거시 컬럼 제거 완료, 테이블 교체 대기 |

---

## 5. 진행상황 (2026-01-27 업데이트)

### 5.1 완료된 작업

#### API 키 순환 로직 구현
- **파일**: `common/api_key_manager.py`
- 4개 API 키 순환 관리 (싱글톤)
- 일일 트래픽 초과 시 자동 다음 키 전환

#### notice 테이블 동기화 완료
- **test.notice 테이블에 7,055,278건 동기화 완료**
- 신규 컬럼 추가:
  - `actual_opengdt`: 실제 개찰일시 (개찰결과 API의 opengDt)
  - `openg_result_inptdt`: 개찰결과 입력일시
  - `progrsdivcdnm`: 진행구분코드명 (개찰완료/유찰/재입찰)
  - `prtcptcnum`: 참가업체수
  - `opengcorpinfo`: 개찰업체정보
  - `bid_collected`: 투찰데이터 수집 완료 여부
- **레거시 컬럼 제거** (notice.sql에서):
  - `opengdate`, `opengtm`, `fnlsucsfamt`, `fnlsucsfrt`, `fnlsucsfdate`
  - `fnlsucsfcorpnm`, `fnlsucsfcorpceonm`, `fnlsucsfcorpofclnm`
  - `fnlsucsfcorpbizrno`, `fnlsucsfcorpadrs`, `fnlsucsfcorpcontacttel`
  - `cntrctcnclssttusnm`, `bidwinrdcsnmthdnm`, `win_synced_at`

#### NoticeUnifiedSyncer 수정
- **파일**: `sync_data/sync/syncers/notice_unified_syncer.py`
- `notice_unified` 대신 `notice` config 사용하도록 변경
- `field_mapping` 적용 로직 추가 (opengDt → actual_opengdt 등)
- syncer_factory.py에서 `notice` → `NoticeUnifiedSyncer` 매핑

#### 개찰결과 수집 로직 통합 및 버그 수정
- **문제 발견**: `openg_result_collector.py`에 재시도 로직 없음
  - 타임아웃 발생 시 해당 날짜 누락
  - **총 6,246일 누락** (2010~2026, 4개 카테고리)
  - 누락 목록: `docs/openg_result_missing_dates.txt`
- **해결**: `data_collector.py`로 통합
  - `data_collector.py`는 재시도 로직 있음 (`while pending_dates` 루프)
  - 실패한 날짜 자동 재시도
- **삭제**: `fetch_data/src/openg_result_collector.py` (더 이상 필요 없음)
- **스크립트 수정**: `scripts/run_openg_result_collectors.sh`
  - `DataCollector` 사용하도록 변경
  - 카테고리별 operation_number 매핑 (물품=5, 공사=6, 용역=7, 외자=8)

### 5.2 현재 진행 중

#### 개찰결과 재수집 (2026-01-27 15:23 시작)
- **68개 screen 세션** 가동 중
- 대상: 2010년 ~ 2026년, 4개 카테고리
- `DataCollector` 사용 (재시도 로직 포함)
- 중복 데이터는 자동 업데이트 처리 (`is_synced = False` 설정)

#### test.notice → data.notice 테이블 교체 대기
- test.notice 정합성 확인 완료
- 개찰결과 재수집 완료 후 교체 예정

### 5.3 남은 작업

1. **개찰결과 재수집 완료 대기**
   - 68개 screen 세션 완료 확인
   - 누락 날짜 없는지 검증

2. **test.notice → data.notice 교체**
   ```sql
   DROP TABLE data.notice;
   ALTER TABLE test.notice SET SCHEMA data;
   ```

3. **notice 테이블 재동기화** (개찰결과 반영)
   - `is_synced = False`인 문서들 재동기화

4. **투찰데이터 수집기 구현** (오퍼레이션 13,14,15)
   - `progrsDivCdNm` 값에 따라 분기 호출
   - 개찰완료 → 13, 유찰 → 14, 재입찰 → 15

5. **투찰데이터 동기화 로직 구현**
   - MongoDB → PostgreSQL bid 테이블 동기화

### 5.4 구현/수정된 파일 목록

```
api-fetcher/
├── common/
│   └── api_key_manager.py              # API 키 순환 관리자
├── fetch_data/src/
│   ├── api_client.py                   # API 클라이언트
│   ├── data_collector.py               # 개찰결과 수집 통합 (재시도 로직 포함)
│   └── (삭제) openg_result_collector.py
├── sync_data/
│   ├── create/notice.sql               # 레거시 컬럼 제거됨
│   ├── sync/syncers/notice_unified_syncer.py  # field_mapping 적용
│   ├── sync/syncer_factory.py          # notice → NoticeUnifiedSyncer 매핑
│   └── sync_config.py                  # OPENG_RESULT_FIELD_MAPPING 정의
├── scheduler/dags/
│   └── data_collection_dag.py          # DAG
├── scripts/
│   └── run_openg_result_collectors.sh  # DataCollector 사용하도록 수정
└── docs/
    └── openg_result_missing_dates.txt  # 누락된 날짜 목록 (6,246일)
```

---

## 6. 참고: 기존 API A vs 새로운 방식 비교

| 구분 | 기존 (API A) | 새로운 방식 |
|------|-------------|------------|
| 개찰결과 수집 | 공공데이터개방표준서비스 | 낙찰정보서비스 5,6,7,8 |
| 투찰데이터 수집 | 공공데이터개방표준서비스 | 낙찰정보서비스 13,14,15 |
| 조회 기준 (초기) | 낙찰일자 | 입력일시 (inqryDiv=1) |
| 조회 기준 (매일) | 낙찰일자 | 공고번호 (inqryDiv=4) |
| 누락 가능성 | 있음 (API 반영 지연) | **없음 (플래그 기반)** |
| 트래픽 효율 | 높음 | 중간 (공고 단위 호출) |
| 일일 트래픽 | 100만 | 30만 (13+14+15) |
| 유찰/재입찰 처리 | 별도 처리 필요 | **자동 분기 처리** |
| 데이터 정합성 | 보장 안됨 | **플래그로 추적 가능** |
