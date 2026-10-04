# JobShield Part B: Data Analysis Interview Guide

Read this together with `backend-interview-guide.md` (Part A, the app). This file covers the data analysis half.

**Numbers:** the figures in this guide come from the real Kaggle file and are the same ones in `docs/findings.md`. Re-run the pipeline yourself and check you get the same values before you say them out loud. Never quote numbers from the synthetic sample file; they are invented.

---

## 1. The pitch (analyst version)

### 30 seconds
"I built a job-scam detector with Python, MySQL, a FastAPI service and Streamlit, and then I tested it honestly. I loaded 17,565 labelled job postings from a Kaggle dataset into MySQL with a pandas pipeline and measured my own rules using SQL. The result was humbling: my rule engine, built from email-scam patterns, caught only 1 of 856 fake postings at its normal threshold. The analysis showed why. The keyword rules fired almost only on honest postings, while a missing company profile or logo, which I had weighted lightly, covered about two thirds of the fakes."

### 2 minutes
Say the 30-second version, then add:

"Only 4.9% of postings were fake, so always answering 'real' would be 95% accurate. That is why I used precision and recall. Lowering the flag threshold to 10 raised recall to 69%, but precision was only 14%. The payment rule fired on 96 postings and none were fake: 'crypto' matched 'cryptography', 'wire transfer' and 'send money' appear in payment-company descriptions, and one posting actually said 'no registration fee'. I also found a flaw of mine: the structure rules can add at most 20 points, so they could never reach the threshold of 25. I did not re-tune afterwards on the same data; I would tune on a 70% split and report on the other 30%. The limits are one older English dataset, keyword rules that are easy to evade, and weights I chose by hand."

**Why this story works:** it shows you measure your own work, report a negative result honestly, and explain the cause. That is what analysts are hired to do.

---

## 2. The pipeline in six steps

1. **Extract**: `pd.read_csv` loads the Kaggle file (`etl/load_postings.py`).
2. **Clean** (`etl/clean.py`): trim text, blanks to NULL, split `location` into country/state/city, parse `salary_range`, convert yes/no columns to 0/1, remove duplicates.
3. **Score**: each posting goes through the rule engine (`PostingAnalyzer`), giving a risk score and the list of rules that fired.
4. **Load**: postings go into `job_postings`, fired rules into `posting_signals`, in batches, in one transaction (all or nothing).
5. **Analyse**: ten SQL queries in `sql/analysis/` answer specific questions.
6. **Serve and show**: `/api/v1/analytics/...` endpoints run aggregate queries, and the Streamlit Analytics page draws charts.

Run it: `python -m etl.load_postings --csv data/fake_job_postings.csv`, then `python -m etl.run_analysis`. For the keyword evidence, `python -m etl.keyword_audit`.

### The two new tables
- `job_postings`: one row per posting, the true label `fraudulent`, the cleaned columns, and our `risk_score`.
- `posting_signals`: one row per rule that fired on a posting (`posting_id` foreign key, `ON DELETE CASCADE`). This table lets SQL measure each rule separately.

---

## 3. The metrics in easy language

Every posting is either really fake or really real, and our engine either flags it or doesn't. That gives four outcomes (the **confusion matrix**):

| | Really fake | Really real |
| :--- | :--- | :--- |
| **Flagged** | True positive (caught a scam) | False positive (false alarm) |
| **Not flagged** | False negative (missed a scam) | True negative (correctly left alone) |

- **Precision** = TP / (TP + FP). "When I raise an alarm, how often am I right?"
- **Recall** = TP / (TP + FN). "Of all the scams out there, how many do I catch?"
- **Accuracy** = (TP + TN) / everything. Misleading when fakes are rare.
- **Lift** = a rule's precision / the overall fake rate. Above 1 means better than guessing; 4 means four times better.
- **Coverage** = of all fake postings, the share that a rule fired on.

### Why accuracy misleads (made-up numbers, for explanation only)
1,000 postings, 50 fake. Say we flag 40, of which 30 are fake: TP 30, FP 10, FN 20, TN 940.
- Accuracy = 970/1000 = **97%** (sounds great)
- But answering "real" every time gives 950/1000 = **95%**. So 97% is barely better than doing nothing.
- Precision = 30/40 = **75%**, Recall = 30/50 = **60%**. These tell the real story.

### The threshold trade-off
The engine flags a posting when its score is at least the threshold (default 25).
- Lower threshold: catches more scams (higher recall), more false alarms (lower precision).
- Higher threshold: fewer false alarms, more missed scams.
There is no "correct" threshold; it depends on which mistake costs more. Query `07` and the dashboard's last chart show this.

---

## 4. The ten queries: what each shows and how to explain it

| # | Question | Key idea to say out loud |
| :--- | :--- | :--- |
| 01 | How rare are fakes? | `AVG(fraudulent)` works because the column is 0/1, so the average is the share of fakes |
| 02 | Fraud by employment type | `GROUP BY`; `COALESCE` turns NULL into "Not specified" so missing data stays visible |
| 03 | Industries ranked | `HAVING COUNT(*) >= 30` drops tiny groups; `RANK() OVER (ORDER BY fraud_pct DESC)` numbers the rest |
| 04 | Feature comparison | `UNION ALL` stacks one small query per feature; compare fraud % when the feature is 0 vs 1 |
| 05 | Confusion matrix | A CTE computes `flagged`; `SUM(flagged = 1 AND fraudulent = 1)` counts matches because true is 1 |
| 06 | Rule performance | `JOIN` signals to postings; `COUNT(DISTINCT ...)` because one posting can trigger a rule twice |
| 07 | Threshold sweep | A list of thresholds `CROSS JOIN`ed to every posting, one precision/recall row per threshold |
| 08 | Baseline vs combined | `LEFT JOIN` + `CASE` rebuilds a "text rules only" score; two models compared with `UNION ALL` |
| 09 | Description length | `CASE WHEN` creates buckets; the cut-offs are my choice, so I'd test other cut-offs |
| 10 | Repeated descriptions | `COUNT(DISTINCT LEFT(description, 80))` counts distinct openings; shows how much of a pattern is one reposted template |

---

## 5. SQL concepts in simple words

| Concept | Simple explanation |
| :--- | :--- |
| **WHERE vs HAVING** | WHERE filters rows before grouping; HAVING filters groups after. Example: `HAVING COUNT(*) >= 30` |
| **CTE** (`WITH x AS (...)`) | A named temporary result, so a long query reads top to bottom. Same result as a subquery, easier to read |
| **Window function** | Calculates across rows without collapsing them. `RANK() OVER (ORDER BY ...)` adds a rank column |
| **RANK vs DENSE_RANK vs ROW_NUMBER** | With ties 1,1,3 (RANK), 1,1,2 (DENSE_RANK), 1,2,3 (ROW_NUMBER) |
| **INNER vs LEFT JOIN** | INNER keeps only matches; LEFT keeps every row from the left table. Query 08 needs LEFT so postings with no signals still count |
| **CROSS JOIN** | Every row paired with every row. Used to test each threshold against all postings |
| **NULLIF(x, 0)** | Returns NULL instead of 0, so dividing by it gives NULL instead of an error |
| **COUNT(DISTINCT)** | Counts unique values; needed when a join repeats rows |
| **CASE WHEN** | If/else inside SQL, used for buckets and conditional counting |
| **Conditional SUM** | `SUM(a = 1 AND b = 1)` counts rows where both are true |
| **UNION ALL** | Stacks results of two queries with the same columns |

---

## 6. Cleaning decisions (and why)

| Decision | Reason |
| :--- | :--- |
| Remove duplicate postings (same content, different `job_id`) | Duplicates inflate counts and can put the same posting in both training and test data. I count how many were removed. |
| Missing category becomes "Not specified", not dropped | Leaving a field blank can itself be informative, and dropping rows would shrink the rare fake class |
| Unparseable salary (`0-0`, `Dec-20`, text) becomes NULL | Some salary values are corrupted into dates by spreadsheets; guessing would add false data |
| Refuse to run if the `fraudulent` label is missing or unrecognised | A silently wrong label would make every metric wrong |
| Ignore groups under 30 postings | Percentages from tiny groups swing wildly |
| Keep one dataset in the tables at a time | Mixing datasets would blend unrelated results |

---

## 7. Testing honestly: the held-out split

My rules are written by hand, not learned, so the usual "train vs test" leak is smaller. But **if I change weights after looking at results, I am tuning on the data I measure on**, and the improvement will look bigger than it is.

Safe method (deterministic, no random seed needed):
```sql
-- 70% for tuning:      WHERE MOD(source_job_id, 10) < 7
-- 30% held back to check:  WHERE MOD(source_job_id, 10) >= 7
```
Add that `WHERE` to query 05 (or 08). Change weights using the 70% only, then report the final precision and recall from the untouched 30%. Say this in the interview: it shows you understand overfitting.

---

## 8. The analytics API and dashboard

| Endpoint | Returns |
| :--- | :--- |
| `GET /analytics/summary?threshold=25` | totals, fake rate, confusion matrix, precision, recall, accuracy |
| `GET /analytics/fraud-by/{dimension}` | ranked fraud rate by employment_type, industry, experience, education, job_function or country |
| `GET /analytics/features` | fraud % when a yes/no feature is absent vs present |
| `GET /analytics/rule-performance` | precision, coverage, lift of each rule |
| `GET /analytics/threshold-sweep` | precision and recall at several thresholds |

- All need a login token.
- `dimension` is an Enum, so only six column names are accepted. A column name cannot be passed as a SQL `%s` parameter, so the SQL text uses a fixed whitelist; anything else returns 422. Numbers (threshold, minimum group size) go through `%s` placeholders as usual.
- The dashboard shows a warning banner whenever the loaded dataset's name contains "synthetic".

---

## 9. Cross-questions and answers

### Data and metrics
**Q1. Walk me through your pipeline.**
Section 2. Say the six steps, then mention it is repeatable: one command reloads everything, and the load is one transaction.

**Q2. What is class imbalance and how did you handle it?**
Fake postings are rare, so a model can look accurate by always saying "real." I did not rebalance the data (my rules aren't trained); instead I evaluate with precision and recall and show the always-real accuracy next to it.

**Q3. Which matters more here, precision or recall?**
It depends on cost. Missing a scam (low recall) harms a job seeker; false alarms (low precision) make people distrust the tool and hurt honest employers. For a warning tool I'd lean toward recall but keep precision high enough to avoid alert fatigue, and let the user see the evidence. The threshold chart shows the trade-off.

**Q4. How did you choose the threshold of 25?**
It is the boundary of my MODERATE level, set before I analysed the data. The sweep shows it was a poor choice for postings: threshold 10 gives recall 69% and precision 14%, while 25 gives almost nothing. I would choose the new threshold by the cost of each mistake, on held-out data, not to make a number look good.

**Q5. Did you tune the weights on the same data you tested on?**
The initial weights were my guesses, written before seeing the data, and so far I have not re-tuned them (`docs/findings.md`, section 6). If I do, I tune on 70% and report results from the held-out 30% (section 7).

**Q6. Could there be data leakage?**
Rules are not learned, so classic leakage is limited. But features like "has company logo" partly reflect how the dataset was collected, so they may not behave the same on new postings. I'd test on a fresh sample.

**Q7. Does a missing logo cause fraud?**
No. It is an association. Scammers tend to skip effort, but a small legitimate business may also have no logo.

**Q8. Is your dataset representative?**
No. It is one source, older, English only, and with few fake postings. Findings may not generalise.

**Q9. Why ignore groups with fewer than 30 postings?**
With few postings, one fake changes the percentage a lot (1 of 3 is 33%). Small groups produce misleading rankings.

**Q10. What is lift?**
How many times better a rule is than picking postings at random. If 5% of all postings are fake and a rule's flagged postings are 40% fake, lift is 8.

**Q11. Which rule was best and which was worst?**
By coverage and lift, `NO_COMPANY_PROFILE`: it fired on 3,277 postings, 17.7% were fake (lift 3.6) and it covers 68% of all fakes. Noisiest: `PAYMENT_REQUEST`, 96 postings flagged and 0 fake. `REGISTRATION_FEE` and `SECURITY_DEPOSIT` fired on only 2 and 1 postings, too few to judge.

**Q12. What would you do next?**
Train a simple model (for example logistic regression on the structure features plus word counts from the description), compare it to the rules on the same held-out data, and keep whichever is better and explainable. I have not built this.

### What the real data showed
**Q-R1. Your recall is 0.12%. Isn't the detector useless?**
At its original threshold of 25, yes, and I report that plainly: 1 true positive, 96 false positives, 855 missed. Two causes: the email-derived keyword rules almost never fire on job postings, and my three structure rules add at most 20 points so they cannot reach 25. The threshold sweep shows the engine is not useless at threshold 10 (recall 69%, precision 14%), but that is still weak, and I chose not to quietly change the numbers after seeing the results.

**Q-R2. Why did adding the structure rules not change query 08?**
Because they can add at most 20 points and the flag threshold is 25, they only change the outcome for postings that already had a text-rule hit. It is a design flaw I found by measuring, and the fix is to make the scale consistent and re-evaluate on held-out data.

**Q-R3. What did you learn about keyword rules?**
They need context. All 96 `PAYMENT_REQUEST` hits were honest: "wire transfer" (39) and "send money" (17) appear in payment-company descriptions, "bitcoin" (25) in crypto employers, "crypto" (18) matched the word cryptography, and "processing fee" matched inside "processing feedback". One posting said "no registration fee" and still triggered the rule, because the rules cannot read negation. Fixes: whole-word matching, negation handling, and applying fee rules only to text about the applicant paying.

**Q-R4. What surprised you?**
Postings that state a salary are fake more often (8.1% vs 4.3%), the opposite of what I expected, so penalising a missing salary would have made the detector worse. Also, description length showed no clear pattern.

**Q-R5. Which single detail best separates fake from real?**
A missing company profile: 17.7% of such postings are fake versus 1.9% of those with a profile (about 9 times), and it covers 68% of all fakes. A missing logo is almost as strong. Caveat: this is an association in one dataset, not a cause.

**Q-R6. What would you do about Oil & Energy at 37.8% fake?**
Treat it as a hint, not a rule. Query 10 shows the 108 fake Oil & Energy postings have only 41 distinct description openings, so part of the rate comes from reposted templates, which means fewer independent cases than the count suggests.

**Q-R7. If you improved the weights, how would you prove it?**
Tune on 70% of postings (`MOD(source_job_id, 10) < 7`) and report precision and recall on the other 30%. Without a held-out set, any improvement is partly overfitting.

### SQL
**Q13. WHERE vs HAVING?** Section 5.

**Q14. Why COUNT(DISTINCT) in the rule-performance query?**
One posting can trigger the same rule several times (for example two fee words), so plain COUNT would count that posting twice and distort precision.

**Q15. Why LEFT JOIN in the baseline query?**
Postings with no signals have no rows in `posting_signals`. An INNER JOIN would drop them and shrink the denominator.

**Q16. How does `SUM(flagged = 1 AND fraudulent = 1)` work?**
The condition is 1 when true and 0 when false, so adding them counts the rows where it is true.

**Q17. Why NULLIF in precision?**
If nothing is flagged, precision is 0 divided by 0. NULLIF returns NULL so the result is "undefined" instead of a crash or a misleading 0.

**Q18. RANK vs ROW_NUMBER?** Section 5.

**Q19. How would you find the top 3 industries per country?**
`ROW_NUMBER() OVER (PARTITION BY country ORDER BY fraud_pct DESC)` in a subquery, then `WHERE rn <= 3`.

**Q20. How would you speed up these queries on millions of rows?**
Indexes on the grouped and filtered columns (I added them on fraudulent, employment_type, industry, country, risk_score), summary tables, and avoiding functions on indexed columns. For text search, FULLTEXT indexes.

### Python and engineering
**Q21. Why pandas for cleaning but SQL for analysis?**
Pandas is convenient for messy text and parsing before loading. SQL is better for grouping and joining once the data is tidy and in a database, and the queries are reusable by the API.

**Q22. How do you load thousands of rows efficiently?**
`executemany` in batches of 1,000 inside one transaction, instead of one INSERT and commit per row.

**Q23. Is the loader safe to run twice?**
Yes. By default it empties the two tables first, so the result is the same. If a step fails, the transaction is rolled back.

**Q24. How do you test the analytics code?**
A hand-built dataset of 20 postings with known answers (4 caught, 2 missed, 1 false alarm, 13 correct). The tests assert exact precision (80%) and recall (66.67%), per-rule numbers, and edge cases such as no flagged postings (precision is null).

**Q25. Why reuse the email rules for job postings?**
Same scam patterns appear in both (fees, urgency, "no interview"). Reusing the keyword lists keeps one source of truth, and the dataset lets me measure those rules for the first time.

**Q26. Why a separate `analytics_schema.sql`?**
So re-running `schema.sql` (which drops the app tables) never deletes a loaded dataset.

---

## 10. Weak spots (admit them first)

1. **Rules are keyword matches.** In the real data all 96 payment-rule hits were honest postings, and the rules cannot handle negation ("no registration fee"). Scammers can also reword.
1a. **A design flaw I found by measuring:** structure rules add at most 20 points, below the flag threshold of 25.
2. **Weights are guesses**, not learned. The held-out check protects the evaluation, not the weights.
3. **No model comparison.** I measured rules only; I did not train a classifier to compare.
4. **One dataset**, older, English only, few fakes; labels may contain errors.
5. **Structure rules reflect dataset collection** as much as real scam behaviour.
6. **Analytics queries are duplicated** between `sql/analysis/*.sql` and `analytics_service.py`. If you edit one, update the other.
7. **No time dimension.** The dataset has no posting date, so I cannot analyse trends.

---

## 11. Don't say / do say

| Don't say | Say instead |
| :--- | :--- |
| "My model is 95% accurate" | "Precision is `[ ]`% and recall `[ ]`%; accuracy is misleading because fakes are rare" |
| "I built a machine-learning model" | "I built and evaluated a rule-based detector" |
| "Missing logos cause fraud" | "Missing logos are associated with fraud in this dataset" |
| "It detects fake jobs" | "It flags suspicious patterns, with measured precision and recall" |
| Any number you did not measure | Only numbers from your own run |
| Numbers from the synthetic sample | Say the sample is only for testing the pipeline |

---

## 12. Two-minute demo script

1. **(20 s)** "Part A scores a single email. Part B asks how well those rules work on real labelled data."
2. **(20 s)** Terminal: `python -m etl.load_postings --csv data/fake_job_postings.csv`. Point at the printed counts: rows read, duplicates removed, fakes, signals stored.
3. **(30 s)** `python -m etl.run_analysis` or open one SQL file (06 or 03) and explain the technique in one sentence.
4. **(40 s)** Analytics page: overview metrics, drag the threshold slider and watch precision and recall move, then show the rule-performance table.
5. **(10 s)** "Limitations: one older dataset, keyword rules, hand-chosen weights."

---

## 13. Your numbers (from the real Kaggle file; re-run to confirm before using)

| Fact | Value |
| :--- | :--- |
| Rows in file / duplicates removed / analysed | 17,880 / 315 / 17,565 |
| Fake postings / share | 856 / 4.87% |
| Always-real accuracy | 95.13% |
| Precision / recall at threshold 25 | 1.03% / 0.12% (TP 1, FP 96, FN 855, TN 16,613) |
| Precision / recall at threshold 10 | 13.81% / 68.69% (4,258 flagged) |
| Best rule (coverage, lift) | NO_COMPANY_PROFILE: 67.76% coverage, precision 17.70%, lift 3.63 |
| Noisiest rule | PAYMENT_REQUEST: 96 flagged, 0 fake |
| Text-only vs combined at 25 | identical (structure rules max out at 20) |
| Strongest feature | no company profile: 17.7% fake vs 1.9% with one |
| Surprising feature | has_salary: 8.1% fake vs 4.3% without |
| Highest-fraud industries (30+ postings) | Oil & Energy 37.8%, Accounting 35.9% |
| Distinct description openings | fake 61%, real 65% |
