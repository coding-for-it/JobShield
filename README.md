# JobShield — Job Scam Detection & Analysis 🛡️

A full-stack project in **Python, MySQL, a REST API and Streamlit** with two parts:

| Part | What it does |
| :--- | :--- |
| **A. Scam checker app** | Check a recruiter email, a job link or a company website for scam warning signs and get an explainable **risk score (0-100)** |
| **B. Job-posting analysis** | Load a labelled dataset of real and fake job postings into MySQL with a Python pipeline, analyse it with SQL, and **measure how well the rule engine from Part A actually performs** |

Part B turns the app into a data project: the rules are not just claimed to work, they are tested against labelled data (precision, recall, per-rule performance).

---

## 📌 Problem

Job seekers receive fake offers. Typical warning signs:
- Asking for a registration fee, training fee or security deposit
- Recruiter writes from `@gmail.com` but claims to represent a big company
- Recruiter email domain does not match the company website
- "Selected without interview" and artificial urgency
- Moving the chat to Telegram / WhatsApp, or using shortened links

## 💡 Approach

Simple, **fixed rules**. Each sign found is a *signal* with a score. Scores add up (max 100) to a level: `LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`. It reports evidence and never claims "100% fake".

---

## 🏗️ How it works

```
                         ┌─ Part A ─────────────────────────────────────────────┐
Streamlit UI ──HTTP──▶  FastAPI routes ──▶ Services (logic + SQL) ──▶ MySQL
 streamlit_app/          app/api/routes/    app/services/              sql/*.sql
                                                 │
                                                 └──▶ Rule engine (analyzers → signals → risk score)
                                                      app/verification/

                         ┌─ Part B ─────────────────────────────────────────────┐
 CSV ──▶ etl/clean.py ──▶ rule engine scores each posting ──▶ MySQL (job_postings, posting_signals)
                                                                     │
                       sql/analysis/*.sql  ◀─────────────────────────┤
                       Analytics API (/analytics/...) ──▶ Streamlit "Analytics" page
```

### Project structure

```
app/
  main.py, database.py       FastAPI app; MySQL connection + SQL helpers (plain PyMySQL, no ORM)
  core/                      settings (.env), bcrypt + JWT, error format
  api/routes/                auth, users, companies, jobs, recruiters, verification, reports, analytics
  schemas/                   Pydantic request/response models
  services/                  the SQL queries + logic for each feature (analytics_service.py = Part B queries)
  verification/              email/url/job/company analyzers, signal_detector, risk_engine,
                             posting_analyzer (applies the same rules to dataset postings)
etl/
  clean.py                   cleaning functions (pandas)
  load_postings.py           CSV -> clean -> score -> MySQL
  run_analysis.py            runs every query in sql/analysis/ and saves CSVs
  keyword_audit.py           which scam keywords fire on which postings (and how many are really fake)
  make_sample_data.py        creates the SYNTHETIC sample file
sql/
  schema.sql, seed.sql       Part A tables and sample data
  analytics_schema.sql       Part B tables (job_postings, posting_signals)
  analysis/                  10 documented analysis queries (CTEs, window functions, joins, CASE)
data/                        sample_job_postings_SYNTHETIC.csv (invented data, for testing only)
streamlit_app/               login + pages: Dashboard, Verify Job, Verify Email, Reports, Analytics
tests/                       57 pytest tests
docs/                        architecture, database, API cheatsheet, findings template, interview guides
```

---

## 🚀 Run it locally

### 1. Install
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/macOS: source venv/bin/activate)
pip install -r requirements.txt
cp .env.example .env           # then put your MySQL details in .env if needed
```

### 2. Create the database (MySQL must be running)
Open the MySQL prompt **from the project folder** and run the files with `source`:
```bash
mysql -u root -p
```
```sql
source sql/schema.sql
source sql/analytics_schema.sql
source sql/seed.sql
CREATE USER 'jobshield_user'@'localhost' IDENTIFIED BY 'jobshield_pass';
GRANT ALL PRIVILEGES ON *.* TO 'jobshield_user'@'localhost';
```
> `ALL ON *.*` lets the tests create their own `jobshield_test` database. For a stricter setup, grant only on `jobshield.*` and `jobshield_test.*`.
> `schema.sql` drops and recreates Part A tables. `analytics_schema.sql` only touches the two Part B tables, so re-running `schema.sql` never deletes a loaded dataset.

### 3. Start the API
```bash
python run.py
```
API: http://127.0.0.1:8000 · Swagger docs: http://127.0.0.1:8000/docs

### 4. Start the Streamlit app (new terminal)
```bash
streamlit run streamlit_app/app.py
```
UI: http://127.0.0.1:8501 — log in with **`user@example.com` / `StrongPassword123`**.

---

## 📊 Part B: run the data analysis

### Option 1: try it right now with the synthetic sample
```bash
python -m etl.load_postings          # loads data/sample_job_postings_SYNTHETIC.csv
python -m etl.run_analysis           # runs the 10 SQL queries, saves CSVs to analysis_output/
```
Then open the **Analytics** page in Streamlit.

> ⚠️ **The sample file is invented.** Its "fake" postings follow patterns I made up, so its numbers prove only that the pipeline works. The Analytics page shows a warning banner while it is loaded. **Never quote results from it.**

### Option 2: the real dataset (do this for real findings)
1. Download the **"Real / Fake Job Posting Prediction"** dataset from Kaggle (EMSCAD, University of the Aegean). Kaggle gives you a file called `archive.zip`. Cite the source in your write-up and follow Kaggle's terms. The dataset is not included in this project, so each person downloads their own copy.
2. Unzip it. Inside is one file, `fake_job_postings.csv` (about 50 MB). Put it in the project's **`data/`** folder so the path is:
```
TrustHire/data/fake_job_postings.csv
```
3. Load and analyse (run from the `TrustHire` folder, with MySQL running and the three SQL files already loaded):
```bash
python -m etl.load_postings --csv data/fake_job_postings.csv
python -m etl.run_analysis
python -m etl.keyword_audit
```
Loading takes a few seconds. It prints rows read, duplicates removed and fake postings found. Loading again replaces the previous data, so it is safe to repeat.
4. Open the **Analytics** page in Streamlit. The results are written up in `docs/findings.md`.

The loader expects the Kaggle columns (`job_id, title, location, department, salary_range, company_profile, description, requirements, benefits, telecommuting, has_company_logo, has_questions, employment_type, required_experience, required_education, industry, function, fraudulent`). Only `title`, `description` and `fraudulent` are mandatory. It prints a clear message if something is wrong, and it refuses to guess a missing label.

### Results at a glance (real Kaggle data, 17,565 postings after removing duplicates)
- Only **4.87%** of postings are fake, so "always answer real" is already 95% accurate. Precision and recall are used instead.
- My rule engine, built from email-scam patterns, **caught 1 of 856 fakes at its original threshold (recall 0.12%)**. The keyword rules fired on 96 postings and every one was honest ("wire transfer", "bitcoin", "crypto" inside *cryptography*...).
- A missing **company profile** or **logo** is the real signal: 17.7% and 15.9% of such postings are fake, against about 2% when present, and each is missing from about two thirds of all fakes.
- Full tables, recommendations and limitations: `docs/findings.md`.

### What the pipeline does
1. **Clean** (`etl/clean.py`): trim text, blanks to NULL, split `location` into country/state/city, parse `salary_range` (junk like `0-0` or `Dec-20` becomes NULL), convert yes/no columns to 0/1, remove duplicate postings.
2. **Score** each posting with the rule engine (`PostingAnalyzer`): the same fee/urgency/no-interview/link keyword rules used for emails, plus three structure rules (no company profile, no logo, no screening questions).
3. **Load** postings and the signals that fired into MySQL, in batches, in one transaction.
4. **Analyse** with SQL (`sql/analysis/`), serve the results through `/api/v1/analytics/...`, and show them on the Analytics page.

### The ten analysis queries
| File | Question | SQL techniques |
| :--- | :--- | :--- |
| `01_overview` | How rare are fake postings? | aggregates |
| `02_fraud_by_employment_type` | Does fraud rate differ by employment type? | GROUP BY, COALESCE |
| `03_fraud_by_industry_ranked` | Which industries rank highest? | subquery, HAVING, `RANK() OVER` |
| `04_feature_comparison` | Do missing logo / profile / questions predict fraud? | UNION ALL |
| `05_rule_engine_confusion_matrix` | How good is the rule engine? | CTE, conditional SUM |
| `06_rule_performance` | Which rules work, which are noisy? | JOIN, COUNT DISTINCT, lift |
| `07_threshold_sweep` | Precision vs recall as the threshold moves | CTE, CROSS JOIN |
| `08_baseline_vs_combined` | Do the structure rules help? | LEFT JOIN, conditional SUM, UNION ALL |
| `09_description_length_buckets` | Are short descriptions suspicious? | CASE WHEN |
| `10_repeated_descriptions` | Are fake postings reposted templates? | COUNT DISTINCT, LEFT |

### Reading the metrics
- **Precision**: of the postings I flagged, how many were really fake?
- **Recall**: of all fake postings, how many did I catch?
- Accuracy is misleading when fakes are rare: always answering "real" scores high. Use precision and recall.

---

## 🐳 Docker (optional)
```bash
docker compose up --build
```
Starts MySQL (all three SQL files load on first start), the API on :8000 and Streamlit on :8501. To load data into the Docker database:
```bash
docker compose exec backend python -m etl.load_postings
```

## 🧪 Tests
```bash
pytest -v
```
57 tests. They use a **separate** database called `jobshield_test` (created from the files in `sql/`), so your real data is never touched. The analytics tests use a small hand-built dataset with known answers, so exact precision and recall values are asserted.

---

## 📊 Risk scoring rules

| Signal | Severity | Score |
| :--- | :--- | :--- |
| `PAYMENT_REQUEST` (money / gift card / crypto) | CRITICAL | +30 |
| `REGISTRATION_FEE` | CRITICAL | +25 |
| `TRAINING_FEE` | CRITICAL | +20 |
| `SECURITY_DEPOSIT` | CRITICAL | +20 |
| `DOMAIN_MISMATCH` (sender vs company website) | HIGH | +15 |
| `SUSPICIOUS_URL` (Telegram/WhatsApp/shortener, bad job URL) | HIGH | +15 |
| `PERSONAL_EMAIL` (Gmail / Yahoo ...) | MEDIUM | +10 |
| `URGENT_LANGUAGE` | MEDIUM | +10 |
| `NO_INTERVIEW_SELECTION` | HIGH | +10 |
| `UNREACHABLE_WEBSITE` | HIGH | +10 |
| `NO_COMPANY_PROFILE` (dataset postings only) | MEDIUM | +10 |
| `NO_COMPANY_LOGO`, `NO_SCREENING_QUESTIONS` (dataset postings only) | LOW | +5 each |
| `VERIFIED_COMPANY_DOMAIN` (site uses HTTPS) | LOW | −10 |

**Levels:** 0–24 `LOW` · 25–49 `MODERATE` · 50–74 `HIGH` · 75–100 `VERY_HIGH`

The weights are my own first guesses, written before looking at any data. Part B measures whether they hold up.

---

## ⚠️ Limitations
1. Scores come from simple keyword rules. They are guidance, not proof of fraud.
2. Keyword matching creates false positives (for example "crypto" in an honest blockchain job).
3. The dataset is a single, older, English-language source with few fake postings, so findings may not generalise.
4. If you tune the weights on the same data you evaluate on, the results look better than they are. Hold out part of the data for the final check (see `docs/analytics-guide.md`).
5. An HTTPS website does not prove a company is genuine, and some sites block automated requests.
6. User reports start as `PENDING`; there is no admin review screen yet, and any logged-in user can edit companies and jobs (no roles).
