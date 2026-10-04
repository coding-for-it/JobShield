-- QUESTION: Do the posting-structure rules (no logo, no profile, no questions) improve on the
-- text-only rules that were originally written for emails?
-- TECHNIQUE: LEFT JOIN + conditional SUM to rebuild a "text rules only" score per posting,
-- then compare two models with UNION ALL. Threshold for "flagged" is 25 in both.
WITH per_posting AS (
    SELECT p.id, p.fraudulent, p.risk_score AS combined_score,
           LEAST(100, COALESCE(SUM(CASE
               WHEN s.signal_type IN ('NO_COMPANY_PROFILE', 'NO_COMPANY_LOGO', 'NO_SCREENING_QUESTIONS')
               THEN 0 ELSE s.score_impact END), 0)) AS text_only_score
    FROM job_postings p
    LEFT JOIN posting_signals s ON s.posting_id = p.id
    GROUP BY p.id, p.fraudulent, p.risk_score
)
SELECT 'text rules only' AS model,
       SUM(text_only_score >= 25 AND fraudulent = 1) AS true_positives,
       SUM(text_only_score >= 25 AND fraudulent = 0) AS false_positives,
       SUM(text_only_score < 25 AND fraudulent = 1) AS false_negatives,
       ROUND(100 * SUM(text_only_score >= 25 AND fraudulent = 1) / NULLIF(SUM(text_only_score >= 25), 0), 2) AS precision_pct,
       ROUND(100 * SUM(text_only_score >= 25 AND fraudulent = 1) / NULLIF(SUM(fraudulent = 1), 0), 2) AS recall_pct
FROM per_posting
UNION ALL
SELECT 'text + structure rules',
       SUM(combined_score >= 25 AND fraudulent = 1),
       SUM(combined_score >= 25 AND fraudulent = 0),
       SUM(combined_score < 25 AND fraudulent = 1),
       ROUND(100 * SUM(combined_score >= 25 AND fraudulent = 1) / NULLIF(SUM(combined_score >= 25), 0), 2),
       ROUND(100 * SUM(combined_score >= 25 AND fraudulent = 1) / NULLIF(SUM(fraudulent = 1), 0), 2)
FROM per_posting;
