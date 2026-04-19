-- Migration: 003_add_winner_bid_rate
-- 날짜: 2026-01-15
-- 설명:
--   1. notice 테이블에 winner_bid_rate 컬럼 추가
--   2. bid 테이블에서 1등 낙찰업체(opengRank=1)의 bid_rate를 가져와 UPDATE
--
-- 참고:
--   - bid.bid_rate는 update_bid_rates.py로 계산됨
--   - winner_bid_rate는 update_winner_bid_rate.py로 계산됨

-- ========================================
-- 1. winner_bid_rate 컬럼 추가
-- ========================================

ALTER TABLE notice
    ADD COLUMN IF NOT EXISTS winner_bid_rate NUMERIC;

COMMENT ON COLUMN notice.winner_bid_rate IS '1등 낙찰업체 사정률 (후처리 계산)';

-- ========================================
-- 2. winner_bid_rate 값 계산 및 UPDATE
-- ========================================

-- bid 테이블에서 opengRank = 1인 레코드의 bid_rate를 notice 테이블로 복사
UPDATE notice n
SET winner_bid_rate = (
    SELECT b.bid_rate
    FROM bid b
    WHERE b.bidntceno = n.bidntceno
      AND b.bidntceord = n.bidntceord
      AND b.opengRank = 1
    LIMIT 1
)
WHERE n.winner_bid_rate IS NULL;

-- ========================================
-- 3. 결과 확인 쿼리 (참고용)
-- ========================================

-- 업데이트 결과 확인:
-- SELECT
--     COUNT(*) as total,
--     COUNT(winner_bid_rate) as has_winner_bid_rate,
--     AVG(winner_bid_rate) as avg_winner_bid_rate,
--     MIN(winner_bid_rate) as min_winner_bid_rate,
--     MAX(winner_bid_rate) as max_winner_bid_rate
-- FROM notice;

-- 샘플 데이터 확인:
-- SELECT
--     n.bidntceno,
--     n.bidntceord,
--     n.fnlsucsfcorpnm,
--     n.winner_bid_rate,
--     b.bid_rate as bid_bid_rate,
--     b.bidprcamt
-- FROM notice n
-- LEFT JOIN bid b ON b.bidntceno = n.bidntceno
--     AND b.bidntceord = n.bidntceord
--     AND b.opengRank = 1
-- WHERE n.winner_bid_rate IS NOT NULL
-- LIMIT 10;
