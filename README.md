# JobShield — Job & Company Verification Platform 🛡️

[![Python 3.11+](https://img.shields.io/badge/Python-3.11%2B-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.109-green.svg)](https://fastapi.tiangolo.com/)
[![SQLAlchemy](https://img.shields.io/badge/SQLAlchemy-2.0-red.svg)](https://www.sqlalchemy.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://www.mysql.com/)
[![Docker](https://img.shields.io/badge/Docker-Enabled-blue.svg)](https://www.docker.com/)
[![pytest](https://img.shields.io/badge/pytest-23%20Passed-brightgreen.svg)](https://docs.pytest.org/)

An **API-First Job & Company Verification Platform** designed to analyze suspicious job offers, recruiter emails, job URLs, and company details using a deterministic rule engine, external web scraping/APIs, and supporting LLM text analysis.

---

## 📌 Problem Statement

Students and job seekers frequently fall victim to job scams, fake recruiter emails, and fraudulent internship offers. Common indicators include:
- Demands for registration fees, training fees, or equipment security deposits.
- Recruiters contacting candidates from personal email domains (`@gmail.com`, `@yahoo.com`) while claiming to represent major corporations.
- Recruiter email domain mismatching official company web domains.
- Guaranteed job selection without undergoing standard technical/interview rounds.
- Artificial urgency and pressure tactics.

---

## 💡 Solution

**JobShield** provides an evidence-based risk assessment for job offers and recruiters without making absolute binary claims ("100% genuine" or "100% fake"). The system calculates a heuristic **Risk Score (0–100)**, assigns a **Risk Level** (`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`), detects structured **Verification Signals**, and provides actionable verification recommendations.

---

## 🏗️ High-Level Architecture

```
Client (Browser / API Client)
       |
       v
 Streamlit Frontend (streamlit_app/)
       |  (HTTP REST API Requests strictly via httpx)
       v
  FastAPI Application (app/main.py)
       |
       +---> API Routes (/api/v1/auth, /api/v1/companies, /api/v1/jobs, etc.)
       |        |
       |        v
       +---> Pydantic Schemas (Request/Response Validation)
       |        |
       |        v
       +---> Services Layer (auth_service, verification_service, report_service, etc.)
       |        |
       |        +---> Verification Engine (email, job, company, url analyzers)
       |        +---> Risk Engine (Deterministic rule-based scoring system: 0 to 100)
       |        +---> Integrations (LLM client for text entities, external HTTP API)
       |        |
       v        v
 SQLAlchemy 2.0 ORM / PyMySQL
       |
       v
 MySQL 8.0 / SQLite Database
```

---

## 🛠️ Technology Stack

- **Backend Framework**: FastAPI, Uvicorn
- **Language**: Python 3.11+ (Type Hints, Pydantic v2)
- **Database**: MySQL 8.0 (PyMySQL) with automatic SQLite fallback for rapid local execution
- **ORM & Migrations**: SQLAlchemy 2.0, Alembic
- **Authentication**: JWT (JSON Web Tokens), `pyjwt`, `bcrypt` password hashing
- **HTTP & Scraping**: `httpx`, `BeautifulSoup4`
- **Frontend**: Streamlit multi-page interface
- **Testing**: `pytest`, `pytest-asyncio`, FastAPI `TestClient`
- **DevOps**: Docker, `docker-compose`

---

## 🚀 Quick Start (Running Locally)

### 1. Clone & Setup Environment
```bash
git clone https://github.com/your-username/JobShield.git
cd TrustHire
python -m venv venv
# On Windows:
venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

pip install -r requirements.txt
```

### 2. Configure Environment Variables
Copy `.env.example` to `.env`:
```bash
cp .env.example .env
```

### 3. Run FastAPI Backend Server
```bash
python run.py
```
Backend API will start at: **http://127.0.0.1:8000**
Interactive API Swagger Docs: **http://127.0.0.1:8000/docs**

### 4. Run Streamlit Frontend App
In a separate terminal window:
```bash
streamlit run streamlit_app/app.py
```
Frontend UI will start at: **http://127.0.0.1:8501**

---

## 🐳 Docker Deployment

To launch MySQL, FastAPI Backend, and Streamlit Frontend using Docker Compose:

```bash
docker compose up --build
```

Services exposed:
- **FastAPI Backend**: `http://localhost:8000`
- **Swagger Documentation**: `http://localhost:8000/docs`
- **Streamlit Frontend**: `http://localhost:8501`
- **MySQL DB**: `localhost:3306`

---

## 🧪 Running Automated Tests

Run the complete pytest test suite (23 automated test cases covering Auth, Companies, Jobs, Verification Engine, and Reports):

```bash
pytest -v
```

---

## 📊 Verification Risk Scoring Rules

| Signal Type | Severity | Weight Impact | Description |
| :--- | :--- | :--- | :--- |
| `PAYMENT_REQUEST` | CRITICAL | **+30** | Request for money/fee before hiring |
| `REGISTRATION_FEE` | CRITICAL | **+25** | Demand for registration fee |
| `TRAINING_FEE` | CRITICAL | **+20** | Mandatory paid training fee |
| `SECURITY_DEPOSIT` | CRITICAL | **+20** | Equipment deposit request |
| `DOMAIN_MISMATCH` | HIGH | **+15** | Sender domain mismatches company website |
| `SUSPICIOUS_URL` | HIGH | **+15** | URL uses IP address / shorteners |
| `PERSONAL_EMAIL` | MEDIUM | **+10** | Recruiter uses free Gmail/Yahoo email |
| `URGENT_LANGUAGE` | MEDIUM | **+10** | Artificial pressure / expiration |
| `NO_INTERVIEW_SELECTION` | HIGH | **+10** | Immediate offer without interview |
| `UNREACHABLE_WEBSITE` | HIGH | **+10** | Company website fails connection |
| `VERIFIED_COMPANY_DOMAIN` | LOW | **-10** | Company uses secure HTTPS domain |

### Risk Levels:
- **0–24**: `LOW`
- **25–49**: `MODERATE`
- **50–74**: `HIGH`
- **75–100**: `VERY_HIGH`

-
