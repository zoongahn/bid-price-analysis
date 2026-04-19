-- Migration: 005_split_opengcorpinfo
-- 날짜: 2026-02-02
-- 설명:
--   1. opengcorpinfo (개찰업체정보) 컬럼을 분리하여 낙찰업체 정보를 개별 컬럼으로 저장
--      형식: 업체명^사업자번호^대표자명^투찰금액^투찰율
--   2. bid_count 컬럼 삭제 (prtcptcnum으로 대체)

-- ========================================
-- 1. 낙찰업체 정보 컬럼 추가
-- ========================================

ALTER TABLE test.notice ADD COLUMN IF NOT EXISTS winner_corpnm TEXT;
ALTER TABLE test.notice ADD COLUMN IF NOT EXISTS winner_bizno TEXT;
ALTER TABLE test.notice ADD COLUMN IF NOT EXISTS winner_ceonm TEXT;
ALTER TABLE test.notice ADD COLUMN IF NOT EXISTS winner_bidamt BIGINT;
ALTER TABLE test.notice ADD COLUMN IF NOT EXISTS winner_plnprc_rate NUMERIC;

COMMENT ON COLUMN test.notice.winner_corpnm IS '낙찰업체명 (opengcorpinfo에서 분리)';
COMMENT ON COLUMN test.notice.winner_bizno IS '낙찰업체 사업자등록번호';
COMMENT ON COLUMN test.notice.winner_ceonm IS '낙찰업체 대표자명';
COMMENT ON COLUMN test.notice.winner_bidamt IS '낙찰업체 투찰금액';
COMMENT ON COLUMN test.notice.winner_plnprc_rate IS '낙찰업체 예가대비투찰률 = (투찰금액-A값)/(예정가격-A값)×100';

-- ========================================
-- 2. 기존 데이터 분리 (일회성)
-- ========================================

UPDATE test.notice
SET
    winner_corpnm = NULLIF(TRIM(SPLIT_PART(opengcorpinfo, '^', 1)), ''),
    winner_bizno = NULLIF(TRIM(SPLIT_PART(opengcorpinfo, '^', 2)), ''),
    winner_ceonm = NULLIF(TRIM(SPLIT_PART(opengcorpinfo, '^', 3)), ''),
    winner_bidamt = CASE
        WHEN TRIM(SPLIT_PART(opengcorpinfo, '^', 4)) ~ '^\d+$'
        THEN TRIM(SPLIT_PART(opengcorpinfo, '^', 4))::BIGINT
        ELSE NULL
    END,
    winner_plnprc_rate = CASE
        WHEN TRIM(SPLIT_PART(opengcorpinfo, '^', 5)) ~ '^[0-9]+\.?[0-9]*$'
        THEN TRIM(SPLIT_PART(opengcorpinfo, '^', 5))::NUMERIC
        ELSE NULL
    END
WHERE opengcorpinfo IS NOT NULL AND opengcorpinfo != '';

-- ========================================
-- 3. bid_count 컬럼 삭제 (prtcptcnum으로 대체)
-- ========================================

ALTER TABLE test.notice DROP COLUMN IF EXISTS bid_count;

-- ========================================
-- 4. 인덱스 (필요시)
-- ========================================

-- CREATE INDEX IF NOT EXISTS idx_notice_winner_bizno ON test.notice (winner_bizno);
