-- QUESTION: Which individual rules are useful, and which are noisy?
-- TECHNIQUE: JOIN posting_signals to job_postings, then COUNT(DISTINCT ...) because one
-- posting can trigger the same rule more than once.
--   precision_pct = of postings where this rule fired, % that were fake
--   coverage_pct  = of ALL fake postings, % this rule fired on
--   lift          = precision divided by the overall fraud rate (above 1 = better than guessing)
WITH totals AS (
    SELECT COUNT(*) AS n, SUM(fraudulent) AS fraud_n FROM job_postings
)
SELECT s.signal_type,
       COUNT(DISTINCT s.posting_id) AS postings_flagged,
       COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END) AS fraud_flagged,
       ROUND(100 * COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END)
             / COUNT(DISTINCT s.posting_id), 2) AS precision_pct,
       ROUND(100 * COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END)
             / NULLIF(t.fraud_n, 0), 2) AS coverage_pct,
       ROUND((COUNT(DISTINCT CASE WHEN p.fraudulent = 1 THEN p.id END) / COUNT(DISTINCT s.posting_id))
             / NULLIF(t.fraud_n / t.n, 0), 2) AS lift
FROM posting_signals s
JOIN job_postings p ON p.id = s.posting_id
CROSS JOIN totals t
GROUP BY s.signal_type, t.n, t.fraud_n
ORDER BY precision_pct DESC;
