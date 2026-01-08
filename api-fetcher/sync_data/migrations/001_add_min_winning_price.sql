-- Migration: 001_add_min_winning_price
-- 날짜: 2026-01-05
-- 설명:
--   1. TEXT → NUMERIC 타입 변경 (금액/비율 컬럼)
--   2. min_winning_price 컬럼 추가
--   3. min_winning_price 값 계산 및 UPDATE

-- ========================================
-- 1. TEXT → NUMERIC 타입 변경
-- ========================================

-- 1.1 bssamtpurcnstcst (기초금액순공사비)
ALTER TABLE notice
    ALTER COLUMN bssamtpurcnstcst TYPE NUMERIC
    USING NULLIF(TRIM(bssamtpurcnstcst), '')::NUMERIC;

-- 1.2 maincnsttycnstwkprearngamt (주공종공사예정금액)
ALTER TABLE notice
    ALTER COLUMN maincnsttycnstwkprearngamt TYPE NUMERIC
    USING NULLIF(TRIM(maincnsttycnstwkprearngamt), '')::NUMERIC;

-- 1.3 maincnsttypresmptprce (주공종추정가격)
ALTER TABLE notice
    ALTER COLUMN maincnsttypresmptprce TYPE NUMERIC
    USING NULLIF(TRIM(maincnsttypresmptprce), '')::NUMERIC;

-- 1.4 bidprtcptfee (입찰참가수수료)
ALTER TABLE notice
    ALTER COLUMN bidprtcptfee TYPE NUMERIC
    USING NULLIF(TRIM(bidprtcptfee), '')::NUMERIC;

-- 1.5 indstrytyevlrt (업종평가비율)
ALTER TABLE notice
    ALTER COLUMN indstrytyevlrt TYPE NUMERIC
    USING NULLIF(TRIM(indstrytyevlrt), '')::NUMERIC;

-- 1.6 rgndutyjntcontrctrt (지역의무공동도급비율)
ALTER TABLE notice
    ALTER COLUMN rgndutyjntcontrctrt TYPE NUMERIC
    USING NULLIF(TRIM(rgndutyjntcontrctrt), '')::NUMERIC;

-- 1.7 subsicnsttyindstrytyevlrt1~9 (부공종업종평가비율)
ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt1 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt1), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt2 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt2), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt3 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt3), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt4 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt4), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt5 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt5), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt6 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt6), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt7 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt7), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt8 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt8), '')::NUMERIC;

ALTER TABLE notice
    ALTER COLUMN subsicnsttyindstrytyevlrt9 TYPE NUMERIC
    USING NULLIF(TRIM(subsicnsttyindstrytyevlrt9), '')::NUMERIC;

-- 1.8 prdctqty (물품수량)
ALTER TABLE notice
    ALTER COLUMN prdctqty TYPE NUMERIC
    USING NULLIF(TRIM(prdctqty), '')::NUMERIC;

-- 1.9 prdctuprc (물품단가)
ALTER TABLE notice
    ALTER COLUMN prdctuprc TYPE NUMERIC
    USING NULLIF(TRIM(prdctuprc), '')::NUMERIC;

-- ========================================
-- 2. min_winning_price 컬럼 추가
-- ========================================

ALTER TABLE notice
    ADD COLUMN IF NOT EXISTS min_winning_price NUMERIC;

COMMENT ON COLUMN notice.min_winning_price IS '낙찰하한가 (후처리 계산)';

-- ========================================
-- 3. min_winning_price 값 계산 (후처리)
-- ========================================
-- 계산 공식:
--   - bssamtpurcnstcst가 NULL인 경우: (plnprc - a_value) * (sucsfbidlwltrate / 100) + a_value
--   - bssamtpurcnstcst가 존재하는 경우: GREATEST(위 값, bssamtpurcnstcst * (answer_rate / 100) * 0.98)

-- 후처리 스크립트 실행으로 대체:
-- python -m sync_data.postprocess.update_notice_stats

-- 또는 직접 실행:
/*
UPDATE notice n
SET min_winning_price = (
    SELECT
        CASE
            WHEN n.bssamtpurcnstcst IS NULL THEN
                (r.plnprc - COALESCE(n.a_value, 0)) * (COALESCE(n.sucsfbidlwltrate, 87.745) / 100) + COALESCE(n.a_value, 0)
            ELSE
                GREATEST(
                    (r.plnprc - COALESCE(n.a_value, 0)) * (COALESCE(n.sucsfbidlwltrate, 87.745) / 100) + COALESCE(n.a_value, 0),
                    n.bssamtpurcnstcst * (COALESCE(n.answer_rate, 100) / 100) * 0.98
                )
        END
    FROM reserve_price_range r
    WHERE r.bidntceno = n.bidntceno
      AND r.bidntceord = n.bidntceord
    LIMIT 1
)
WHERE n.sucsfbidlwltrate IS NOT NULL;
*/
