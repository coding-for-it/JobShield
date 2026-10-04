-- QUESTION: Which industries have the highest fraud rate?
-- TECHNIQUE: subquery + HAVING (ignore tiny groups, their rates are noise)
--            + window function RANK() to number the industries.
-- HAVING filters groups AFTER grouping. WHERE filters rows BEFORE grouping.
SELECT industry, postings, fraud_postings, fraud_pct,
       RANK() OVER (ORDER BY fraud_pct DESC) AS fraud_rank
FROM (
    SELECT COALESCE(industry, 'Not specified') AS industry,
           COUNT(*) AS postings,
           SUM(fraudulent) AS fraud_postings,
           ROUND(100 * AVG(fraudulent), 2) AS fraud_pct
    FROM job_postings
    GROUP BY COALESCE(industry, 'Not specified')
    HAVING COUNT(*) >= 30
) AS by_industry
ORDER BY fraud_rank, postings DESC
LIMIT 15;
