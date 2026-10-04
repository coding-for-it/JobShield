-- QUESTION: Does the fraud rate differ by employment type (full-time, part-time, ...)?
-- TECHNIQUE: GROUP BY + COALESCE (missing values become their own group, because
-- "left it blank" can itself be a useful signal).
SELECT COALESCE(employment_type, 'Not specified') AS employment_type,
       COUNT(*) AS postings,
       SUM(fraudulent) AS fraud_postings,
       ROUND(100 * AVG(fraudulent), 2) AS fraud_pct
FROM job_postings
GROUP BY COALESCE(employment_type, 'Not specified')
ORDER BY fraud_pct DESC;
