DROP TABLE bid;

CREATE TABLE IF NOT EXISTS bid
(
    bidNtceNo              TEXT,
    bidNtceOrd             TEXT,
    bidNtceNm              TEXT,
    bsnsDivNm              TEXT,
    cntrctCnclsSttusNm     TEXT,
    cntrctCnclsMthdNm      TEXT,
    bidwinrDcsnMthdNm      TEXT,
    ntceInsttNm            TEXT,
    ntceInsttCd            TEXT,
    dmndInsttNm            TEXT,
    dmndInsttCd            TEXT,
    sucsfLwstlmtRt         NUMERIC,
    presmptPrce            BIGINT,
    rsrvtnPrce             BIGINT,
    bssAmt                 BIGINT,
    opengDate              DATE,
    opengTm                TIME,
    opengRsltDivNm         TEXT,
    opengRank              INTEGER,
    bidprcCorpBizrno       TEXT,
    bidprcCorpNm           TEXT,
    bidprcCorpCeoNm        TEXT,
    bidprcAmt              BIGINT,
    bidprcRt               NUMERIC(5, 3),
    bidprcDate             DATE,
    bidprcTm               TIME,
    sucsfYn                TEXT,
    dqlfctnRsn             TEXT,
    fnlSucsfAmt            BIGINT,
    fnlSucsfRt             NUMERIC(5, 3),
    fnlSucsfDate           DATE,
    fnlSucsfCorpNm         TEXT,
    fnlSucsfCorpCeoNm      TEXT,
    fnlSucsfCorpOfclNm     TEXT,
    fnlSucsfCorpBizrno     TEXT,
    fnlSucsfCorpAdrs       TEXT,
    fnlSucsfCorpContactTel TEXT,
    dataBssDate            DATE,
    collected_at           TIMESTAMP,

    PRIMARY KEY (bidNtceNo, bidprcCorpBizrno)
);

COMMENT ON COLUMN bid.bidNtceNo IS '입찰공고번호';
COMMENT ON COLUMN bid.bidNtceOrd IS '입찰공고차수';
COMMENT ON COLUMN bid.bidNtceNm IS '입찰공고명';
COMMENT ON COLUMN bid.bsnsDivNm IS '사업구분명';
COMMENT ON COLUMN bid.cntrctCnclsSttusNm IS '계약체결상태명';
COMMENT ON COLUMN bid.cntrctCnclsMthdNm IS '계약체결방법명';
COMMENT ON COLUMN bid.bidwinrDcsnMthdNm IS '낙찰자결정방법명';
COMMENT ON COLUMN bid.ntceInsttNm IS '공고기관명';
COMMENT ON COLUMN bid.ntceInsttCd IS '공고기관코드';
COMMENT ON COLUMN bid.dmndInsttNm IS '수요기관명';
COMMENT ON COLUMN bid.dmndInsttCd IS '수요기관코드';
COMMENT ON COLUMN bid.sucsfLwstlmtRt IS '성공최저제한율';
COMMENT ON COLUMN bid.presmptPrce IS '예정가격';
COMMENT ON COLUMN bid.rsrvtnPrce IS '예약가격';
COMMENT ON COLUMN bid.bssAmt IS '기초금액';
COMMENT ON COLUMN bid.opengDate IS '개찰일자';
COMMENT ON COLUMN bid.opengTm IS '개찰시간';
COMMENT ON COLUMN bid.opengRsltDivNm IS '개찰결과구분명';
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
COMMENT ON COLUMN bid.fnlSucsfAmt IS '최종낙찰금액';
COMMENT ON COLUMN bid.fnlSucsfRt IS '최종낙찰률';
COMMENT ON COLUMN bid.fnlSucsfDate IS '최종낙찰일자';
COMMENT ON COLUMN bid.fnlSucsfCorpNm IS '최종낙찰업체명';
COMMENT ON COLUMN bid.fnlSucsfCorpCeoNm IS '최종낙찰업체대표자명';
COMMENT ON COLUMN bid.fnlSucsfCorpOfclNm IS '최종낙찰업체담당자명';
COMMENT ON COLUMN bid.fnlSucsfCorpBizrno IS '최종낙찰업체사업자번호';
COMMENT ON COLUMN bid.fnlSucsfCorpAdrs IS '최종낙찰업체주소';
COMMENT ON COLUMN bid.fnlSucsfCorpContactTel IS '최종낙찰업체전화번호';
COMMENT ON COLUMN bid.dataBssDate IS '데이터기준일자';
COMMENT ON COLUMN bid.collected_at IS '수집시각';
