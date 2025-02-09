SELECT *,
       CASE
           WHEN CAST(예가대비투찰률 AS TEXT) ~ '^-?[0-9]+(\.[0-9]+)?$'
               THEN '숫자'
           ELSE '숫자 아님'
           END AS is_numeric
FROM bids;

SELECT n.공고번호,
       n.공고제목,
       c.업체명,
       b.투찰금액,
       b.순위,
       b.기초대비사정률,
       b.비고
FROM bids b
         JOIN companies c ON b.company_id = c.id
         join notices n ON b.notice_id = n.id
WHERE n.공고번호 = '20231239637-00';


select *
from bids
where 기초대비사정률 is null;