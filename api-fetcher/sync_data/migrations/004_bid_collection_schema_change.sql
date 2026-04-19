-- 004_bid_collection_schema_change.sql
-- 투찰데이터 수집 방식 변경에 따른 스키마 변경
-- 관련 문서: docs/bid_data_collection_issue.md
-- 생성일: 2026-01-26
--
-- 전략:
--   - 새 컬럼 추가 후 새 API로 수집/동기화
--   - 완료 후 기존 레거시 컬럼 삭제 예정
--   - 기존 데이터 마이그레이션 없음

-- ========================================
-- 1. notice 테이블 변경
-- ========================================

-- 1.1 개찰결과 API (오퍼레이션 5,6,7,8) 필드 추가
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS actual_opengdt TIMESTAMP;           -- 실제 개찰일시 (개찰결과 API의 opengDt)
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS openg_result_inptdt TIMESTAMP;      -- 개찰결과 입력일시 (개찰결과 API의 inptDt)
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS bidclsfcno TEXT;                    -- 입찰분류번호
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS rbidno TEXT;                        -- 재입찰번호
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS prtcptcnum INTEGER;                 -- 참가업체수
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS opengcorpinfo TEXT;                 -- 개찰업체정보 (업체명^사업자번호^대표자명^투찰금액^투찰율)
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS progrsdivcdnm TEXT;                 -- 진행구분코드명 (개찰완료/유찰/재입찰)
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS rsrvtnprcefileexistnceyn TEXT;      -- 예비가격파일존재여부
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS opengrsltntccntnts TEXT;            -- 개찰결과공지내용

-- 1.2 수집 플래그 컬럼 추가
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS openg_result_collected BOOLEAN DEFAULT FALSE; -- 개찰결과 수집 완료 여부
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS bid_collected BOOLEAN DEFAULT FALSE;          -- 투찰데이터 수집 완료 여부

-- 1.3 동기화 시점 컬럼 추가
ALTER TABLE data.notice ADD COLUMN IF NOT EXISTS openg_result_synced_at TIMESTAMPTZ; -- 개찰결과 동기화 시점

-- 1.4 컬럼 코멘트
COMMENT ON COLUMN data.notice.actual_opengdt IS '실제 개찰일시 (개찰결과 API의 opengDt, 입찰공고의 opengdt는 예정 개찰일시)';
COMMENT ON COLUMN data.notice.openg_result_inptdt IS '개찰결과 입력일시 (개찰결과 API의 inptDt)';
COMMENT ON COLUMN data.notice.bidclsfcno IS '입찰분류번호 (개찰결과 API)';
COMMENT ON COLUMN data.notice.rbidno IS '재입찰번호 (개찰결과 API)';
COMMENT ON COLUMN data.notice.prtcptcnum IS '참가업체수 (개찰결과 API)';
COMMENT ON COLUMN data.notice.opengcorpinfo IS '개찰업체정보 (업체명^사업자번호^대표자명^투찰금액^투찰율)';
COMMENT ON COLUMN data.notice.progrsdivcdnm IS '진행구분코드명 (개찰완료/유찰/재입찰)';
COMMENT ON COLUMN data.notice.rsrvtnprcefileexistnceyn IS '예비가격파일존재여부';
COMMENT ON COLUMN data.notice.opengrsltntccntnts IS '개찰결과공지내용';
COMMENT ON COLUMN data.notice.openg_result_collected IS '개찰결과 수집 완료 여부 (TRUE=수집완료)';
COMMENT ON COLUMN data.notice.bid_collected IS '투찰데이터 수집 완료 여부 (TRUE=수집완료)';
COMMENT ON COLUMN data.notice.openg_result_synced_at IS '개찰결과 동기화 시점';

-- 1.5 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_notice_progrsdivcdnm ON data.notice (progrsdivcdnm);
CREATE INDEX IF NOT EXISTS idx_notice_openg_result_collected ON data.notice (openg_result_collected) WHERE openg_result_collected = FALSE;
CREATE INDEX IF NOT EXISTS idx_notice_opengdt_openg_result ON data.notice (opengdt, openg_result_collected) WHERE openg_result_collected = FALSE;
CREATE INDEX IF NOT EXISTS idx_notice_bid_collected ON data.notice (bid_collected) WHERE bid_collected = FALSE;
CREATE INDEX IF NOT EXISTS idx_notice_opengdt_bid_collected ON data.notice (opengdt, bid_collected) WHERE bid_collected = FALSE;


-- ========================================
-- 2. 레거시 컬럼 삭제 (나중에 실행)
-- ========================================
-- 새 API 수집/동기화 완료 후 실행할 것
--
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS opengdate;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS opengtm;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS opengrsltdivnm;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfamt;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfrt;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfdate;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfcorpnm;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfcorpceonm;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfcorpofclnm;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfcorpbizrno;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfcorpadrs;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS fnlsucsfcorpcontacttel;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS cntrctcnclssttusNm;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS bidwinrdcsnmthdnm;
-- ALTER TABLE data.notice DROP COLUMN IF EXISTS win_synced_at;
