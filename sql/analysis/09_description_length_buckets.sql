-- QUESTION: Are very short descriptions more often fake?
-- TECHNIQUE: CASE WHEN turns a number into labelled buckets. The cut-offs are my own choice
-- (not magic numbers), so change them and see if the conclusion survives.
SELECT CASE
           WHEN description_length < 300 THEN '1. under 300 characters'
           WHEN description_length < 1000 THEN '2. 300 to 999'
           WHEN description_length < 2500 THEN '3. 1000 to 2499'
           ELSE '4. 2500 or more'
       END AS description_length_bucket,
       COUNT(*) AS postings,
       SUM(fraudulent) AS fraud_postings,
       ROUND(100 * AVG(fraudulent), 2) AS fraud_pct
FROM job_postings
GROUP BY description_length_bucket
ORDER BY description_length_bucket;
