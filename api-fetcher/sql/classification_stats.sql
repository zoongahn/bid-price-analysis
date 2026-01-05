-- 분류코드별 업종수, 업체수, 공고수 집계
SELECT
    i.classification_code AS 분류코드,
    i.classification_name AS 분류명,
    COUNT(DISTINCT i.industry_code) AS 업종수,
    COALESCE(SUM(c.company_count), 0) AS 업체수,
    COALESCE(SUM(n.notice_count), 0) AS 공고수
FROM meta.industry_type_info i
LEFT JOIN (
    SELECT indstrytycd, COUNT(DISTINCT bizno) AS company_count
    FROM data.company_industry_type
    GROUP BY indstrytycd
) c ON i.industry_code = c.indstrytycd
LEFT JOIN (
    SELECT lcnslmtnm_code, COUNT(DISTINCT bidntceno || bidntceord) AS notice_count
    FROM data.notice_industry_type
    GROUP BY lcnslmtnm_code
) n ON i.industry_code = n.lcnslmtnm_code
GROUP BY i.classification_code, i.classification_name
ORDER BY i.classification_code;
