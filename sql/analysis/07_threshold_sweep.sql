-- QUESTION: How do precision and recall trade off as the "flag" threshold moves?
-- TECHNIQUE: a small list of thresholds built with UNION ALL, CROSS JOINed to the postings.
-- A LOW threshold flags more (catches more scams, but more false alarms).
-- A HIGH threshold flags less (fewer false alarms, but misses more scams).
WITH thresholds AS (
    SELECT 10 AS threshold UNION ALL SELECT 25 UNION ALL SELECT 50 UNION ALL SELECT 75
)
SELECT t.threshold,
       SUM(p.risk_score >= t.threshold) AS flagged,
       SUM(p.risk_score >= t.threshold AND p.fraudulent = 1) AS true_positives,
       ROUND(100 * SUM(p.risk_score >= t.threshold AND p.fraudulent = 1)
             / NULLIF(SUM(p.risk_score >= t.threshold), 0), 2) AS precision_pct,
       ROUND(100 * SUM(p.risk_score >= t.threshold AND p.fraudulent = 1)
             / NULLIF(SUM(p.fraudulent = 1), 0), 2) AS recall_pct
FROM thresholds t
CROSS JOIN job_postings p
GROUP BY t.threshold
ORDER BY t.threshold;
