SELECT i.industry_code AS 업종코드, i.industry_name AS 업종명, i.classification_name AS 분류명, COALESCE(c.company_count, 0) AS 업체수, COALESCE(n.notice_count, 0) AS 공고수
FROM meta.industry_type_info i
    LEFT JOIN (
        SELECT indstrytycd, COUNT(DISTINCT bizno) AS company_count
        FROM data.company_industry_type
        GROUP BY
            indstrytycd
    ) c ON i.industry_code = c.indstrytycd
    LEFT JOIN (
        SELECT lcnslmtnm_code, COUNT(
                DISTINCT bidntceno || bidntceord
            ) AS notice_count
        FROM data.notice_industry_type
        GROUP BY
            lcnslmtnm_code
    ) n ON i.industry_code = n.lcnslmtnm_code
ORDER BY i.industry_code;