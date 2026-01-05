CREATE TABLE IF NOT EXISTS institution
(
    /* 고유 식별자 */
    dminsttCd              TEXT PRIMARY KEY, -- 수요기관코드

    /* 기관명 */
    dminsttNm              TEXT NOT NULL,    -- 수요기관명
    dminsttAbrvtNm         TEXT,             -- 수요기관약칭명
    dminsttEngNm           TEXT,             -- 수요기관영문명

    /* 법인/사업자 정보 */
    corprtRgstNo           TEXT,             -- 법인등록번호
    bizno                  TEXT,             -- 사업자등록번호

    /* 유효기간 */
    vldPrdBgnDt            TEXT,             -- 유효기간시작일자
    vldPrdEndDt            TEXT,             -- 유효기간종료일자

    /* 기관 분류 */
    jrsdctnDivNm           TEXT,             -- 관할구분명 (국가기관, 지방자치단체, 기타기관)
    insttTyCdLrgclsfcNm    TEXT,             -- 기관유형대분류명
    insttTyCdMidclsfcNm    TEXT,             -- 기관유형중분류명
    insttTyCdSmlclsfcNm    TEXT,             -- 기관유형소분류명

    /* 업종 정보 */
    bizcndtnNm             TEXT,             -- 업태명
    indstrytyNm            TEXT,             -- 업종명

    /* 소재지 */
    rgnCd                  TEXT,             -- 행정구역코드
    rgnNm                  TEXT,             -- 행정구역명
    zip                    TEXT,             -- 우편번호
    adrs                   TEXT,             -- 주소
    dtlAdrs                TEXT,             -- 상세주소

    /* 연락처 */
    telNo                  TEXT,             -- 전화번호
    faxNo                  TEXT,             -- 팩스번호
    ofclFaxNo              TEXT,             -- 대표팩스번호
    hmpgAdrs               TEXT,             -- 홈페이지주소

    /* 상위기관 정보 */
    toplvlInsttCd          TEXT,             -- 최상위기관코드
    toplvlInsttNm          TEXT,             -- 최상위기관명

    /* 상태 정보 */
    dltYn                  CHAR(1),          -- 삭제여부 (Y/N)

    /* 행정 정보 */
    rgstDt                 TIMESTAMP,        -- 등록일시
    chgDt                  TIMESTAMP,        -- 변경일시

    /* 메타 */
    collected_at           TIMESTAMPTZ,      -- 수집시각
    synced_at              TIMESTAMPTZ       -- 마지막 동기화 시점
);

/* ──────────────────────────────────────────────────────────────────────────
   컬럼 주석
   ────────────────────────────────────────────────────────────────────────── */

COMMENT ON TABLE institution IS '수요기관(발주기관) 정보';

COMMENT ON COLUMN institution.dminsttCd IS '수요기관코드 (PK)';
COMMENT ON COLUMN institution.dminsttNm IS '수요기관명';
COMMENT ON COLUMN institution.dminsttAbrvtNm IS '수요기관약칭명';
COMMENT ON COLUMN institution.dminsttEngNm IS '수요기관영문명';
COMMENT ON COLUMN institution.corprtRgstNo IS '법인등록번호';
COMMENT ON COLUMN institution.bizno IS '사업자등록번호';
COMMENT ON COLUMN institution.vldPrdBgnDt IS '유효기간시작일자';
COMMENT ON COLUMN institution.vldPrdEndDt IS '유효기간종료일자';
COMMENT ON COLUMN institution.jrsdctnDivNm IS '관할구분명 (국가기관, 지방자치단체, 기타기관)';
COMMENT ON COLUMN institution.insttTyCdLrgclsfcNm IS '기관유형대분류명';
COMMENT ON COLUMN institution.insttTyCdMidclsfcNm IS '기관유형중분류명';
COMMENT ON COLUMN institution.insttTyCdSmlclsfcNm IS '기관유형소분류명';
COMMENT ON COLUMN institution.bizcndtnNm IS '업태명';
COMMENT ON COLUMN institution.indstrytyNm IS '업종명';
COMMENT ON COLUMN institution.rgnCd IS '행정구역코드';
COMMENT ON COLUMN institution.rgnNm IS '행정구역명';
COMMENT ON COLUMN institution.zip IS '우편번호';
COMMENT ON COLUMN institution.adrs IS '주소';
COMMENT ON COLUMN institution.dtlAdrs IS '상세주소';
COMMENT ON COLUMN institution.telNo IS '전화번호';
COMMENT ON COLUMN institution.faxNo IS '팩스번호';
COMMENT ON COLUMN institution.ofclFaxNo IS '대표팩스번호';
COMMENT ON COLUMN institution.hmpgAdrs IS '홈페이지주소';
COMMENT ON COLUMN institution.toplvlInsttCd IS '최상위기관코드';
COMMENT ON COLUMN institution.toplvlInsttNm IS '최상위기관명';
COMMENT ON COLUMN institution.dltYn IS '삭제여부 (Y/N)';
COMMENT ON COLUMN institution.rgstDt IS '등록일시';
COMMENT ON COLUMN institution.chgDt IS '변경일시';
COMMENT ON COLUMN institution.collected_at IS '데이터 수집 시각';
COMMENT ON COLUMN institution.synced_at IS '마지막 동기화 시점';

/* 인덱스 */
CREATE INDEX IF NOT EXISTS idx_institution_bizno ON institution(bizno);
CREATE INDEX IF NOT EXISTS idx_institution_rgn ON institution(rgnCd);
CREATE INDEX IF NOT EXISTS idx_institution_toplvl ON institution(toplvlInsttCd);
