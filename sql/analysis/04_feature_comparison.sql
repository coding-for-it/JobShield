-- QUESTION: Are postings that lack a logo / screening questions / company profile more often fake?
-- TECHNIQUE: UNION ALL stacks one small GROUP BY per feature into a single result.
-- READ IT AS: "among postings where the feature is 0 (absent) or 1 (present), what % are fake?"
SELECT 'has_company_logo' AS feature, has_company_logo AS feature_value, COUNT(*) AS postings,
       SUM(fraudulent) AS fraud_postings, ROUND(100 * AVG(fraudulent), 2) AS fraud_pct
FROM job_postings GROUP BY has_company_logo
UNION ALL
SELECT 'has_questions', has_questions, COUNT(*), SUM(fraudulent), ROUND(100 * AVG(fraudulent), 2)
FROM job_postings GROUP BY has_questions
UNION ALL
SELECT 'has_company_profile', has_company_profile, COUNT(*), SUM(fraudulent), ROUND(100 * AVG(fraudulent), 2)
FROM job_postings GROUP BY has_company_profile
UNION ALL
SELECT 'has_salary', has_salary, COUNT(*), SUM(fraudulent), ROUND(100 * AVG(fraudulent), 2)
FROM job_postings GROUP BY has_salary
UNION ALL
SELECT 'telecommuting', telecommuting, COUNT(*), SUM(fraudulent), ROUND(100 * AVG(fraudulent), 2)
FROM job_postings GROUP BY telecommuting
ORDER BY feature, feature_value;
