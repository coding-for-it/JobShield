# 🏛️ JobShield — System Architecture & Design Document

A practical architectural overview of JobShield, covering the application layers, verification workflow, authentication, database design, and Docker deployment.

---

## 📌 Architectural Principles

### 1. API-First Monolith

JobShield uses a simple, maintainable monolithic architecture with a single **FastAPI backend**.

The application is kept as one backend instead of using multiple microservices because the project does not require distributed services.

The main technologies are:

* Python
* FastAPI
* REST APIs
* Pydantic
* SQLAlchemy
* MySQL 8
* JWT authentication
* HTTPX
* BeautifulSoup
* Streamlit
* Pytest
* Docker

---

### 2. Layered Separation of Concerns

The backend is divided into separate layers so that each part has a clear responsibility.

#### Routes Layer — `app/api/routes/`

Responsible for:

* Defining HTTP endpoints
* Receiving requests
* Reading path, query, and body parameters
* Calling the appropriate service
* Returning HTTP responses and status codes

Example:

```text
POST /api/v1/verification/email
```

The route receives the request and passes it to the verification service.

---

#### Schemas Layer — `app/schemas/`

Uses **Pydantic** models for:

* Request validation
* Response validation
* Data type checking
* Serialization

For example, an email verification request can validate fields such as:

```text
sender_email
subject
body
company_name
job_title
```

Invalid or missing input is rejected before the business logic runs.

---

#### Services Layer — `app/services/`

Contains the main application logic.

Examples:

```text
auth_service.py
company_service.py
job_service.py
verification_service.py
report_service.py
```

The service layer coordinates:

```text
Request
   ↓
Analyzer
   ↓
Signal Detection
   ↓
Risk Calculation
   ↓
Database Storage
```

This keeps business logic separate from the HTTP routes.

---

#### Verification Engine — `app/verification/`

This is the main verification component of JobShield.

It contains:

```text
EmailAnalyzer
JobAnalyzer
CompanyAnalyzer
URLAnalyzer
SignalDetector
RiskEngine
```

Their responsibilities are:

| Component         | Responsibility                                        |
| ----------------- | ----------------------------------------------------- |
| `EmailAnalyzer`   | Checks recruiter emails and email content             |
| `JobAnalyzer`     | Checks job URLs and job-related information           |
| `CompanyAnalyzer` | Checks company website information                    |
| `URLAnalyzer`     | Checks URLs, domains and basic URL risks              |
| `SignalDetector`  | Converts detected issues into structured risk signals |
| `RiskEngine`      | Calculates the final risk score and risk level        |

The verification process is **rule-based**.

It does not depend on AI or machine-learning models for the final decision.

---

#### Database Layer — `app/database/` and `app/models/`

JobShield uses **MySQL 8** as its relational database.

SQLAlchemy is used as the ORM layer between Python and MySQL.

The database stores information such as:

```text
Users
Companies
Jobs
Recruiters
Verification Results
Verification Signals
Reports
```

The general flow is:

```text
FastAPI
   ↓
Service Layer
   ↓
SQLAlchemy
   ↓
MySQL
```

---

### 3. Decoupled Frontend

The Streamlit application is kept separate from the FastAPI backend.

The frontend does **not** directly access the database or backend Python functions.

Instead:

```text
Streamlit
    ↓
HTTP REST Request
    ↓
FastAPI
    ↓
Business Logic
    ↓
MySQL
```

This means the same FastAPI backend can later be used by another frontend or client without changing the core business logic.

---

### 4. Rule-Based and Explainable Verification

JobShield uses predefined rules to detect suspicious patterns.

For example:

```text
Payment request              +30
Suspicious domain mismatch   +15
Personal email address       +10
Suspicious URL               +15
Urgent language              +10
Official career match        -20
```

The actual rules are implemented inside the verification and risk-engine components.

The RiskEngine combines the detected signals and produces:

```text
Risk Score
Risk Level
Verification Status
Recommended Actions
```

The score is a **rule-based risk score**, not a statistical probability of fraud.

---

## 🔄 Verification Engine Sequence Diagram

```text
User / Client
      |
      | POST /api/v1/verification/email
      v
FastAPI Endpoint
      |
      | validate request
      v
Pydantic Schema
      |
      | valid request
      v
VerificationService
      |
      |----------------------+
      |                      |
      v                      v
EmailAnalyzer          URL / Domain Checks
      |                      |
      +----------+-----------+
                 |
                 v
          SignalDetector
                 |
                 | structured signals
                 v
             RiskEngine
                 |
                 | score, level,
                 | status, actions
                 v
           SQLAlchemy
                 |
                 v
              MySQL
                 |
                 | stored result
                 v
         VerificationService
                 |
                 v
          FastAPI Response
                 |
                 | 200 OK
                 v
             User / Client
```

---

# 📧 Email Verification Flow

When a user submits a recruiter email:

```text
User submits email
        ↓
POST /api/v1/verification/email
        ↓
Pydantic validates request
        ↓
EmailAnalyzer
        ↓
Checks:
    • Sender email
    • Sender domain
    • Company/domain relationship
    • Payment-related words
    • Urgency
    • Selection claims
    • Suspicious links
        ↓
SignalDetector
        ↓
Creates structured signals
        ↓
RiskEngine
        ↓
Calculates risk score
        ↓
Stores result + signals in MySQL
        ↓
Returns JSON response
```

Example response:

```json
{
    "risk_score": 40,
    "risk_level": "MODERATE",
    "verification_status": "VERIFICATION_INCONCLUSIVE",
    "signals": [
        {
            "type": "PAYMENT_REQUEST",
            "severity": "HIGH"
        },
        {
            "type": "URGENCY",
            "severity": "MEDIUM"
        }
    ]
}
```

---

# 💼 Job Verification Flow

For a job URL:

```text
User submits job URL
        ↓
POST /api/v1/verification/job
        ↓
Pydantic validation
        ↓
JobAnalyzer
        ↓
Fetches and parses available webpage content
        ↓
URLAnalyzer
        ↓
Checks URL/domain characteristics
        ↓
SignalDetector
        ↓
RiskEngine
        ↓
Risk score + status
        ↓
Store result in MySQL
        ↓
Return JSON response
```

BeautifulSoup can be used to parse available HTML content from webpages.

The system should not assume that every website can be fully verified because some websites may block requests, require JavaScript rendering, or provide incomplete information.

---

# 🏢 Company Verification Flow

For company verification:

```text
User submits company information
        ↓
POST /api/v1/verification/company
        ↓
CompanyAnalyzer
        ↓
Checks available company information
        ↓
Website / domain checks
        ↓
Careers/contact information checks
        ↓
SignalDetector
        ↓
RiskEngine
        ↓
Risk result
        ↓
MySQL
        ↓
JSON response
```

The system reports detected signals and available evidence rather than guaranteeing that a company is genuine or fraudulent.

---

# ⚠️ Risk Engine

The RiskEngine is deterministic.

The same input signals produce the same score.

Example:

```text
Payment request       +30
Personal email        +10
Urgent language       +10
--------------------------------
Total                 50
```

The score can then be mapped to a risk level.

Example:

```text
0–24    → LOW
25–49   → MODERATE
50–74   → HIGH
75–100  → VERY_HIGH
```

The exact thresholds and weights are defined in the implementation.

The RiskEngine does not use machine learning or an AI model.

This makes the result:

* Easy to explain
* Reproducible
* Transparent
* Easy to test
* Easy to modify

---

# 🔐 Authentication Architecture

JobShield uses **JWT-based authentication** for protected API endpoints.

The authentication flow is:

```text
User
  |
  | username + password
  v
POST /api/v1/auth/login
  |
  v
FastAPI
  |
  | verify credentials
  v
Generate JWT
  |
  v
Return access token
  |
  v
Client
```

For protected requests:

```text
Client
  |
  | Authorization: Bearer <JWT>
  v
FastAPI
  |
  v
JWT Dependency
  |
  | validate token
  v
Current User
  |
  v
Protected Endpoint
```

FastAPI dependencies are used to reuse the authentication logic across protected endpoints.

---

# 🗄️ Database Architecture

MySQL 8 is the primary database.

The main tables are:

```text
users
companies
jobs
recruiters
verification_results
verification_signals
reports
```

High-level relationships:

```text
User
 ├── Verification Results
 └── Reports

Company
 ├── Jobs
 ├── Recruiters
 ├── Verification Results
 └── Reports

Job
 ├── Verification Results
 └── Reports

Verification Result
 └── Verification Signals
```

SQLAlchemy models represent these database tables in Python.

---

# 🌐 API Architecture

The API follows REST principles.

Example endpoint groups:

```text
/api/v1/auth
/api/v1/companies
/api/v1/jobs
/api/v1/recruiters
/api/v1/verification
/api/v1/reports
```

Examples:

```text
POST   /api/v1/auth/register
POST   /api/v1/auth/login
GET    /api/v1/auth/me

GET    /api/v1/companies
POST   /api/v1/companies
GET    /api/v1/companies/{id}

GET    /api/v1/jobs
POST   /api/v1/jobs
GET    /api/v1/jobs/{id}

POST   /api/v1/verification/email
POST   /api/v1/verification/job
POST   /api/v1/verification/company

GET    /api/v1/verification/history

POST   /api/v1/reports
GET    /api/v1/reports
```

FastAPI automatically provides interactive API documentation through:

```text
/docs
/redoc
/openapi.json
```

---

# 🐳 Docker Deployment & Container Topology

```text
+-------------------------------------------------------------------+
|                         Docker Network                            |
|                                                                   |
|   +-----------------------+       +-----------------------+       |
|   |  jobshield_frontend   |       |   jobshield_backend   |       |
|   |    (Streamlit App)    | HTTP  |     (FastAPI App)     |       |
|   |      Port: 8501       |======>|      Port: 8000       |       |
|   +-----------------------+       +-----------------------+       |
|                                           |                       |
|                                           | PyMySQL               |
|                                           v                       |
|                               +-----------------------+           |
|                               |   jobshield_mysql     |           |
|                               |      (MySQL 8.0)      |           |
|                               |       Port: 3306      |           |
|                               +-----------------------+           |
|                                                                   |
+-------------------------------------------------------------------+
```

### Container responsibilities

**Frontend**

```text
Streamlit
Port: 8501
```

Responsible only for the user interface and API requests.

**Backend**

```text
FastAPI
Port: 8000
```

Responsible for:

* REST APIs
* Authentication
* Validation
* Business logic
* Verification
* Risk calculation
* Database operations

**Database**

```text
MySQL 8
Port: 3306
```

Responsible for persistent application data.

---

# 📁 Project Structure

```text
JobShield/
│
├── app/
│   ├── main.py
│   │
│   ├── api/
│   │   ├── deps.py
│   │   └── routes/
│   │       ├── auth.py
│   │       ├── companies.py
│   │       ├── jobs.py
│   │       ├── recruiters.py
│   │       ├── verification.py
│   │       └── reports.py
│   │
│   ├── core/
│   │   ├── config.py
│   │   ├── security.py
│   │   └── exceptions.py
│   │
│   ├── database/
│   │   ├── connection.py
│   │   └── base.py
│   │
│   ├── models/
│   │   ├── user.py
│   │   ├── company.py
│   │   ├── job.py
│   │   ├── recruiter.py
│   │   ├── verification.py
│   │   └── report.py
│   │
│   ├── schemas/
│   │   ├── auth.py
│   │   ├── company.py
│   │   ├── job.py
│   │   ├── verification.py
│   │   └── report.py
│   │
│   ├── services/
│   │   ├── auth_service.py
│   │   ├── company_service.py
│   │   ├── job_service.py
│   │   ├── verification_service.py
│   │   └── report_service.py
│   │
│   ├── verification/
│   │   ├── email_analyzer.py
│   │   ├── job_analyzer.py
│   │   ├── company_analyzer.py
│   │   ├── url_analyzer.py
│   │   ├── signal_detector.py
│   │   └── risk_engine.py
│   │
│   └── utils/
│       ├── pagination.py
│       └── validators.py
│
├── streamlit_app/
│
├── tests/
│
├── docs/
│   ├── architecture.md
│   └── interview-notes.md
│
├── requirements.txt
├── .env.example
├── .gitignore
├── Dockerfile
├── docker-compose.yml
└── README.md
```

---

# 🧪 Testing Architecture

The project uses **Pytest** for automated testing.

Tests cover areas such as:

```text
Authentication
Company APIs
Job APIs
Verification APIs
Report APIs
```

External HTTP requests should be mocked during tests so that tests do not depend on the availability of external websites.

The goal is to verify both individual API endpoints and important verification logic.

---

# 🔗 Overall Architecture

The complete application flow can be summarized as:

```text
                 USER
                   |
                   v
              Streamlit
                   |
                   | HTTP REST
                   v
               FastAPI
                   |
          +--------+--------+
          |                 |
          v                 v
       Pydantic          JWT Auth
       Validation
          |
          v
       Services
          |
          v
   Verification Engine
          |
    +-----+-----+--------+
    |     |     |        |
    v     v     v        v
  Email  Job  Company   URL
 Analyzer Analyzer Analyzer Analyzer
    |     |     |        |
    +-----+-----+--------+
              |
              v
       SignalDetector
              |
              v
          RiskEngine
              |
              v
          SQLAlchemy
              |
              v
            MySQL
```

---

## 🎯 Design Goal

The main design goal of JobShield is to keep the system **simple, explainable, and maintainable**.

The project demonstrates practical knowledge of:

* Python
* REST API development
* FastAPI
* Pydantic validation
* JWT authentication
* SQLAlchemy
* MySQL
* HTTP requests
* HTML parsing
* Rule-based verification
* Database relationships
* Automated testing
* Docker
* Streamlit API integration

The verification process is intentionally rule-based so that each detected signal and its effect on the risk score can be understood and explained clearly.
