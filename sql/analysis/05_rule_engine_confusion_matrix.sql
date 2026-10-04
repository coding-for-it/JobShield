-- QUESTION: How well does the rule engine do when "risk score >= 25" means "flagged as suspicious"?
-- TECHNIQUE: CTE (WITH ...) + conditional counting. A comparison like (a AND b) is 1 or 0,
-- so SUM() of it counts the rows where it is true.
--   true_positives  = flagged AND really fake        false_positives = flagged but really real
--   false_negatives = missed scams                   true_negatives  = correctly left alone
--   precision = of the postings I flagged, how many were really fake?
--   recall    = of all the fake postings, how many did I catch?
WITH scored AS (
    SELECT fraudulent, (risk_score >= 25) AS flagged
    FROM job_postings
)
SELECT SUM(flagged = 1 AND fraudulent = 1) AS true_positives,
       SUM(flagged = 1 AND fraudulent = 0) AS false_positives,
       SUM(flagged = 0 AND fraudulent = 1) AS false_negatives,
       SUM(flagged = 0 AND fraudulent = 0) AS true_negatives,
       ROUND(100 * SUM(flagged = 1 AND fraudulent = 1) / NULLIF(SUM(flagged = 1), 0), 2) AS precision_pct,
       ROUND(100 * SUM(flagged = 1 AND fraudulent = 1) / NULLIF(SUM(fraudulent = 1), 0), 2) AS recall_pct
FROM scored;
