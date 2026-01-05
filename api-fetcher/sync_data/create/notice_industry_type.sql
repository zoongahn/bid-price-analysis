-- 입찰공고 면허제한정보(업종) 테이블
-- MongoDB: 입찰공고정보서비스.입찰공고목록정보에대한면허제한정보조회

DROP TABLE IF EXISTS notice_industry_type;

CREATE TABLE IF NOT EXISTS notice_industry_type
(
    bidntceno              TEXT NOT NULL,
    bidntceord             TEXT NOT NULL,
    lmtgrpno               TEXT NOT NULL,
    lmtsno                 TEXT NOT NULL,
    lcnslmtnm_name         TEXT,
    lcnslmtnm_code         TEXT,
    permsnindstrytylist    TEXT,
    indstrytymfrcfldlist   TEXT,
    rgstdt                 TIMESTAMP,
    bsnsdivnm              TEXT,

    /* 메타 */
    synced_at              TIMESTAMPTZ,      -- 마지막 동기화 시점

    /* 분류 정보 (후처리 - meta.industry_type_info 테이블과 JOIN) */
    classification_code    TEXT,             -- 분류코드
    classification_name    TEXT,             -- 분류명

    PRIMARY KEY (bidntceno, bidntceord, lmtgrpno, lmtsno)
    -- FOREIGN KEY는 모든 데이터 동기화 후 추가 권장
    -- FOREIGN KEY (bidntceno, bidntceord) REFERENCES notice (bidntceno, bidntceord)
);

-- 컬럼 설명
COMMENT ON TABLE notice_industry_type IS '입찰공고 면허제한정보(업종)';

COMMENT ON COLUMN notice_industry_type.bidntceno IS '입찰공고번호';
COMMENT ON COLUMN notice_industry_type.bidntceord IS '입찰공고차수';
COMMENT ON COLUMN notice_industry_type.lmtgrpno IS '제한그룹번호';
COMMENT ON COLUMN notice_industry_type.lmtsno IS '제한일련번호';
COMMENT ON COLUMN notice_industry_type.lcnslmtnm_name IS '면허제한명 (이름 부분, 예: 도장공사업)';
COMMENT ON COLUMN notice_industry_type.lcnslmtnm_code IS '면허제한명 (코드 부분, 예: 0010)';
COMMENT ON COLUMN notice_industry_type.permsnindstrytylist IS '허용업종목록';
COMMENT ON COLUMN notice_industry_type.indstrytymfrcfldlist IS '업종주력분야목록';
COMMENT ON COLUMN notice_industry_type.rgstdt IS '등록일시';
COMMENT ON COLUMN notice_industry_type.bsnsdivnm IS '사업구분명';
COMMENT ON COLUMN notice_industry_type.synced_at IS '마지막 동기화 시점';
COMMENT ON COLUMN notice_industry_type.classification_code IS '분류코드 (후처리 - meta.industry_type_info JOIN)';
COMMENT ON COLUMN notice_industry_type.classification_name IS '분류명 (후처리 - meta.industry_type_info JOIN)';

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_notice_industry_type_bidntceno
    ON notice_industry_type (bidntceno, bidntceord);

CREATE INDEX IF NOT EXISTS idx_notice_industry_type_rgstdt
    ON notice_industry_type (rgstdt);
