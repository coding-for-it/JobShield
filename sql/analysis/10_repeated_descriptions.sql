-- QUESTION: Are fake postings more repetitive than real ones (the same text posted again and again)?
-- TECHNIQUE: COUNT(DISTINCT LEFT(text, 80)) counts how many different openings there are.
-- WHY IT MATTERS: if many fakes are one template reposted, a rule or industry that looks strong
-- may really be a few campaigns, and "N postings" overstates how much independent evidence we have.
SELECT CASE WHEN fraudulent = 1 THEN 'fake' ELSE 'real' END AS label,
       COUNT(*) AS postings,
       COUNT(DISTINCT LEFT(description, 80)) AS distinct_description_openings,
       ROUND(100 * COUNT(DISTINCT LEFT(description, 80)) / COUNT(*), 1) AS distinct_pct
FROM job_postings
GROUP BY fraudulent
ORDER BY fraudulent;
