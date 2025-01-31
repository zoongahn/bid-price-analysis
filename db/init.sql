DROP TABLE IF EXISTS notices CASCADE;
DROP TABLE IF EXISTS companies CASCADE;
DROP TABLE IF EXISTS bids CASCADE;

CREATE TABLE notices
(
    id       SERIAL PRIMARY KEY,
    "공고번호"   VARCHAR(50) UNIQUE NOT NULL,
    "입찰년도"   NUMERIC            NOT NULL,
    "공고제목"   TEXT               NOT NULL,
    "발주처"    TEXT               NOT NULL,
    "지역제한"   VARCHAR(50)        NOT NULL,
    "기초금액"   NUMERIC,
    "예정가격"   NUMERIC,
    "예가범위"   VARCHAR(50),
    "A값"     NUMERIC            NOT NULL,
    "투찰률"    NUMERIC,
    "참여업체수"  NUMERIC            NOT NULL,
    "공고구분표시" VARCHAR(100),
    "정답사정률"  NUMERIC
);

CREATE TABLE companies
(
    id         SERIAL PRIMARY KEY,
    "사업자 등록번호" VARCHAR(20) UNIQUE NOT NULL,
    "업체명"      VARCHAR(255)       NOT NULL,
    "대표명"      VARCHAR(30)
);

CREATE TABLE bids
(
    id         SERIAL PRIMARY KEY,
    notice_id  INTEGER REFERENCES notices (id),
    company_id INTEGER REFERENCES companies (id),
    "순위"       INTEGER NOT NULL,
    "투찰금액"     NUMERIC,
    "가격점수"     NUMERIC,
    "예가대비 투찰률" NUMERIC,
    "기초대비 투찰률" NUMERIC,
    "기초대비 사정률" NUMERIC,
    "추첨번호"     VARCHAR(30),
    "낙찰여부"     BOOLEAN NOT NULL,
    "투찰일시"     TIMESTAMP,
    "비고"       VARCHAR(100)
);
