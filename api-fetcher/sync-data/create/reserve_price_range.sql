CREATE TABLE IF NOT EXISTS reserve_price_range
(
    /* 공고 식별자 */
    bidNtceNo                TEXT     NOT NULL,
    bidNtceOrd               TEXT     NOT NULL,

    /* 구간 번호(1‑15) : compnoRsrvtnPrceSno */
    range_no                 SMALLINT NOT NULL,

    /* ── 금액/지표 ───────────────────── */
    plnprc                   NUMERIC,     -- 예정가격(플랜가격)
    bssamt                   NUMERIC,     -- 기초금액
    bsisPlnprc               NUMERIC,     -- 기초예정가격
    bssamtBssUpNum           SMALLINT,    -- 기초금액(실제) 상향 번호
    PrearngPrcePurcnstcst    NUMERIC,     -- 기초금액 순공사비 (채워져 있으면 숫자, 없으면 NULL)

    /* ── 예가 생성/추첨 정보 ───────────── */
    totRsrvtnPrceNum         SMALLINT,    -- 총 예가 건수(보통 15)
    drwtYn                   CHAR(1),     -- 추첨 여부(Y/N)
    drwtNum                  SMALLINT,    -- 추첨 번호(대표값 1‑15)
    compnoRsrvtnPrceMkngDt   TIMESTAMP,   -- 예가 생성일시
    rlOpengDt                TIMESTAMP,   -- 실제 개찰일시

    /* 기타 */
    bidwinrSlctnAplBssCntnts TEXT,        -- 낙찰자 결정 적용기준
    bidClsfcNo               TEXT,        -- 입찰분류번호(원본필드)
    rbidNo                   TEXT,        -- 재입찰번호(원본필드)
    inptDt                   TIMESTAMP,   -- 입력일시
    collected_at             TIMESTAMPTZ, -- 크롤링 수집 시각

    /* ── 제약 조건 ─────────────────── */
    PRIMARY KEY (bidNtceNo, bidNtceOrd, range_no),

    /* 공고 테이블과의 연계 (notice 의 PK 와 맞춰 두었을 경우) */
    FOREIGN KEY (bidNtceNo, bidNtceOrd)
        REFERENCES notice (bidNtceNo, bidNtceOrd)
        ON DELETE CASCADE
);

COMMENT ON TABLE reserve_price_range IS '공고별 복수예정가격(예가) 구간 정보';
COMMENT ON COLUMN reserve_price_range.bidNtceNo IS '입찰공고번호';
COMMENT ON COLUMN reserve_price_range.bidNtceOrd IS '입찰공고차수';
COMMENT ON COLUMN reserve_price_range.range_no IS '예가 구간 번호(1‑15)';
COMMENT ON COLUMN reserve_price_range.plnprc IS '예정가격(플랜가격)';
COMMENT ON COLUMN reserve_price_range.bssamt IS '기초금액';
COMMENT ON COLUMN reserve_price_range.bsisPlnprc IS '기초예정가격';
COMMENT ON COLUMN reserve_price_range.totRsrvtnPrceNum IS '총 예가 건수';
COMMENT ON COLUMN reserve_price_range.drwtYn IS '추첨 여부(Y/N)';
COMMENT ON COLUMN reserve_price_range.drwtNum IS '추첨 번호(대표 예가)';
COMMENT ON COLUMN reserve_price_range.compnoRsrvtnPrceMkngDt IS '예가 생성(작성) 일시';
COMMENT ON COLUMN reserve_price_range.rlOpengDt IS '실제 개찰 일시';
COMMENT ON COLUMN reserve_price_range.bidwinrSlctnAplBssCntnts IS '낙찰자 결정 적용기준';
COMMENT ON COLUMN reserve_price_range.inptDt IS '데이터 입력 일시';
COMMENT ON COLUMN reserve_price_range.collected_at IS '데이터 수집(ETL) 시각';


-- 복수예가 -> 해당 구간 사정률(총 15개)
-- floor_5dp(user-defined-func.sql)이 UDP로써 미리 정의되어있어야함.
ALTER TABLE reserve_price_range
    ADD COLUMN bssamt_to_bsisplnprc_ratio NUMERIC GENERATED ALWAYS AS (
        CASE
            WHEN bssamt IS NOT NULL AND bssamt != 0 THEN ((bsisPlnprc / bssamt) - 1) * 100
            ELSE NULL
            END
        ) STORED;

ALTER TABLE reserve_price_range
    ADD COLUMN bssamt_to_bsisplnprc_ratio_floor NUMERIC GENERATED ALWAYS AS (
        CASE
            WHEN bssamt IS NOT NULL AND bssamt != 0 THEN floor_5dp(((bsisPlnprc / bssamt) - 1) * 100)
            ELSE NULL
            END
        ) STORED;

alter table reserve_price_range
    drop COLUMN bssamt_to_bsisplnprc_ratio_floor;

alter table reserve_price_range
    drop COLUMN bssamt_to_bsisplnprc_ratio;