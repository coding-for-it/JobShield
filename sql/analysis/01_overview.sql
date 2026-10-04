-- QUESTION: How big is the dataset, and how rare are fake postings?
-- TECHNIQUE: aggregate functions. AVG of a 0/1 column = the share of 1s.
-- WHY IT MATTERS: if only a few postings are fake, a model that always says "real" still
-- looks very accurate. That is why we later use precision and recall, not accuracy.
SELECT dataset_name,
       COUNT(*) AS total_postings,
       SUM(fraudulent) AS fraud_postings,
       ROUND(100 * AVG(fraudulent), 2) AS fraud_pct,
       ROUND(100 - 100 * AVG(fraudulent), 2) AS accuracy_if_always_real_pct
FROM job_postings
GROUP BY dataset_name;
