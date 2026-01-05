-- Active: 1759025182018@@127.0.0.1@5432@GFCON_PSQL
-- 업종 정보 테이블 (마스터 데이터)
-- 입찰공고의 업종 제한에 사용되는 업종 정보를 관리하는 테이블

DROP TABLE IF EXISTS notice_industry_type_info;

CREATE TABLE IF NOT EXISTS notice_industry_type_info (
    industry_code TEXT PRIMARY KEY,
    classification_code TEXT NOT NULL,
    classification_name TEXT NOT NULL,
    industry_name TEXT NOT NULL,
    legal_basis TEXT,
    related_regulations TEXT,
    last_modified_date DATE
);

-- 컬럼 설명
COMMENT ON TABLE notice_industry_type_info IS '업종 정보 테이블 (마스터 데이터)';

COMMENT ON COLUMN notice_industry_type_info.industry_code IS '업종코드 (예: 0001, 0002) - Primary Key';
COMMENT ON COLUMN notice_industry_type_info.classification_code IS '분류코드 (예: 49-건설업, 61-정보통신)';
COMMENT ON COLUMN notice_industry_type_info.classification_name IS '업종분류명 (예: 건설업, 정보통신)';
COMMENT ON COLUMN notice_industry_type_info.industry_name IS '업종명 (예: 토목공사업, 건축공사업)';
COMMENT ON COLUMN notice_industry_type_info.legal_basis IS '근거법령';
COMMENT ON COLUMN notice_industry_type_info.related_regulations IS '관련규정';
COMMENT ON COLUMN notice_industry_type_info.last_modified_date IS '최종변경일시';

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_notice_industry_type_info_classification ON notice_industry_type_info (
    classification_code,
    classification_name
);

CREATE INDEX IF NOT EXISTS idx_notice_industry_type_info_industry_name ON notice_industry_type_info (industry_name);