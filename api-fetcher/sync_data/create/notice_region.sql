-- 입찰공고 참가가능지역정보 테이블
-- MongoDB: 입찰공고정보서비스.입찰공고목록정보에대한참가가능지역정보조회

DROP TABLE IF EXISTS notice_region;

CREATE TABLE IF NOT EXISTS notice_region
(
    bidntceno              TEXT NOT NULL,
    bidntceord             TEXT NOT NULL,
    lmtsno                 TEXT NOT NULL,
    prtcptpsblrgnnm        TEXT,
    rgstdt                 TIMESTAMP,
    bsnsdivnm              TEXT,

    /* 메타 */
    synced_at              TIMESTAMPTZ,      -- 마지막 동기화 시점

    PRIMARY KEY (bidntceno, bidntceord, lmtsno)
    -- FOREIGN KEY는 모든 데이터 동기화 후 추가 권장
    -- FOREIGN KEY (bidntceno, bidntceord) REFERENCES notice (bidntceno, bidntceord)
);

-- 컬럼 설명
COMMENT ON TABLE notice_region IS '입찰공고 참가가능지역정보';

COMMENT ON COLUMN notice_region.bidntceno IS '입찰공고번호';
COMMENT ON COLUMN notice_region.bidntceord IS '입찰공고차수';
COMMENT ON COLUMN notice_region.lmtsno IS '제한일련번호';
COMMENT ON COLUMN notice_region.prtcptpsblrgnnm IS '참가가능지역명';
COMMENT ON COLUMN notice_region.rgstdt IS '등록일시';
COMMENT ON COLUMN notice_region.bsnsdivnm IS '사업구분명';
COMMENT ON COLUMN notice_region.synced_at IS '마지막 동기화 시점';

-- 인덱스 생성 (조회 성능 향상)
CREATE INDEX IF NOT EXISTS idx_notice_region_bidntceno
    ON notice_region (bidntceno, bidntceord);

CREATE INDEX IF NOT EXISTS idx_notice_region_rgstdt
    ON notice_region (rgstdt);
