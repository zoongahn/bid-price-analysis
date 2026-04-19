CREATE TABLE IF NOT EXISTS company
(
    /* 고유 식별자 */
    bizNo             TEXT PRIMARY KEY, -- 사업자등록번호

    /* 한글/영문 상호 */
    corpNm            TEXT NOT NULL,    -- 회사명(국문)
    engCorpNm         TEXT,             -- 회사명(영문)

    /* 개업일자 */
    opBizDt           TIMESTAMP,        -- 개업일자

    /* 소재지 */
    rgnCd             TEXT,             -- 행정구역코드
    rgnNm             TEXT,             -- 행정구역명
    zip               TEXT,             -- 우편번호
    adrs              TEXT,             -- 도로명주소
    dtlAdrs           TEXT,             -- 상세주소
    cntryNm           TEXT,             -- 국가명

    /* 연락처 */
    telNo             TEXT,
    faxNo             TEXT,
    hmpgAdrs          TEXT,             -- 홈페이지

    /* 사업 구분·규모 */
    mnfctDivCd        TEXT,             -- 제조·공급 구분코드
    mnfctDivNm        TEXT,             -- 제조·공급 구분명
    empLyeNum         INTEGER,          -- 종업원수
    corpBsnsDivCd     TEXT,             -- 사업분야 코드(콤마 구분)
    corpBsnsDivNm     TEXT,             -- 사업분야 명(콤마 구분)
    hdOffceDivNm      TEXT,             -- 본사/지사 구분

    /* 행정 정보 */
    rgstDt            TIMESTAMP,        -- 최초 등록일시
    chgDt             TIMESTAMP,        -- 최근 변경일시
    esntlNoCertRgstYn CHAR(1),          -- 필수번호인증여부

    /* 대표자 */
    ceoNm             TEXT,             -- 대표자명

    /* 메타 */
    collected_at      TIMESTAMPTZ,      -- 수집시각
    synced_at         TIMESTAMPTZ,      -- 마지막 동기화 시점

    /* 국세청 사업자등록 상태조회 결과 */
    bizstt_b_stt            TEXT,          -- 납세자상태 (계속사업자/휴업자/폐업자)
    bizstt_b_stt_cd         TEXT,          -- 납세자상태 코드 (01/02/03)
    bizstt_tax_type         TEXT,          -- 과세유형 명칭
    bizstt_tax_type_cd      TEXT,          -- 과세유형 코드
    bizstt_end_dt           DATE,          -- 폐업일
    bizstt_utcc_yn          TEXT,          -- 단위과세전환폐업여부 (Y/N)
    bizstt_tax_type_change_dt DATE,        -- 최근과세유형전환일자
    bizstt_invoice_apply_dt DATE,          -- 세금계산서적용일자
    bizstt_rbf_tax_type     TEXT,          -- 직전과세유형 명칭
    bizstt_rbf_tax_type_cd  TEXT,          -- 직전과세유형 코드
    bizstt_status_updated_at TIMESTAMPTZ,  -- 국세청 상태 조회 시각

    /* 계산 컬럼 (후처리 UPDATE) */
    has_bid           BOOLEAN,          -- 투찰 이력 여부
    bid_count         INTEGER           -- 투찰 횟수
);

/* ──────────────────────────────────────────────────────────────────────────
   ② 컬럼 주석(선택) – psql COMMENT 구문
   ────────────────────────────────────────────────────────────────────────── */

COMMENT ON COLUMN company.bizNo IS '사업자등록번호';
COMMENT ON COLUMN company.corpNm IS '회사명(국문)';
COMMENT ON COLUMN company.engCorpNm IS '회사명(영문)';
COMMENT ON COLUMN company.opBizDt IS '개업일자';
COMMENT ON COLUMN company.rgnCd IS '행정구역코드(행자부)';
COMMENT ON COLUMN company.rgnNm IS '행정구역명';
COMMENT ON COLUMN company.zip IS '우편번호';
COMMENT ON COLUMN company.adrs IS '도로명주소';
COMMENT ON COLUMN company.dtlAdrs IS '상세주소';
COMMENT ON COLUMN company.cntryNm IS '국가명';
COMMENT ON COLUMN company.telNo IS '전화번호';
COMMENT ON COLUMN company.faxNo IS '팩스번호';
COMMENT ON COLUMN company.hmpgAdrs IS '홈페이지 주소';
COMMENT ON COLUMN company.mnfctDivCd IS '제조/공급 구분코드';
COMMENT ON COLUMN company.mnfctDivNm IS '제조/공급 구분명';
COMMENT ON COLUMN company.empLyeNum IS '종업원 수';
COMMENT ON COLUMN company.corpBsnsDivCd IS '사업분야 코드(콤마 구분)';
COMMENT ON COLUMN company.corpBsnsDivNm IS '사업분야 명(콤마 구분)';
COMMENT ON COLUMN company.hdOffceDivNm IS '본사/지사 구분';
COMMENT ON COLUMN company.rgstDt IS '최초 등록일시';
COMMENT ON COLUMN company.chgDt IS '최근 변경일시';
COMMENT ON COLUMN company.esntlNoCertRgstYn IS '필수번호 인증 등록 여부';
COMMENT ON COLUMN company.ceoNm IS '대표자명';
COMMENT ON COLUMN company.collected_at IS '데이터 수집 시각';
COMMENT ON COLUMN company.synced_at IS '마지막 동기화 시점';
COMMENT ON COLUMN company.bizstt_b_stt IS '국세청 납세자상태 (계속사업자/휴업자/폐업자)';
COMMENT ON COLUMN company.bizstt_b_stt_cd IS '국세청 납세자상태 코드 (01/02/03)';
COMMENT ON COLUMN company.bizstt_tax_type IS '국세청 과세유형 명칭';
COMMENT ON COLUMN company.bizstt_tax_type_cd IS '국세청 과세유형 코드';
COMMENT ON COLUMN company.bizstt_end_dt IS '국세청 폐업일';
COMMENT ON COLUMN company.bizstt_utcc_yn IS '국세청 단위과세전환폐업여부 (Y/N)';
COMMENT ON COLUMN company.bizstt_tax_type_change_dt IS '국세청 최근과세유형전환일자';
COMMENT ON COLUMN company.bizstt_invoice_apply_dt IS '국세청 세금계산서적용일자';
COMMENT ON COLUMN company.bizstt_rbf_tax_type IS '국세청 직전과세유형 명칭';
COMMENT ON COLUMN company.bizstt_rbf_tax_type_cd IS '국세청 직전과세유형 코드';
COMMENT ON COLUMN company.bizstt_status_updated_at IS '국세청 상태 조회 시각';
COMMENT ON COLUMN company.has_bid IS '투찰 이력 여부 (후처리 계산)';
COMMENT ON COLUMN company.bid_count IS '투찰 횟수 (후처리 계산)';



INSERT INTO company (bizno, corpnm)
VALUES ('__DEFAULT__', '미확인업체')
ON CONFLICT DO NOTHING;

