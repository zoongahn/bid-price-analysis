-- 원데이터와 업종 테이블 간 고아 레코드 확인
-- notice <-> notice_industry_type, company <-> company_industry_type

-- notice 기준: 공고는 있지만 업종이 없는 경우 / 업종은 있지만 공고가 없는 경우
SELECT
    '공고-업종' AS 관계,
    (SELECT COUNT(DISTINCT (bidntceno, bidntceord))
     FROM data.notice n
     WHERE NOT EXISTS (
         SELECT 1 FROM data.notice_industry_type nit
         WHERE nit.bidntceno = n.bidntceno AND nit.bidntceord = n.bidntceord
     )) AS "원데이터O_업종X",
    (SELECT COUNT(DISTINCT (bidntceno, bidntceord))
     FROM data.notice_industry_type nit
     WHERE NOT EXISTS (
         SELECT 1 FROM data.notice n
         WHERE n.bidntceno = nit.bidntceno AND n.bidntceord = nit.bidntceord
     )) AS "원데이터X_업종O"

UNION ALL

-- company 기준: 업체는 있지만 업종이 없는 경우 / 업종은 있지만 업체가 없는 경우
SELECT
    '업체-업종' AS 관계,
    (SELECT COUNT(*)
     FROM data.company c
     WHERE NOT EXISTS (
         SELECT 1 FROM data.company_industry_type cit
         WHERE cit.bizno = c.bizno
     )) AS "원데이터O_업종X",
    (SELECT COUNT(DISTINCT bizno)
     FROM data.company_industry_type cit
     WHERE NOT EXISTS (
         SELECT 1 FROM data.company c
         WHERE c.bizno = cit.bizno
     )) AS "원데이터X_업종O";
