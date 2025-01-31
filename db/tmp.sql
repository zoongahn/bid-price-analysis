SELECT "사업자 등록번호", "업체명", "순위"
FROM companies,
     bids
WHERE 순위 = 1;