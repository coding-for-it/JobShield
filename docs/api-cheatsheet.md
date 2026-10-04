# 🚀 JobShield — API Cheat Sheet & REST Reference

Quick-reference cheat sheet for HTTP methods, API authentication, path/query parameters, status codes, Pydantic schemas, and example API requests/responses.

---

## 📌 REST API Core Cheat Sheet

| HTTP Method | Operation | Usage in JobShield | Idempotent |
| :--- | :--- | :--- | :--- |
| `GET` | Read | Fetch user profile, list companies, search jobs, get report details | Yes |
| `POST` | Create / Execute | Register user, login, verify email/job, submit report | No |
| `PUT` | Full Replace | Overwrite full resource entity | Yes |
| `PATCH` | Partial Update | Modify select company or job fields | No |
| `DELETE` | Remove | Delete company or job posting | Yes |

---

## 🔑 Request Parameter Types

1. **Path Parameter**: Part of the URL endpoint path identifying a specific resource.
   - Example: `GET /api/v1/companies/{company_id}` (`company_id` = 1)
2. **Query Parameter**: Key-value pairs following `?` in the URL used for filtering & pagination.
   - Example: `GET /api/v1/jobs?page=1&limit=10&location=Remote`
3. **Request Body**: JSON payload sent in HTTP `POST`/`PATCH` requests.
   - Example: `{"name": "TechCorp", "website": "https://techcorp.com"}`
4. **Headers**: HTTP metadata sent with requests.
   - Example: `Authorization: Bearer <jwt_access_token>`

---

## 🚦 HTTP Status Codes Quick Reference

- `200 OK`: Request succeeded.
- `201 Created`: New resource successfully created.
- `204 No Content`: Resource deleted successfully (no response body).
- `400 Bad Request`: Malformed client request syntax.
- `401 Unauthorized`: Missing or invalid JWT Bearer token.
- `403 Forbidden`: Account inactive or forbidden action.
- `404 Not Found`: Requested entity ID does not exist.
- `409 Conflict`: Resource state conflict (e.g. duplicate email).
- `422 Unprocessable Entity`: Pydantic schema validation failure.
- `500 Internal Server Error`: Unexpected backend server error.

---

## 📋 Example API Requests & Responses

### 1. User Registration (`POST /api/v1/auth/register`)
**Request:**
```json
POST /api/v1/auth/register
Content-Type: application/json

{
  "name": "Alex Johnson",
  "email": "alex@example.com",
  "password": "StrongPassword123"
}
```
**Response (201 Created):**
```json
{
  "id": 1,
  "name": "Alex Johnson",
  "email": "alex@example.com",
  "is_active": true,
  "created_at": "2026-09-30T10:00:00Z",
  "updated_at": "2026-09-30T10:00:00Z"
}
```

---

### 2. User Login (`POST /api/v1/auth/login`)
**Request:**
```json
POST /api/v1/auth/login
Content-Type: application/json

{
  "email": "alex@example.com",
  "password": "StrongPassword123"
}
```
**Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

---

### 3. Verify Recruiter Email (`POST /api/v1/verification/email`)
**Request:**
```json
POST /api/v1/verification/email
Authorization: Bearer <jwt_access_token>
Content-Type: application/json

{
  "company_name": "TechCorp Solutions",
  "company_website": "https://techcorp.com",
  "sender_name": "HR Placement Team",
  "sender_email": "hr-techcorp@gmail.com",
  "subject": "Selection Notice: Data Analyst Position",
  "body": "Congratulations! You are selected without interview. Please pay $50 registration fee to reserve equipment."
}
```
**Response (200 OK):**
```json
{
  "id": 1,
  "user_id": 1,
  "company_id": 1,
  "job_id": null,
  "verification_type": "email",
  "risk_score": 60,
  "risk_level": "HIGH",
  "verification_status": "VERIFIED_SIGNALS_FOUND",
  "summary": "Email verification for hr-techcorp@gmail.com regarding 'TechCorp Solutions'. Risk Level: HIGH (Score: 60/100). 3 risk signals detected.",
  "created_at": "2026-09-30T10:05:00Z",
  "signals": [
    {
      "id": 1,
      "signal_type": "PERSONAL_EMAIL",
      "severity": "MEDIUM",
      "title": "Recruiter Uses Free/Personal Email Domain",
      "description": "The recruiter sent this offer from a free email provider (e.g. Gmail/Yahoo/Hotmail) rather than an official company domain.",
      "evidence": "Sender Email: hr-techcorp@gmail.com",
      "score_impact": 10
    },
    {
      "id": 2,
      "signal_type": "REGISTRATION_FEE",
      "severity": "CRITICAL",
      "title": "Registration Fee Requested",
      "description": "Legitimate employers never charge candidates registration fees for job applications.",
      "evidence": "Detected trigger phrase: 'registration fee'",
      "score_impact": 25
    },
    {
      "id": 3,
      "signal_type": "NO_INTERVIEW_SELECTION",
      "severity": "HIGH",
      "title": "Immediate Job Offer Without Interview",
      "description": "The candidate was purportedly selected without undergoing standard interview procedures.",
      "evidence": "Detected phrases: selected without interview",
      "score_impact": 10
    }
  ],
  "recommended_actions": [
    "DO NOT send money, pay registration fees, or transfer cryptocurrency for job placement.",
    "Contact the company directly through their official website contact page to verify the recruiter's identity."
  ]
}
```

---

### 4. Paginated Jobs List (`GET /api/v1/jobs?page=1&limit=2`)
**Request:**
```json
GET /api/v1/jobs?page=1&limit=2
```
**Response (200 OK):**
```json
{
  "data": [
    {
      "id": 1,
      "company_id": 1,
      "title": "Junior Backend Developer (Python/FastAPI)",
      "description": "Build scalable RESTful APIs using Python, FastAPI, MySQL, and Docker.",
      "location": "Remote",
      "job_url": "https://techcorp.com/careers/backend-dev",
      "salary_text": "$70,000 - $85,000",
      "source": "Official Site",
      "created_at": "2026-09-30T10:00:00Z",
      "updated_at": "2026-09-30T10:00:00Z"
    }
  ],
  "pagination": {
    "page": 1,
    "limit": 2,
    "total": 1,
    "total_pages": 1
  }
}
```

---

## Analytics endpoints (Part B)

All require `Authorization: Bearer <token>` and are read-only (`GET`).

| Endpoint | Query parameters | Returns |
| :--- | :--- | :--- |
| `/analytics/summary` | `threshold` (0-100, default 25) | dataset names, totals, fraud rate, confusion matrix, precision, recall, accuracy, always-real accuracy |
| `/analytics/fraud-by/{dimension}` | `min_postings` (default 30), `limit` (default 15) | ranked fraud % per category. `dimension` is one of `employment_type`, `industry`, `required_experience`, `required_education`, `job_function`, `country` (anything else returns 422) |
| `/analytics/features` | none | fraud % when each yes/no feature is 0 vs 1 |
| `/analytics/rule-performance` | none | per rule: postings flagged, fraud flagged, precision, coverage, lift |
| `/analytics/threshold-sweep` | none | precision and recall at thresholds 5 to 75 |

Example:
```
GET /api/v1/analytics/summary?threshold=25
{ "datasets": ["fake_job_postings"], "total_postings": ..., "fraud_postings": ...,
  "confusion_matrix": {"true_positives": ..., "false_positives": ..., "false_negatives": ..., "true_negatives": ...},
  "precision_pct": ..., "recall_pct": ..., "accuracy_pct": ..., "always_real_accuracy_pct": ... }
```
`precision_pct` is `null` when nothing is flagged (undefined, not zero).
