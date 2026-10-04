# JobShield Part A: App & Backend Interview Reference

> This guide covers the app and backend (Part A). For the data-analysis half (dataset, ETL, SQL analysis, precision/recall), read `analytics-guide.md`.

**How to use this:** Read sections 1 to 5 first (pitch and big picture). Skim 6 to 14 for details. Then practise section 15 (cross-questions) out loud. Section 16 lists the weak spots, so you can admit them before the interviewer finds them. Section 18 is a 2-minute demo script.

---

## 1. The pitch

### 30-second version
"JobShield helps job seekers spot fake job offers. You paste a recruiter's email or a job link, and it checks for scam signs, like asking for a registration fee, writing from a Gmail address while claiming to be a big company, or pushing you to Telegram. Each sign adds points, and the total is a risk score from 0 to 100. It's built with Python: a FastAPI backend, MySQL for storage, and a Streamlit front end."

### 2-minute version
Say the 30-second version, then add:

"The Streamlit app never touches the database. It only calls my REST API. The API checks the user's login token, validates the input, runs the checks, and saves the result in MySQL. The checks are plain rules, not machine learning, so every score can be explained: the user sees each signal that fired and the evidence for it. I write SQL directly using PyMySQL, with parameterized queries to prevent SQL injection, and I save a result together with its signals in one transaction. Passwords are hashed with bcrypt and login uses JWT tokens. There are 57 automated tests that run against a separate test database."

---

## 2. Problem and solution

**Problem:** Students and job seekers receive fake offers. Common warning signs:
- Asking for a registration fee, training fee, or security deposit
- Recruiter writes from `@gmail.com` but claims to represent a big company
- Recruiter's email domain does not match the company website
- "Selected without interview" and fake urgency ("offer expires in 24 hours")
- Moving the chat to Telegram/WhatsApp, or using shortened links

**Solution:** The app looks for these signs using fixed rules. Each sign found is called a **signal** and carries a score. Scores are added (maximum 100) and mapped to a level: LOW, MODERATE, HIGH, VERY_HIGH.

**Important design choice:** It never says "this is 100% fake" or "100% genuine." It reports evidence and a risk level, because rules can be wrong and a false accusation has consequences.

---

## 3. Tech stack: what each piece is and why

| Tool | What it is (simple) | Why I used it |
| :--- | :--- | :--- |
| **Python** | The language | Readable, great libraries |
| **FastAPI** | Framework to build the API | Fast, validates input automatically, creates the `/docs` test page for free |
| **Uvicorn** | The server program that runs FastAPI | FastAPI needs an ASGI server; this is the standard one |
| **MySQL** | The database | Relational data, foreign keys, transactions (data stays consistent) |
| **PyMySQL** | Python library that talks to MySQL | Lets me run plain SQL; pure Python so no extra install |
| **Pydantic** | Data validation | Checks every request body (email format, lengths) and shapes every response |
| **bcrypt** | Password hashing | Slow on purpose, adds a random salt, so passwords are hard to crack |
| **PyJWT** | Creates and checks login tokens | Stateless login: the server doesn't need to remember sessions |
| **httpx** | Makes web requests | Supports async, used to fetch job pages and company websites |
| **BeautifulSoup** | Reads HTML | Pulls the title and text out of a job page |
| **Streamlit** | Builds the web UI in Python | Fast to build forms and dashboards without HTML/JS |
| **pandas** | Table-shaped data in Python | Cleans the messy CSV before it is loaded into MySQL (Part B) |
| **pytest** | Test runner | Standard for Python |
| **Docker Compose** | Runs MySQL + API + UI together | One command to start everything |

---

## 4. The big picture: three programs

```
Browser ──▶ Streamlit (port 8501) ──HTTP──▶ FastAPI (port 8000) ──SQL──▶ MySQL (port 3306)
```

- **Streamlit** shows forms and results. It holds the login token and calls the API.
- **FastAPI** is the brain. It checks login, validates input, runs the logic, talks to MySQL.
- **MySQL** stores users, companies, results, signals, reports.

**Why separate the UI and the API?**
- The same API could serve a mobile app or another website later.
- The database password lives only in the backend, never in the UI.
- Validation and security happen in one place.

### The layers inside the API

```
Route  ──▶  Service  ──▶  database.py  ──▶  MySQL
(HTTP)     (logic + SQL)   (helpers)
              │
              └──▶ Verification engine (analyzers → signals → risk score)
```

| Layer | Folder | Job |
| :--- | :--- | :--- |
| Routes | `app/api/routes/` | Receive the HTTP request, pick the right service, return the response. No business logic. |
| Schemas | `app/schemas/` | Pydantic classes that define what the API accepts and returns |
| Services | `app/services/` | The actual logic and the SQL queries |
| Database helper | `app/database.py` | Opens the connection and provides `fetch_one`, `fetch_all`, `execute` |
| Verification engine | `app/verification/` | Finds scam signals and calculates the score |

**Why layers?** Each file has one job, so code is easy to read, reuse, and test. For example, `JobService` reuses `CompanyService.get_company` to check that a company exists.

---

## 5. What happens when you click "Run Email Analysis"

1. **Streamlit** (`pages/3_Verify_Email.py`) collects the form and calls `APIClient.verify_email(token, payload)`, which sends `POST /api/v1/verification/email` with the header `Authorization: Bearer <token>`.
2. **FastAPI route** (`routes/verification.py`) runs `get_current_user` first: it decodes the token, loads the user from MySQL, and checks the account is active. If anything is wrong, it returns 401/403.
3. **Pydantic** (`EmailVerificationRequest`) validates the body: the sender must be a valid email, and required fields must be present. If not, 422.
4. **Service** (`VerificationService.verify_email`) looks for the company in MySQL by domain, then by name.
5. **`EmailAnalyzer`** collects facts: is the sender a free email provider? does the domain mismatch the company's? which fee/urgency/no-interview/Telegram keywords appear?
6. **`SignalDetector`** turns those facts into signals, each with a type, severity, evidence text, and score impact.
7. **`RiskEngine`** adds the score impacts, clamps to 0 to 100, and decides the level, status, and recommended actions.
8. **`_save_verification`** inserts one row into `verification_results` and one row per signal into `verification_signals`, then calls `commit()` once.
9. The API returns JSON: score, level, status, summary, signals, recommended actions.
10. **Streamlit** displays the metrics and the red signal boxes.

If you can explain these 10 steps without notes, you can handle most questions.

---

## 6. File-by-file walkthrough

| File | What it does (one line) |
| :--- | :--- |
| `run.py` | Starts Uvicorn on port 8000 |
| `app/main.py` | Creates the FastAPI app, registers error handlers and routes, `/` and `/health` |
| `app/database.py` | Connection, `get_db` dependency, `fetch_one`, `fetch_all`, `execute`, `update_row` |
| `app/core/config.py` | Reads settings (MySQL, JWT) from `.env` |
| `app/core/security.py` | Hash/verify passwords (bcrypt), create/decode JWT |
| `app/core/exceptions.py` | One consistent error format for the whole API |
| `app/api/deps.py` | `get_current_user`: the login check used by protected routes |
| `app/api/router.py` | Combines all route files under `/api/v1` |
| `app/api/routes/*.py` | auth, users, companies, jobs, recruiters, verification, reports |
| `app/schemas/*.py` | Request and response shapes |
| `app/services/*.py` | Logic + SQL for each feature |
| `app/verification/email_analyzer.py` | Free email? domain mismatch? keyword lists |
| `app/verification/url_analyzer.py` | Is the URL an IP address? https? valid? |
| `app/verification/job_analyzer.py` | Downloads the job page and looks for fee keywords |
| `app/verification/company_analyzer.py` | Is the company site reachable? https? mentions careers? |
| `app/verification/signal_detector.py` | Converts analyzer facts into signals with scores |
| `app/verification/risk_engine.py` | Adds scores, picks level/status/advice |
| `app/utils/validators.py` | `extract_domain`, `get_base_domain` |
| `app/utils/pagination.py` | Generic paginated response |
| `sql/schema.sql` | Creates the database and 7 tables |
| `sql/seed.sql` | Sample user, companies, jobs, recruiters |
| `streamlit_app/` | `app.py` (login) + pages: Dashboard, Verify Job, Verify Email, Reports, Analytics |
| `etl/` | Part B pipeline: `clean.py`, `load_postings.py`, `run_analysis.py`, `make_sample_data.py` (see `analytics-guide.md`) |
| `sql/analysis/` | Part B: ten documented analysis queries |
| `tests/` | 57 pytest tests; `conftest.py` prepares the test database |

---

## 7. The database

### Tables (7 for the app; Part B adds `job_postings` and `posting_signals`, see `analytics-guide.md`)

| Table | Stores | Notes |
| :--- | :--- | :--- |
| `users` | name, email (unique), hashed_password, is_active | Passwords are never stored in plain text |
| `companies` | name, website, domain, verified_domain | Reference data, used by the email check |
| `jobs` | company_id, title, location, salary, job_url | Belongs to a company |
| `recruiters` | company_id, name, email, email_domain | Belongs to a company |
| `verification_results` | user_id, company_id, type, risk_score, risk_level, status, summary | One row per check |
| `verification_signals` | verification_id, signal_type, severity, title, evidence, score_impact | Many per result |
| `reports` | user_id, company_id, job_id, report_type, description, status | User-submitted scam reports |

### Relationships (all one-to-many)
- 1 company has many jobs and many recruiters
- 1 user has many verification results and many reports
- 1 verification result has many signals

### What happens on delete (set in `schema.sql`)

| Delete this... | ...and this happens |
| :--- | :--- |
| a user | their results and reports are deleted (CASCADE) |
| a company | its jobs and recruiters are deleted (CASCADE) |
| a company | `company_id` in results/reports becomes NULL (SET NULL), so history is kept |
| a job | `job_id` in results/reports becomes NULL (SET NULL) |
| a verification result | its signals are deleted (CASCADE) |

MySQL does this automatically. My Python code never deletes child rows by hand.

### Indexes
On `users.email`, `companies.name`, `companies.domain`, `jobs.company_id`, `jobs.title`, `recruiters.email_domain`, `verification_results.user_id`, and the foreign key columns. They make lookups fast without scanning the whole table.

### How `database.py` works (explain this well, it's the heart of "no ORM")

```python
def get_db():                      # FastAPI dependency
    conn = get_connection()        # open a connection
    try:
        yield conn                 # the route/service uses it
    except Exception:
        conn.rollback()            # undo unsaved work if something failed
        raise
    finally:
        conn.close()               # always close
```

- **One connection per request**, always closed afterwards.
- `autocommit=False`: nothing is saved until I call `commit()`. This is what makes transactions possible.
- **Rows come back as dictionaries**, e.g. `{"id": 1, "name": "TechCorp"}` (`DictCursor`).
- Helpers: `fetch_one` (first row or None), `fetch_all` (list), `execute` (INSERT/UPDATE/DELETE, returns the new id).

### Parameterized queries (say this in the interview)

```python
fetch_one(db, "SELECT * FROM users WHERE email = %s", (email,))
```

The `%s` is a placeholder. The driver sends the value separately from the SQL text, so user input can never change the meaning of the query. That is how SQL injection is prevented. I never build SQL by joining user text into a string.

**One thing to know:** `update_row` puts *column names* into the SQL text. That is safe because the names come from my own Pydantic schema fields, never from the user. Only the *values* come from the user, and they go through `%s`.

### Transactions
A verification saves one result row plus N signal rows. I call `commit()` once after all inserts, so either everything is saved or nothing is. You never get a result with half its signals.

### N+1 problem (avoided)
The history page needs each result with its signals. A naive approach runs 1 query for results and then 1 query per result (1 + N). I run 1 query for results and 1 query for all their signals using `WHERE verification_id IN (...)`, then group them in Python. That is 2 queries total.

---

## 8. Login and security

### Register
`POST /auth/register` → check the email is not already used (else 409) → hash the password with bcrypt → insert → return the user (without the hash).

### Login
`POST /auth/login` → find user by email → `bcrypt.checkpw` compares the typed password to the stored hash → if correct, create a JWT and return it.

### What is a JWT?
A signed string with three parts: header, payload, signature. My payload has:
- `sub`: the user's id
- `exp`: expiry time (24 hours; `JWT_EXPIRE_MINUTES=1440`)
- `iat`: issued-at time

It is signed with `JWT_SECRET_KEY` using HS256. Anyone can *read* the payload, but nobody can *change* it without the secret, because the signature would no longer match. So never put passwords in a token.

### Using the token
Every protected request sends `Authorization: Bearer <token>`. `get_current_user`:
1. reads the header (`HTTPBearer(auto_error=False)`, so I return my own consistent 401 JSON instead of FastAPI's default),
2. verifies signature and expiry,
3. loads the user from MySQL (so a deleted or deactivated user is rejected even with a valid token),
4. returns the user row.

### Why bcrypt and not SHA-256 or MD5?
SHA-256 and MD5 are fast, so attackers can try billions of guesses per second. bcrypt is deliberately slow and adds a random **salt** (random data mixed in), so two users with the same password get different hashes, and precomputed "rainbow tables" don't work. bcrypt only reads the first 72 bytes, so I truncate to 72.

### Status codes used
200 OK, 201 Created, 204 No Content (delete), 401 not logged in / bad token, 403 inactive account, 404 not found, 409 duplicate email, 422 validation error, 500 unexpected error.

### Error format
All errors look the same: `{"success": false, "error": {"code": "COMPANY_NOT_FOUND", "message": "..."}}`. The generic 500 handler returns a safe message and does not leak internal details.

---
## 9. The verification engine (the core of the project)

Every check follows 4 stages:

```
Analyzers  ──▶  SignalDetector  ──▶  RiskEngine  ──▶  Save in MySQL
(collect facts)  (facts → signals)   (add up score)
```

### Email check: what it looks for

| Signal | Severity | Score | Triggered when |
| :--- | :--- | :--- | :--- |
| `PERSONAL_EMAIL` | MEDIUM | +10 | Sender uses gmail, yahoo, hotmail, outlook, aol, rediffmail, protonmail, yandex, icloud, live, mail.com |
| `DOMAIN_MISMATCH` | HIGH | +15 | Sender's domain differs from the company's domain (only when sender is *not* a free provider) |
| `REGISTRATION_FEE` | CRITICAL | +25 | Text contains "registration fee" |
| `TRAINING_FEE` | CRITICAL | +20 | Text contains "training fee" |
| `SECURITY_DEPOSIT` | CRITICAL | +20 | "security deposit" or "refundable deposit" |
| `PAYMENT_REQUEST` | CRITICAL | +30 | "laptop fee", "processing fee", "onboarding fee", "wire transfer", "crypto", "bitcoin", "gift card", "send money", "pay before starting" |
| `URGENT_LANGUAGE` | MEDIUM | +10 | "offer expires today", "act fast", "expires in 24 hours", "immediate joiner", etc. (one signal even if several match) |
| `NO_INTERVIEW_SELECTION` | HIGH | +10 | "selected without interview", "direct selection", "congratulations you are hired", etc. |
| `SUSPICIOUS_URL` | HIGH | +15 | "t.me/", "wa.me/", "chat.whatsapp.com", "bit.ly/", "tinyurl.com" (one signal) |

Each *payment* keyword found creates its own signal, so several fee words stack up.

### Job link check

| Signal | Severity | Score | Triggered when |
| :--- | :--- | :--- | :--- |
| `SUSPICIOUS_URL` (raw IP) | HIGH | +20 | URL host is an IP address like `10.0.0.5` |
| `SUSPICIOUS_URL` (http) | MEDIUM | +10 | URL is `http://`, not `https://` |
| `PAYMENT_REQUEST` | CRITICAL | +30 | The downloaded page text contains a fee/payment keyword |
| `SUSPICIOUS_URL` (invalid) | HIGH | +15 | URL cannot be parsed |

The app downloads the page (6-second timeout), reads the title and text with BeautifulSoup, and searches for the same payment keywords.

### Company check

| Signal | Severity | Score | Triggered when |
| :--- | :--- | :--- | :--- |
| `UNREACHABLE_WEBSITE` | HIGH | +10 | Site did not respond (5-second timeout) or returned an error |
| `MISSING_CAREERS_PAGE` | LOW | +5 | Site is reachable but the page doesn't mention "career", "job", or "join us" |
| `VERIFIED_COMPANY_DOMAIN` | LOW | **-10** | Website URL uses https. This is the only signal that *reduces* the score. |

### How the score becomes a level

Score = sum of all `score_impact` values, clamped between 0 and 100.

| Score | Level |
| :--- | :--- |
| 0 to 24 | LOW |
| 25 to 49 | MODERATE |
| 50 to 74 | HIGH |
| 75 to 100 | VERY_HIGH |

### The "status" field (different from level)

| Status | When |
| :--- | :--- |
| `VERIFIED_SIGNALS_FOUND` | Level is HIGH or VERY_HIGH, **or** two or more signals are HIGH/CRITICAL severity |
| `PARTIALLY_VERIFIED` | Level is MODERATE |
| `INSUFFICIENT_INFORMATION` | An `UNREACHABLE_WEBSITE` signal exists (and none of the rules above applied) |
| `INCONCLUSIVE` | Everything else (including a clean email) |

Because of the "two or more HIGH/CRITICAL" rule, a result can be MODERATE in level but `VERIFIED_SIGNALS_FOUND` in status. This is not a bug; the status says "several serious signs were found," the level says "the total is middling." A clean email gets `INCONCLUSIVE`, not "genuine," on purpose: absence of red flags doesn't prove an offer is real.

### Recommended actions
Plain advice picked from the signal types: don't send money (for fee/payment signals), contact the company through its official website (personal email), verify the sender domain (mismatch), avoid Telegram/shortened links (suspicious URL). If none apply, it suggests checking the company's official careers page.

### Worked examples (know at least two by heart)

**Example A: obvious scam**
- Sender `hr-techcorp@gmail.com`, subject "URGENT: Selection Notice", body: "selected without interview ... refundable registration fee of $100 via gift card"
- Signals: personal email (+10), registration fee (+25), gift card (+30), no-interview (+10)
- **Total 75, VERY_HIGH, VERIFIED_SIGNALS_FOUND**

**Example B: clean email**
- Sender `alice.smith@techcorp.com`, company site `techcorp.com`, body: "schedule a technical interview next week"
- No signals. **Total 0, LOW, INCONCLUSIVE**

**Example C: lookalike domain**
- Sender `hr@techcorp-careers.com`, company site `techcorp.com`, body: "continue on Telegram t.me/..., offer expires in 24 hours"
- Signals: domain mismatch (+15), Telegram link (+15), urgency (+10)
- **Total 40, MODERATE, VERIFIED_SIGNALS_FOUND** (two HIGH signals)

**Example D: job link `http://10.0.0.5/apply`**
- Signals: raw IP (+20), http (+10) → **Total 30, MODERATE, PARTIALLY_VERIFIED**

### How the email check finds the company
It extracts the domain from the website the user typed. It looks that domain up in the `companies` table; if not found, it tries the company name with `LIKE`. If found, the result is linked to that company, and the stored domain is used for mismatch detection when the user left the website blank.

### How to add a new rule (they may ask)
For a new keyword: add it to the right list in `email_analyzer.py` (e.g. `PAYMENT_KEYWORDS`). For a new kind of signal: add a check in `SignalDetector` that calls `create_signal(...)` with a type, severity, evidence, and score. `RiskEngine` and the database code need no changes, because they work on any list of signals. That is the benefit of the design.

---

## 10. API endpoints

All under `/api/v1`. "Auth" means a Bearer token is required.

| Method | Path | Auth | Purpose |
| :--- | :--- | :--- | :--- |
| POST | `/auth/register` | no | Create account (201) |
| POST | `/auth/login` | no | Get token |
| GET | `/auth/me` | yes | Current user |
| GET / PATCH | `/users/me` | yes | View / change name or password |
| GET | `/companies` | no | List, with `page`, `limit`, `domain` filter |
| GET | `/companies/search?q=` | no | Search name, domain, description |
| POST / PATCH / DELETE | `/companies`, `/companies/{id}` | yes | Create / update / delete |
| GET | `/companies/{id}` | no | One company |
| GET, POST, PATCH, DELETE | `/jobs...` | read: no, write: yes | Same pattern as companies, plus `company_id`, `location` filters |
| POST / GET | `/recruiters`, `/recruiters/{id}` | create: yes | Recruiter records |
| GET | `/companies/{id}/recruiters` | no | Recruiters of one company |
| POST | `/verification/email` | yes | Run email check |
| POST | `/verification/job` | yes | Run job-link check |
| POST | `/verification/company` | yes | Run company-website check |
| GET | `/verification/history` | yes | My past checks, with signals |
| GET | `/verification/{id}` | yes | One of my checks |
| POST / GET | `/reports`, `/reports/{id}` | yes | Submit / list / read my reports |
| GET | `/analytics/summary`, `/analytics/fraud-by/{dimension}`, `/analytics/features`, `/analytics/rule-performance`, `/analytics/threshold-sweep` | yes | Part B dataset statistics (see `analytics-guide.md`) |
| GET | `/health` | no | Is the API alive |

**Route order matters:** `/companies/search` is declared *before* `/companies/{company_id}`. Otherwise FastAPI would treat the word "search" as a company id and fail.

**Privacy rule:** verification and report lookups include `AND user_id = %s`, so one user gets a 404 (not someone else's data) if they guess another user's id.

---

## 11. The Streamlit app

| Page | What it does |
| :--- | :--- |
| Home (`app.py`) | Login and register tabs; after login shows the user and a Logout button |
| Dashboard | Lists my past verifications with expandable signals |
| Verify Job | Takes a job URL, shows score, summary, signals, advice |
| Verify Email | Takes sender, subject, body, company; same output |
| Reports | Submit a scam report; see my reports with status |
| Analytics | Part B: fake-posting statistics, rule performance, precision/recall trade-off |

How it works:
- `api_client.py` wraps `httpx` calls to the API. Pages never talk to MySQL.
- After login, the token is saved in `st.session_state`. Each page checks it and shows "please sign in" otherwise.
- Streamlit **re-runs the whole script** on every click. `session_state` is how it remembers things between runs.
- A full browser refresh clears `session_state`, so the user must log in again.
- Streamlit has no real "logout"; the button just clears the token from session state.

---

## 12. Testing

- **57 tests** with pytest, in `tests/`: auth (7), companies (6), jobs (2), reports (2), verification logic + one API test (6), plus Part B: ETL cleaning (9), posting rule analyzer (7), analytics (18).
- `conftest.py` creates a **separate database `jobshield_test`** from `schema.sql` and empties every table before each test, so real data is never touched and tests don't affect each other.
- Tests use FastAPI's `TestClient`, which calls the app without starting a server, against real MySQL. I use real MySQL instead of SQLite because SQL behaves differently across databases, and I want to catch real SQL mistakes.
- Fixtures: `client`, and `auth_headers` (registers and logs in a test user).

**Not covered by automated tests (say this honestly):** recruiters endpoints, `PATCH /users/me`, job/company verification endpoints (they need real internet), and the Streamlit pages. I checked those manually.

---

## 13. Docker

`docker-compose.yml` defines three containers:
1. **mysql**: MySQL 8.0; on first start it runs `schema.sql` and `seed.sql` automatically; has a health check.
2. **backend**: runs Uvicorn; waits until MySQL is healthy (`depends_on` with `service_healthy`); gets `MYSQL_HOST=mysql` (the service name acts as the hostname inside Docker's network).
3. **frontend**: runs Streamlit; `API_BASE_URL=http://backend:8000/api/v1`.

Start everything with `docker compose up --build`.

**Before the interview:** run it once yourself. Only say "I containerized it" if you have seen it work on your machine.

---

## 14. Concepts in simple words

| Concept | Simple explanation | Where in the project |
| :--- | :--- | :--- |
| **REST API** | Clients talk to the server using HTTP methods (GET read, POST create, PATCH update, DELETE remove) on URLs | All routes |
| **Dependency injection (`Depends`)** | FastAPI automatically runs a helper function and passes its result into your route | `get_db`, `get_current_user` |
| **Pydantic** | Python classes that validate data and convert types | `schemas/` |
| **`response_model`** | Filters the output to the declared fields, so `hashed_password` is never sent | Every route |
| **Async (`async def`)** | While waiting for slow I/O (web requests), the server can handle other requests | Verification routes, httpx calls |
| **JWT** | Signed token that proves who you are without a server-side session | `security.py` |
| **Salt** | Random data added before hashing so identical passwords hash differently | bcrypt |
| **Foreign key** | A column that must match an id in another table | `jobs.company_id` |
| **Transaction** | A group of SQL statements that succeed or fail together | `_save_verification` |
| **Pagination** | Return results in pages using `LIMIT` and `OFFSET` | List endpoints |
| **Parameterized query** | SQL with `%s` placeholders; values sent separately | All services |

### A JOIN you could write if asked
The app's services (Part A) run simple single-table queries. The Part B analysis queries do use JOINs (queries 06 and 08), a CROSS JOIN (07) and window functions (03). For Part A, a JOIN you could write is:

```sql
SELECT v.id, v.risk_score, c.name AS company
FROM verification_results v
LEFT JOIN companies c ON c.id = v.company_id
WHERE v.user_id = 1;
```
`LEFT JOIN` because `company_id` can be NULL, and we still want results without a company.

---
## 15. Cross-questions and answers

Answers are short on purpose. Say them in your own words.

### About the project

**Q1. Why did you build this?**
Job scams hit students a lot, and the warning signs are well known but easy to miss. I wanted a tool that checks them quickly and shows the evidence.

**Q2. Why not use machine learning or an LLM?**
Rules are explainable (the user sees exactly why), repeatable (same input gives the same score), free to run, and easy to test. I also don't have a labelled fraud dataset to train on. Next step: use confirmed user reports to tune the weights, and possibly train a model later while keeping the rule signals as explainable features.

**Q3. How did you choose the score weights?**
They are my own judgement: direct money requests are the strongest scam sign (+25 to +30), structural signs like a domain mismatch are medium (+15), softer signs like a free email or urgency are lower (+10). They are heuristics, not trained values, and I say so in the README.

**Q4. Can the scores be wrong?**
Yes. False negatives: a scammer who avoids my keywords and uses a lookalike domain that matches nothing I check. False positives: a legitimate page containing a word like "crypto" (for example a blockchain job) triggers a payment signal. That's why the tool reports risk and evidence, never "fake" or "genuine."

**Q5. A clean email gets INCONCLUSIVE, not "safe." Why?**
No red flags found doesn't prove an offer is real. Claiming "safe" would give false confidence.

**Q6. What's the difference between risk level and verification status?**
Level comes from the total score (LOW to VERY_HIGH). Status is a summary of how strong the evidence is: it is `VERIFIED_SIGNALS_FOUND` when the level is HIGH/VERY_HIGH or when two or more serious (HIGH/CRITICAL) signals exist.

**Q7. How would you add a new scam rule?**
Add a keyword to a list in `email_analyzer.py`, or add a check in `SignalDetector` that creates a signal with a type, severity, evidence and score. The risk engine and database code don't change, because they work on any list of signals.

**Q8. How does domain mismatch work, and where does it fail?**
I take the sender's domain and the company's domain, reduce both to the base domain (last two parts), and compare. It fails for domains like `company.co.in` or `.co.uk`, where the "last two parts" is `co.in`. A proper fix is the Public Suffix List (the `tldextract` library). It also doesn't catch a lookalike like `techcorp-careers.com` unless the company's real domain is known, which is why the user gives the website or I find the company in my table.

**Q9. What if the job website blocks your request?**
The request is in `try/except` with a timeout, so the API never crashes. For the job check, a failed fetch simply means no page-text signals (a weakness; I could report "could not fetch" as its own signal). For the company check, it becomes an `UNREACHABLE_WEBSITE` signal.

### Architecture

**Q10. Why separate Streamlit and FastAPI?**
The UI and logic stay independent. The same API could power a mobile app, the DB password stays in the backend, and validation and security live in one place.

**Q11. Why FastAPI over Flask or Django?**
Automatic request validation with Pydantic, automatic `/docs` page for testing, async support, and type hints. Django is heavier than needed for a small API; Flask needs extra libraries for validation and docs.

**Q12. What is Uvicorn?**
The server that actually listens on port 8000 and runs the FastAPI app. FastAPI defines the app; Uvicorn serves it.

**Q13. Why a services layer?**
Routes should only deal with HTTP. Services hold the logic and SQL so they're readable, reusable and testable.

**Q14. Walk me through one endpoint's code.**
Use `POST /reports`: the route receives `ReportCreate` (validated by Pydantic) and the logged-in user (from `get_current_user`); it calls `ReportService.create_report(db, user_id, data)`; that runs `INSERT INTO reports ... VALUES (%s, ...)` with status `'PENDING'`, calls `db.commit()`, reads the row back with `SELECT`, and returns it; FastAPI filters it through `ReportResponse` and sends JSON with status 201.

### Database

**Q15. Why MySQL?**
The data is relational (users have results, results have signals), and I want foreign keys, constraints and transactions so the data stays consistent.

**Q16. Why didn't you use an ORM like SQLAlchemy?**
The project has 7 tables and simple queries, so plain SQL keeps everything visible and shows I understand SQL directly. Trade-off: more hand-written code, no automatic schema migrations. For a large project with many relationships, I'd use an ORM.

**Q17. How do you prevent SQL injection?**
Parameterized queries: `%s` placeholders and values passed separately, so input is always treated as data, never as SQL. Even `' OR 1=1; DROP TABLE users;--` typed into search just matches nothing.

**Q18. What if the server crashes halfway through saving a verification?**
Nothing is saved. The result and its signals are inserted without committing in between, and I commit once at the end. If an error occurs, `get_db` calls `rollback()`.

**Q19. Do your LIKE searches use indexes?**
No. `LIKE '%text%'` (leading wildcard) forces a scan. It's fine for small data. For large data I'd use MySQL FULLTEXT indexes or a search engine.

**Q20. Do you use connection pooling?**
No, one connection per request, closed afterwards. It's simple and correct, but slower under heavy load. I'd add a pool (e.g. SQLAlchemy's pool or `DBUtils`) for production.

**Q21. How does pagination work?**
`page` and `limit` query parameters become `LIMIT limit OFFSET (page-1)*limit`. I run a separate `COUNT(*)` to return `total` and `total_pages`. OFFSET gets slow on very large tables; keyset pagination is the alternative.

**Q22. What's the difference between CASCADE and SET NULL in your schema?**
CASCADE deletes the child rows too (deleting a company deletes its jobs). SET NULL keeps the child row but clears the link (deleting a company keeps old verification history with `company_id = NULL`).

**Q23. How would you change the schema later without losing data?**
Write an `ALTER TABLE` script and run it on the existing database. Right now I only have `schema.sql`, which drops tables, so it's for fresh installs. For a team I'd use numbered migrations or a tool like Flyway or Alembic.

**Q24. Why do you store the `domain` separately from `website`?**
So I can compare domains quickly with an equality check and an index, instead of parsing URLs at query time.

### Security

**Q25. Explain the login flow.**
Register hashes the password with bcrypt and stores the hash. Login compares the typed password with the hash; if it matches, the server returns a JWT containing the user id and expiry. The client sends it in the `Authorization: Bearer` header on every protected request, and `get_current_user` verifies it and loads the user.

**Q26. Why is a JWT safe if anyone can read it?**
It's *signed*, not encrypted. Anyone can read the payload, but any change breaks the signature, so it can't be forged without the secret key. That's why I keep only the user id and times in it.

**Q27. How do you log out or revoke a token?**
I can't revoke it on the server; JWTs are stateless. Streamlit's logout just deletes the token from the session. The token stays valid until it expires (24 hours). For real revocation I'd use a blacklist in Redis, shorter expiry with refresh tokens, or a token version stored on the user.

**Q28. Can any logged-in user delete any company?**
Yes, that is a real gap. There are no roles, so any logged-in user can create, update or delete companies and jobs. In production I'd add an `is_admin` role and restrict those routes to admins. Verification results and reports are already private to their owner.

**Q29. Where is the JWT secret stored?**
In `.env`, which is in `.gitignore`. The code has a development default for convenience, and it must be changed in production.

**Q30. Is there any security risk in fetching the URL the user gives you?**
Yes: server-side request forgery (SSRF). Someone could submit an internal address (like `http://localhost:...` or a private IP) and make my server request it. I only read text and extract keywords, but a fix is to resolve the host and reject private and loopback IPs. I haven't implemented it yet.

**Q31. Why bcrypt?**
It's slow on purpose and salts each hash, so brute force and rainbow tables are impractical. SHA-256/MD5 are fast, which helps attackers.

### Code concepts

**Q32. What is `Depends`?**
FastAPI's dependency injection. A route says `db = Depends(get_db)` and FastAPI runs `get_db`, passes the result in, and runs the cleanup after the response. It avoids repeating code and makes it easy to replace in tests.

**Q33. You use `async def` but PyMySQL is blocking. Is that a problem?**
Good catch, and yes, it's a trade-off. The web requests (httpx) are truly async. But the PyMySQL calls inside async routes block the event loop while they run. At my scale it's fine. To fix it I'd either make those routes plain `def` (FastAPI then runs them in a thread pool) or use an async driver like `aiomysql`.

**Q34. What does Pydantic do for you?**
It validates input (email format, minimum lengths) and rejects bad requests with a 422 before my code runs. For output, `response_model` returns only declared fields, so `hashed_password` never leaves the server.

**Q35. Why httpx instead of requests?**
`requests` is synchronous and would freeze the server while waiting for a website. `httpx` supports async.

**Q36. How is error handling designed?**
I raise a `CustomAPIException(status, code, message)` from services. A registered handler turns it into a consistent JSON body. Separate handlers cover validation errors (422) and unexpected errors (500, with a safe message).

**Q37. Why does `/companies/search` come before `/companies/{id}`?**
FastAPI matches routes in order. If `{id}` came first, the word "search" would be read as an id and fail validation.

### Testing, Streamlit, Docker

**Q38. How do you test?**
57 pytest tests using FastAPI's TestClient against a real MySQL test database (`jobshield_test`), emptied before each test. Not covered: recruiters, profile update, internet-dependent checks, and the UI. I tested those manually.

**Q39. Why not SQLite for tests?**
SQL behaviour differs between databases. Testing on MySQL catches real SQL errors.

**Q40. How does Streamlit remember the logged-in user?**
`st.session_state` holds the token. Streamlit re-runs the script on every interaction, so session state is how values survive. A browser refresh clears it.

**Q41. Explain your Docker setup.**
Three containers: MySQL (loads `schema.sql` and `seed.sql` on first start, has a health check), the FastAPI backend (waits for MySQL to be healthy), and Streamlit (points at the backend through `API_BASE_URL`). Containers reach each other by service name.

### Improvement and reflection

**Q42. How would you scale or deploy this?**
Put the API behind a reverse proxy with HTTPS, run several Uvicorn workers, add a connection pool, move scraping to a background job queue (so slow websites don't hold requests), cache repeated lookups, and use a managed MySQL.

**Q43. What would you improve next?**
In priority order: admin roles; block private IPs (SSRF); use confirmed reports to tune weights; a proper domain library for `.co.in`-style domains; turn the extra URL checks into signals; connection pooling; migrations; rate limiting.

**Q44. What was the hardest part?**
Pick something true for you. Good options: designing the signal system so new rules need no other changes; making save-result-plus-signals atomic; handling websites that time out or block requests without crashing.

**Q45. What's one thing you'd do differently?**
Add roles from the start, and design the schema migrations earlier.

---

## 16. Known weak spots (admit these before they ask)

1. **No roles:** any logged-in user can modify companies and jobs.
2. **Rules are simple:** keyword substring matching, English only. "crypto" on a legitimate blockchain job page raises a false payment signal. Scammers can reword.
3. **Weights are my guesses,** not learned from data.
4. **Job check uses only fee keywords.** The code also detects urgency and no-interview phrases, and the URL analyzer finds extra flags (too many subdomains, very long URL, suspicious words), but the job check doesn't turn those into signals. A failed page fetch is not reported as a signal.
5. **Company check is shallow:** "uses https" is judged from the URL typed, not from a real certificate check; "has careers page" is a simple word search.
6. **Domain comparison** breaks for `.co.in` / `.co.uk` style domains.
7. **Jobs and recruiters are stored but not used by the verification logic.** `verification_results.job_id` is never filled. Only the `companies` table is used (email and company checks).
8. **Reports** are stored but have no admin review and don't affect scores.
9. **Tokens** can't be revoked before the 24-hour expiry.
10. **SSRF risk** when fetching user-supplied URLs.
11. **Blocking DB calls** inside async routes; **no connection pool.**
12. **`SECURITY_DEPOSIT` signals** don't trigger the "don't send money" advice (the advice only checks for "FEE" or "PAYMENT" in the signal type). Small bug.
13. **No migrations;** `schema.sql` drops tables, so it's for fresh installs only.
14. **Two endpoints return the current user** (`/auth/me` and `/users/me`), a minor duplication.
15. **Streamlit login form is pre-filled** with the demo user, for convenience only.

Knowing this list shows maturity: "I know the limits and I know how I'd fix them."

---

## 17. Don't say / do say

| Don't say | Say instead |
| :--- | :--- |
| "It detects all scams" or "99% accurate" | "It flags common scam patterns and gives an explainable risk score" |
| "It uses AI/ML" | "It's a rule-based engine, on purpose, so it's explainable" |
| "It's production ready" | "It's a working prototype; here's what I'd add for production" |
| "Recruiters/jobs tables feed the verification" | "Only companies are used by verification right now" |
| "I use an ORM / connection pooling" | "Plain SQL, one connection per request. Simple queries in the app, JOINs and window functions in the analysis" |
| "Logout invalidates the token" | "Logout clears it on the client; the token expires after 24 hours" |
| "I containerized and deployed it" | Only say this after you've run `docker compose up` yourself |

If you're asked how you built it, answer truthfully and be ready to open any file and explain it. The best preparation is to read these files once yourself and trace the flow: `app/database.py`, `app/api/deps.py`, `app/services/verification_service.py`, `app/verification/signal_detector.py`, `app/verification/risk_engine.py`.

---

## 18. Two-minute live demo script

1. **(10 s)** "Three parts: Streamlit UI, FastAPI backend, MySQL database."
2. **(15 s)** Log in with the seed user (`user@example.com` / `StrongPassword123`). "This calls `/auth/login`, gets a JWT, and Streamlit stores it in session state."
3. **(30 s)** Verify Email with the pre-filled scam sample. Show **75/100, VERY_HIGH** and the four signals. "Each signal has severity, evidence and a score. The scores add up to 75."
4. **(20 s)** Change the sender to `alice.smith@techcorp.com` and the body to a normal interview invite. Show **0/100, LOW**. "It doesn't flag everything."
5. **(15 s)** Open Dashboard. "History comes from MySQL, loaded with two queries."
6. **(30 s)** In MySQL: `SELECT id, risk_score, risk_level FROM verification_results;` and `SELECT signal_type, score_impact FROM verification_signals;` "One result row, with its signal rows, saved in one transaction."

Also have the `/docs` page ready (`http://127.0.0.1:8000/docs`) in case they ask to see the API directly.

---

## 19. Numbers cheat sheet

| Fact | Value |
| :--- | :--- |
| Database tables | 9 (7 for the app + `job_postings`, `posting_signals` for the analysis) |
| Automated tests | 57 (auth 7, companies 6, jobs 2, reports 2, verification 6, ETL clean 9, posting analyzer 7, analytics 18) |
| Streamlit pages | 5 (Dashboard, Verify Job, Verify Email, Reports, Analytics) plus the login home |
| Ports | UI 8501, API 8000, MySQL 3306 |
| JWT | HS256, expires in 1440 min (24 h), `sub` = user id |
| bcrypt | reads first 72 bytes only |
| Password minimum | 8 characters |
| Risk levels | 0-24 LOW, 25-49 MODERATE, 50-74 HIGH, 75-100 VERY_HIGH |
| Biggest score impacts | gift card/crypto etc. +30, registration fee +25, training fee / deposit +20 |
| Only negative score | HTTPS company site, -10 |
| Timeouts | job page 6 s, company site 5 s |
| Pagination | default 10 per page, max 100 |
| Seed login | `user@example.com` / `StrongPassword123` |
| Seed data | 1 user, 3 companies, 2 jobs, 2 recruiters |
| Test database | `jobshield_test` (separate from `jobshield`) |
