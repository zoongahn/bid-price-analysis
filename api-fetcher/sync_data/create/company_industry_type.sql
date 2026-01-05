-- Active: 1759025182018@@127.0.0.1@5432@GFCON_PSQL
-- company_industry_type 테이블 생성
-- 업체별 업종 정보 (사용자정보서비스.조달업체업종정보조회)

DROP TABLE IF EXISTS company_industry_type CASCADE;

CREATE TABLE IF NOT EXISTS company_industry_type (
    -- Primary Key
    bizno VARCHAR(20) NOT NULL,                   -- 사업자등록번호
    indstrytycd VARCHAR(10) NOT NULL,             -- 업종코드

-- 업종 정보
indstrytynm VARCHAR(200), -- 업종명 (예: "석유판매업(주유소)")
indstrytystatsNm VARCHAR(200), -- 업종통계명
rprsntindstrytyyn CHAR(1), -- 대표업종여부 (Y/N)

-- 날짜 정보
rgstdt TIMESTAMP, -- 등록일시
vldprdexprtdt TIMESTAMP, -- 유효기간만료일시
chgdt TIMESTAMP, -- 변경일시
systmrgstdt TIMESTAMP, -- 시스템등록일시
systmchgdt TIMESTAMP, -- 시스템변경일시

-- 메타
synced_at TIMESTAMPTZ, -- 마지막 동기화 시점

-- 제약 조건
PRIMARY KEY (bizno, indstrytycd),

-- 외래키 (company 테이블 참조)
CONSTRAINT fk_company_industry_type_company
        FOREIGN KEY (bizno)
        REFERENCES company(bizno)
        ON DELETE CASCADE
);

-- 인덱스 생성
CREATE INDEX idx_company_industry_type_bizno ON company_industry_type (bizno);

CREATE INDEX idx_company_industry_type_rprsnt ON company_industry_type (bizno, rprsntindstrytyyn)
WHERE
    rprsntindstrytyyn = 'Y';

-- 테이블 코멘트
COMMENT ON TABLE company_industry_type IS '업체별 업종 정보';

COMMENT ON COLUMN company_industry_type.bizno IS '사업자등록번호';

COMMENT ON COLUMN company_industry_type.indstrytycd IS '업종코드';

COMMENT ON COLUMN company_industry_type.indstrytynm IS '업종명';

COMMENT ON COLUMN company_industry_type.indstrytystatsNm IS '업종통계명';

COMMENT ON COLUMN company_industry_type.rprsntindstrytyyn IS '대표업종여부 (Y/N)';

COMMENT ON COLUMN company_industry_type.rgstdt IS '등록일시';

COMMENT ON COLUMN company_industry_type.vldprdexprtdt IS '유효기간만료일시';

COMMENT ON COLUMN company_industry_type.chgdt IS '변경일시';

COMMENT ON COLUMN company_industry_type.systmrgstdt IS '시스템등록일시';

COMMENT ON COLUMN company_industry_type.systmchgdt IS '시스템변경일시';

COMMENT ON COLUMN company_industry_type.synced_at IS '마지막 동기화 시점';