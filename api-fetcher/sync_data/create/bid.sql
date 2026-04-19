-- bid 테이블: 개찰결과 (개찰완료/유찰/재입찰) 통합 테이블
-- 소스: 낙찰정보서비스.개찰결과개찰완료목록조회, 유찰목록조회, 재입찰목록조회

CREATE TABLE IF NOT EXISTS {schema}.bid (
    -- 복합 PK
    bidntceno VARCHAR(20) NOT NULL,          -- 입찰공고번호
    bidntceord VARCHAR(3) NOT NULL,          -- 입찰공고차수
    bidclsfcno VARCHAR(10) NOT NULL,         -- 입찰분류번호
    rbidno VARCHAR(3) NOT NULL,              -- 재입찰번호
    prcbdrbizno VARCHAR(20) NOT NULL DEFAULT '',  -- 투찰자 사업자등록번호 (PK용 빈문자열)

    opengrsltdivnm VARCHAR(20) NOT NULL,     -- 개찰결과구분 (개찰완료/유찰/재입찰)

    -- 개찰완료 전용 필드
    prcbdrnm VARCHAR(200),                   -- 투찰자명
    prcbdrceonm VARCHAR(100),                -- 투찰자 대표자명
    bidprcamt BIGINT,                        -- 투찰금액
    bidprcdt TIMESTAMP,                      -- 투찰일시
    bidprcrt NUMERIC,                        -- 투찰률
    opengrank INTEGER,                       -- 개찰순위
    drwtno1 VARCHAR(20),                     -- 추첨번호1
    drwtno2 VARCHAR(20),                     -- 추첨번호2
    bidprceevlval VARCHAR(50),               -- 입찰가격평가값
    techevlval VARCHAR(50),                  -- 기술평가값
    techevlnaturval VARCHAR(50),             -- 기술평가환산값
    totalevlamtval VARCHAR(50),              -- 종합평가금액값
    cnsttyaccotbidamturl TEXT,               -- 공종별내역투찰금액URL
    rmrk TEXT,                               -- 비고

    -- 유찰 전용 필드
    nobidrsn VARCHAR(500),                   -- 유찰사유

    -- 재입찰 전용 필드
    rbidrsn VARCHAR(500),                    -- 재입찰사유
    bidclsedt TIMESTAMP,                     -- 입찰마감일시 (재입찰)
    opengdt TIMESTAMP,                       -- 개찰일시 (재입찰)
    cmmnspldmdagrmntclsedt TIMESTAMP,        -- 공동수급협정마감일시

    -- 메타데이터
    collected_at TIMESTAMP,                  -- MongoDB 수집일시
    synced_at TIMESTAMP DEFAULT NOW(),       -- PostgreSQL 동기화일시

    -- 복합 Primary Key
    PRIMARY KEY (bidntceno, bidntceord, bidclsfcno, rbidno, prcbdrbizno)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_bid_bidntceno ON {schema}.bid(bidntceno);
CREATE INDEX IF NOT EXISTS idx_bid_opengrsltdivnm ON {schema}.bid(opengrsltdivnm);
CREATE INDEX IF NOT EXISTS idx_bid_prcbdrbizno ON {schema}.bid(prcbdrbizno);
CREATE INDEX IF NOT EXISTS idx_bid_bidprcdt ON {schema}.bid(bidprcdt);
CREATE INDEX IF NOT EXISTS idx_bid_collected_at ON {schema}.bid(collected_at);

-- 코멘트
COMMENT ON TABLE {schema}.bid IS '개찰결과 통합 테이블 (개찰완료/유찰/재입찰)';
COMMENT ON COLUMN {schema}.bid.opengrsltdivnm IS '개찰결과구분: 개찰완료, 유찰, 재입찰';
COMMENT ON COLUMN {schema}.bid.prcbdrbizno IS '투찰자 사업자등록번호 (개찰완료만)';
COMMENT ON COLUMN {schema}.bid.nobidrsn IS '유찰사유 (유찰만)';
COMMENT ON COLUMN {schema}.bid.rbidrsn IS '재입찰사유 (재입찰만)';
