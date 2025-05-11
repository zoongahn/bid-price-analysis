CREATE TABLE IF NOT EXISTS reserve_price_range
(
    bidNtceNo      TEXT,
    bidNtceOrd     TEXT,
    range_no       INTEGER, -- 예: 1~15 중 몇 번째 예가 구간인지
    price_min      NUMERIC, -- 구간 하한
    price_max      NUMERIC, -- 구간 상한
    bsisPlnprc     NUMERIC, -- 기초예정가격
    selected_value NUMERIC, -- 이 구간 내에서 선택된 대표값 (정답사정률 계산용)
    PRIMARY KEY (bidNtceNo, bidNtceOrd, range_no),
    FOREIGN KEY (bidNtceNo, bidNtceOrd) REFERENCES notice (bidNtceNo, bidNtceOrd)
);

COMMENT ON COLUMN reserve_price_range.bidNtceNo IS '입찰공고번호 (notice 테이블 참조)';
COMMENT ON COLUMN reserve_price_range.bidNtceOrd IS '입찰공고차수 (notice 테이블 참조)';
COMMENT ON COLUMN reserve_price_range.range_no IS '예가 구간 번호 (1~15)';
COMMENT ON COLUMN reserve_price_range.price_min IS '예가 구간 하한값';
COMMENT ON COLUMN reserve_price_range.price_max IS '예가 구간 상한값';
COMMENT ON COLUMN reserve_price_range.bsisPlnprc IS '기초예정가격';
COMMENT ON COLUMN reserve_price_range.selected_value IS '구간 내 선택된 대표값 (정답사정률 계산용)';