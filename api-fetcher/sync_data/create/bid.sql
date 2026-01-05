CREATE TABLE IF NOT EXISTS bid
(
    /* 공고 식별자 */
    bidNtceNo        TEXT NOT NULL,
    bidNtceOrd       TEXT NOT NULL,

    /* 금액 정보 */
    presmptPrce      BIGINT,           -- 예정가격
    rsrvtnPrce       BIGINT,           -- 예약가격
    bssAmt           BIGINT,           -- 기초금액
    sucsfLwstlmtRt   NUMERIC,          -- 낙찰하한율

    /* 투찰 정보 */
    opengRank        INTEGER,          -- 개찰순위
    bidprcCorpBizrno TEXT NOT NULL,    -- 입찰업체사업자등록번호
    bidprcAmt        BIGINT,           -- 입찰금액
    bidprcRt         NUMERIC,          -- 입찰률
    bidprcDate       DATE,             -- 입찰일자
    bidprcTm         TIME,             -- 입찰시간
    sucsfYn          TEXT,             -- 낙찰여부
    dqlfctnRsn       TEXT,             -- 탈락사유

    /* 계산 컬럼 (후처리 UPDATE) */
    bid_rate         NUMERIC,          -- 사정률 기준 투찰률
    bid_rate_diff    NUMERIC,          -- 사정률 기준 투찰률 차이 (bid_rate - 100)

    /* 메타 */
    collected_at     TIMESTAMPTZ,      -- 수집시각
    synced_at        TIMESTAMPTZ,      -- 마지막 동기화 시점

    /* 제약 조건 */
    PRIMARY KEY (bidNtceNo, bidNtceOrd, bidprcCorpBizrno),
    FOREIGN KEY (bidNtceNo, bidNtceOrd) REFERENCES notice (bidNtceNo, bidNtceOrd),
    FOREIGN KEY (bidprcCorpBizrno) REFERENCES company (bizno)
);

/* 컬럼 주석 */
COMMENT ON TABLE bid IS '투찰 정보';

COMMENT ON COLUMN bid.bidNtceNo IS '입찰공고번호';
COMMENT ON COLUMN bid.bidNtceOrd IS '입찰공고차수';
COMMENT ON COLUMN bid.presmptPrce IS '예정가격';
COMMENT ON COLUMN bid.rsrvtnPrce IS '예약가격';
COMMENT ON COLUMN bid.bssAmt IS '기초금액';
COMMENT ON COLUMN bid.sucsfLwstlmtRt IS '낙찰하한율 (낙찰 최저 제한율)';
COMMENT ON COLUMN bid.opengRank IS '개찰순위';
COMMENT ON COLUMN bid.bidprcCorpBizrno IS '입찰업체사업자등록번호';
COMMENT ON COLUMN bid.bidprcAmt IS '입찰금액';
COMMENT ON COLUMN bid.bidprcRt IS '입찰률';
COMMENT ON COLUMN bid.bidprcDate IS '입찰일자';
COMMENT ON COLUMN bid.bidprcTm IS '입찰시간';
COMMENT ON COLUMN bid.sucsfYn IS '낙찰여부';
COMMENT ON COLUMN bid.dqlfctnRsn IS '탈락사유';
COMMENT ON COLUMN bid.bid_rate IS '사정률 기준 투찰률 (후처리 계산)';
COMMENT ON COLUMN bid.bid_rate_diff IS '사정률 기준 투찰률 차이 (bid_rate - 100)';
COMMENT ON COLUMN bid.collected_at IS '수집시각';
COMMENT ON COLUMN bid.synced_at IS '마지막 동기화 시점';

/* 인덱스 */
CREATE INDEX IF NOT EXISTS idx_bid_ntce ON bid(bidNtceNo, bidNtceOrd);
CREATE INDEX IF NOT EXISTS idx_bid_corp ON bid(bidprcCorpBizrno);
