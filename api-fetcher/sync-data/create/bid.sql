CREATE TABLE IF NOT EXISTS bid
(
    bidNtceNo        TEXT,
    bidNtceOrd       TEXT,
    bidNtceNm        TEXT,
    bsnsDivNm        TEXT,
    presmptPrce      BIGINT,
    rsrvtnPrce       BIGINT,
    bssAmt           BIGINT,

    opengRank        INTEGER,
    bidprcCorpBizrno TEXT,
    bidprcCorpNm     TEXT,
    bidprcCorpCeoNm  TEXT,
    bidprcAmt        BIGINT,
    bidprcRt         NUMERIC,
    bidprcDate       DATE,
    bidprcTm         TIME,
    sucsfYn          TEXT,
    dqlfctnRsn       TEXT,
    collected_at     TIMESTAMP,

    PRIMARY KEY (bidNtceNo, bidNtceOrd, bidprcCorpBizrno),
    FOREIGN KEY (bidNtceNo, bidNtceOrd) REFERENCES notice (bidNtceNo, bidNtceOrd),
    FOREIGN KEY (bidprcCorpBizrno) REFERENCES company (bizno)
);

COMMENT ON COLUMN bid.bidNtceNo IS '입찰공고번호';
COMMENT ON COLUMN bid.bidNtceOrd IS '입찰공고차수';
COMMENT ON COLUMN bid.bidNtceNm IS '입찰공고명';
COMMENT ON COLUMN bid.bsnsDivNm IS '사업구분명';
COMMENT ON COLUMN bid.presmptPrce IS '예정가격';
COMMENT ON COLUMN bid.rsrvtnPrce IS '예약가격';
COMMENT ON COLUMN bid.bssAmt IS '기초금액';

COMMENT ON COLUMN bid.opengRank IS '개찰순위';
COMMENT ON COLUMN bid.bidprcCorpBizrno IS '입찰업체사업자등록번호';
COMMENT ON COLUMN bid.bidprcCorpNm IS '입찰업체명';
COMMENT ON COLUMN bid.bidprcCorpCeoNm IS '입찰업체대표자명';
COMMENT ON COLUMN bid.bidprcAmt IS '입찰금액';
COMMENT ON COLUMN bid.bidprcRt IS '입찰률';
COMMENT ON COLUMN bid.bidprcDate IS '입찰일자';
COMMENT ON COLUMN bid.bidprcTm IS '입찰시간';
COMMENT ON COLUMN bid.sucsfYn IS '성공여부';
COMMENT ON COLUMN bid.dqlfctnRsn IS '탈락사유';
COMMENT ON COLUMN bid.collected_at IS '수집시각';
