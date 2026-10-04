# Findings: Fake Job Postings Analysis

**Dataset:** Kaggle "Real / Fake Job Posting Prediction" (EMSCAD, University of the Aegean), file `fake_job_postings.csv`.

**Reproduce every number below:**
```
python -m etl.load_postings --csv data/fake_job_postings.csv
python -m etl.run_analysis          # queries 01 to 10 (CSV copies go to analysis_output/)
python -m etl.keyword_audit         # the keyword table in section 5
```
Results are deterministic, so you should get exactly these figures. If you don't, find out why before quoting them.

---

## 1. Data  (`01_overview.sql`)
- Rows in file: **17,880**. Exact duplicate postings removed: **315**. Rows analysed: **17,565**.
- Fake postings: **856** (**4.87%**). Real: 16,709.
- Answering "real" for every posting would be **95.13%** accurate. That is why accuracy is useless here and I report precision and recall instead.
- A salary could be parsed for only 2,660 postings (15%).

## 2. Where are fake postings concentrated?  (`02`, `03`, `09`, `10`)

**By employment type** (overall rate 4.87%)

| Employment type | Postings | Fake % |
| :--- | :--- | :--- |
| Part-time | 768 | 9.51 |
| Not specified | 3,427 | 6.89 |
| Other | 225 | 6.67 |
| Full-time | 11,395 | 4.27 |
| Contract | 1,513 | 2.84 |
| Temporary | 237 | 0.84 |

**By industry** (groups with at least 30 postings, top 4)

| Industry | Postings | Fake | Fake % |
| :--- | :--- | :--- | :--- |
| Oil & Energy | 286 | 108 | 37.76 |
| Accounting | 159 | 57 | 35.85 |
| Computer Networking | 43 | 12 | 27.91 |
| Leisure, Travel & Tourism | 72 | 20 | 27.78 |

Oil & Energy and Accounting hold 165 of the 856 fakes (19%) while being under 3% of all postings.

**By description length:** 5.48% (under 300 characters), 6.00% (300 to 999), 3.47% (1,000 to 2,499), 5.90% (2,500 or more). There is **no clear pattern**, so length is not a useful signal.

**Repetition** (`10`): 856 fake postings have 521 distinct description openings (61%); 16,709 real postings have 10,878 (65%). Fakes are only slightly more repetitive overall. Inside Oil & Energy specifically, the 108 fakes share only 41 distinct openings, so some of that industry's rate comes from reposted templates.

Takeaway: fake rates vary a lot by industry and somewhat by employment type. That says where fakes appear in this dataset, not how to recognise one.

## 3. Which posting details separate fake from real?  (`04`)

| Feature | % fake when absent (0) | % fake when present (1) |
| :--- | :--- | :--- |
| has_company_logo | **15.87** | 2.02 |
| has_company_profile | **17.70** | 1.93 |
| has_questions | 6.81 | 2.88 |
| telecommuting | 4.71 | 8.50 |
| has_salary | 4.29 | 8.12 |

- Without a company profile, a posting is fake 17.7% of the time versus 1.9% with one: about 9 times as often. A missing logo gives about 8 times.
- `has_salary` goes the **opposite way** to intuition: postings that state a salary are fake *more* often (8.1% vs 4.3%). Penalising a missing salary would make a detector worse.
- These are associations, not causes. A missing logo does not make a posting fake.

## 4. How good is the rule engine?  (`05`, `07`, `08`)

At my original flag threshold of **25** (the MODERATE boundary):

| True positives | False positives | False negatives | True negatives | Precision | Recall |
| :--- | :--- | :--- | :--- | :--- | :--- |
| 1 | 96 | 855 | 16,613 | **1.03%** | **0.12%** |

**As first built, the rule engine is nearly useless on this data.** It flags 97 of 17,565 postings and catches 1 of 856 fakes.

| Threshold | Postings flagged | True positives | Precision | Recall |
| :--- | :--- | :--- | :--- | :--- |
| 10 | 4,258 | 588 | 13.81% | 68.69% |
| 25 | 97 | 1 | 1.03% | 0.12% |
| 50 | 13 | 0 | 0.00% | 0.00% |
| 75 | 1 | 0 | 0.00% | 0.00% |

- At threshold 10 the engine catches 69% of fakes but flags 24% of all postings, and 86% of what it flags is honest. Its precision of 13.8% is about 2.8 times better than picking at random (4.87%).
- **Query 08: text rules only and text + structure rules give identical results at threshold 25.** This is a design flaw of mine. The three structure rules add at most 10 + 5 + 5 = 20 points, so they can never reach 25 on their own.

## 5. Which rules work and which are noisy?  (`06`, `etl.keyword_audit`)

| Rule | Postings flagged | Fake | Precision | Coverage of all fakes | Lift |
| :--- | :--- | :--- | :--- | :--- | :--- |
| NO_COMPANY_PROFILE | 3,277 | 580 | 17.70% | 67.76% | 3.63 |
| NO_COMPANY_LOGO | 3,618 | 574 | 15.87% | 67.06% | 3.26 |
| NO_SCREENING_QUESTIONS | 8,913 | 607 | 6.81% | 70.91% | 1.40 |
| PAYMENT_REQUEST | 96 | **0** | 0.00% | 0.00% | 0.00 |
| URGENT_LANGUAGE | 2 | 0 | 0.00% | 0.00% | 0.00 |
| REGISTRATION_FEE | 2 | 1 | 50.00% | 0.12% | 10.27 |
| SECURITY_DEPOSIT | 1 | 1 | 100.00% | 0.12% | 20.53 |

REGISTRATION_FEE and SECURITY_DEPOSIT fired on 2 and 1 postings, far too few for their precision to mean anything.

**Why the payment rule fails on postings** (`keyword_audit`): all 96 flagged postings were honest. The keywords behind the hits were "wire transfer" (39 postings, descriptions of payment companies), "bitcoin" (25, crypto and fintech employers), "crypto" (18, it also matches the word *cryptography*), "send money" (17, money-transfer companies), "gift card" (5, for example a gift card offered as an interview incentive) and "processing fee" (1, matched inside "processing feedback"). Separately, one posting containing "registration fee" actually says "no registration fee", and the rules cannot read negation.

Takeaway: the email keywords were written for emails that demand money from the reader. Job-posting scammers rarely write that, and honest finance and crypto employers use these words constantly. The signal is in the structure fields.

## 6. Re-weighting (not done yet)
I have deliberately **not** changed any weights after seeing these results. If I do, I tune on 70% of the postings (`MOD(source_job_id, 10) < 7`) and report precision and recall from the untouched 30% (`MOD(source_job_id, 10) >= 7`). Otherwise the improvement is overstated. See `docs/analytics-guide.md`, section 7.

## 7. Recommendations
1. **Do not reuse the email payment keywords on postings as they are.** They fired on 96 honest postings and no fake ones. If kept: match whole words, ignore negations ("no registration fee"), and apply them only where a fee is demanded from the applicant.
2. **Build the posting score around the structure fields** (company profile, logo, screening questions), which each cover 67 to 71% of fakes, and choose the flag threshold from the precision/recall table, checked on held-out data.
3. **Make the score scale consistent.** Structure rules currently cannot reach the threshold of 25.
4. **Do not penalise a missing salary.** In this data it points the wrong way.
5. **Give Oil & Energy and Accounting postings extra scrutiny**, but treat it as a dataset-specific hint (see limitations).

## 8. Limitations
- One dataset, collected years ago, English only. Scam tactics change.
- Labels come from the dataset authors and may contain errors.
- Even the best signals are weak: at 68.7% recall, 86% of flagged postings are honest. A real system would need a trained classifier.
- The structure fields describe how this dataset was collected as much as how scams behave, so they may not carry over to postings from another site.
- The Oil & Energy rate is partly driven by reposted templates (section 2), so it overstates how many independent cases there are.
- Weights and the threshold of 25 were my own choices, made before I saw the data.
