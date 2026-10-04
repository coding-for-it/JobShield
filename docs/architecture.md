# 🏛️ JobShield — System Architecture & Design Document

Comprehensive architectural overview detailing design principles, layer responsibilities, authentication security, engine workflows, and container topology.

---

## 📌 Architectural Principles

1. **API-First Monolith**: Simple, maintainable, single FastAPI backend without unnecessary microservice overhead.
2. **Layered Separation of Concerns**:
   - **Routes Layer (`app/api/routes/`)**: HTTP endpoints, parameter extraction, and status code handling.
   - **Schemas Layer (`app/schemas/`)**: Pydantic v2 data models for input validation and output serialization.
   - **Services Layer (`app/services/`)**: Business logic and the SQL queries for each feature (commits the transaction when an operation is complete).
   - **Verification Engine (`app/verification/`)**: Signal extraction analyzers (`EmailAnalyzer`, `JobAnalyzer`, `CompanyAnalyzer`, `URLAnalyzer`), signal detection (`SignalDetector`), and deterministic scoring (`RiskEngine`).
   - **Database Layer (`app/database.py`)**: plain SQL on MySQL 8.0 through the PyMySQL driver. One connection per request, `%s` placeholders for values, explicit `commit()`. Table definitions live in `sql/schema.sql`.
3. **Decoupled Frontend**: Streamlit UI consumes FastAPI backend exclusively over HTTP REST calls via `APIClient`.
4. **Resilience & Fallbacks**: Non-blocking `httpx` calls with strict timeouts; if a website cannot be reached, that is reported as a signal (e.g. `UNREACHABLE_WEBSITE`) and the rule engine continues without erroring.

---

## 🔄 Verification Engine Sequence Diagram

```
User / Client         FastAPI Endpoint      VerificationService    Analyzers & Detectors    RiskEngine         MySQL DB
     |                       |                       |                      |                   |                 |
     |--- POST /verify/email>|                       |                      |                   |                 |
     |                       |--- verify_email() --->|                      |                   |                 |
     |                       |                       |-- EmailAnalyzer ---->|                   |                 |
     |                       |                       |   analyze_email()    |                   |                 |
     |                       |                       |<-- raw_signals ------|                   |                 |
     |                       |                       |                      |                   |                 |
     |                       |                       |-- SignalDetector --->|                   |                 |
     |                       |                       |   detect_signals()   |                   |                 |
     |                       |                       |<-- structured_sigs --|                   |                 |
     |                       |                       |                                          |                 |
     |                       |                       |---- calculate_risk_score(signals) ------>|                 |
     |                       |                       |<--- (score, level, status, actions) -----|                 |
     |                       |                       |                                                            |
     |                       |                       |---------------- INSERT Verification & Signals ------------>|
     |                       |                       |<--------------- OK (db_verification) ----------------------|
     |                       |<-- 200 OK (JSON) -----|
     |<-- VerificationResult-|
```

---

## 🐳 Docker Deployment & Container Topology

```
+-------------------------------------------------------------------+
|                         Docker Network                            |
|                                                                   |
|   +-----------------------+           +-----------------------+   |
|   |  jobshield_frontend   |           |   jobshield_backend   |   |
|   |   (Streamlit App)     |  HTTP     |     (FastAPI App)     |   |
|   |    Port: 8501         |=========> |      Port: 8000       |   |
|   +-----------------------+           +-----------------------+   |
|                                                   |               |
|                                                   | PyMySQL       |
|                                                   v               |
|                                       +-----------------------+   |
|                                       |    jobshield_mysql    |   |
|                                       |      (MySQL 8.0)      |   |
|                                       |      Port: 3306       |   |
|                                       +-----------------------+   |
+-------------------------------------------------------------------+
```

---

## Part B: Data analysis layer

The same rule engine is also applied to a labelled dataset of job postings, so its performance can be measured.

```
CSV ──▶ etl/clean.py ──▶ PostingAnalyzer + RiskEngine ──▶ job_postings, posting_signals (MySQL)
                                                              │
        sql/analysis/*.sql (run by etl/run_analysis.py) ◀─────┤
        AnalyticsService ──▶ /api/v1/analytics/* ──▶ Streamlit "Analytics" page
```

- `etl/` is a command-line pipeline (not part of the web API). It imports the same `app.database` connection and the same `app.verification` rules.
- `PostingAnalyzer` reuses the keyword lists from `EmailAnalyzer`, so there is one source of truth for the scam rules.
- Analytics endpoints are read-only and require a login token. The group-by column comes from a fixed whitelist, never from user input.
- See `analytics-guide.md` for the metrics and `findings.md` for the results template.
