# 🎓 JobShield — Interview Master Guide & 52 Technical Q&As

This document contains interview cheat sheets, system explanations, and **52 structured interview questions & answers** for explaining **JobShield** in technical interviews for Python, Backend, API, Data, and Software Engineering roles.

---

# ⏱️ Elevator Summaries

## 30-Second Pitch

> "I built JobShield, an API-first Job and Company Verification Platform using Python, FastAPI, MySQL, and Docker. It helps users assess suspicious job offers, recruiter emails, and job URLs by checking signals such as payment requests, domain mismatches, suspicious links, and personal email addresses. The system uses a deterministic rule-based engine to generate an explainable risk score from 0 to 100. I also used JWT authentication, Pydantic validation, SQLAlchemy, and a separate Streamlit frontend that communicates with the backend through REST APIs."

---

## 1-Minute Pitch

> "JobShield is a REST API-based backend platform built with Python, FastAPI, SQLAlchemy, and MySQL. The purpose is to help job seekers assess suspicious recruitment opportunities using available evidence and predefined verification rules.
>
> I designed it using a layered architecture. FastAPI handles the REST endpoints, Pydantic validates incoming data, JWT handles authentication, and the service layer contains the main business logic. The verification engine contains separate analyzers for emails, jobs, companies, and URLs. These analyzers identify suspicious signals, and the SignalDetector converts them into structured signals. The RiskEngine then applies predefined weights and generates a risk score and risk level.
>
> I used HTTPX and BeautifulSoup for checking and parsing available webpage information. SQLAlchemy handles communication with MySQL. I also built a Streamlit frontend that communicates with FastAPI only through HTTP REST APIs. The project includes Pytest tests and can be run using Docker Compose."

---

## 2-Minute Technical Deep Dive

> "Architecturally, JobShield is an API-first monolithic application. The main backend is built using FastAPI and follows a layered structure.
>
> The route layer handles HTTP requests, Pydantic schemas validate request and response data, and the service layer contains the main application logic. JWT authentication is implemented using FastAPI dependencies, so protected endpoints can identify the current user from the Bearer token.
>
> The main business logic is in the verification engine. When a user submits an email, job URL, or company, the appropriate analyzer checks the available information. For example, EmailAnalyzer checks the sender domain, personal email providers, payment-related language, urgency, suspicious links, and other predefined patterns. JobAnalyzer and URLAnalyzer perform similar checks for job pages and URLs.
>
> The SignalDetector converts these findings into structured risk signals. The RiskEngine then applies predefined weights to those signals and calculates a score between 0 and 100. It also maps the score to a risk level and provides recommended actions.
>
> The verification result and individual signals are stored in MySQL using SQLAlchemy. The frontend is built separately using Streamlit and communicates with the backend only through REST APIs. The project is tested with Pytest and can be deployed using Docker Compose."

---

# 🏗️ Deep-Dive System Architecture & Concepts

## 1. JWT Authentication Flow

### Step 1 — User Registration

The client sends user information to:

```text
POST /api/v1/auth/register
```

The password is hashed before being stored in the database.

The original password is never stored directly.

---

### Step 2 — User Login

The client sends credentials to:

```text
POST /api/v1/auth/login
```

The server:

1. Finds the user.
2. Verifies the password against the stored hash.
3. Creates a JWT access token.
4. Returns the token to the client.

The JWT contains claims such as:

```text
sub → user ID
exp → expiration time
iat → issued-at time
```

---

### Step 3 — Protected API Access

The client sends:

```text
Authorization: Bearer <jwt_token>
```

with protected requests.

---

### Step 4 — JWT Dependency

FastAPI uses:

```python
Depends(get_current_user)
```

The dependency:

1. Extracts the Bearer token.
2. Validates the JWT.
3. Gets the user ID.
4. Retrieves the user.
5. Makes the authenticated user available to the endpoint.

### Interview answer

> "After login, the server generates a JWT access token. The client sends that token in the Authorization Bearer header for protected endpoints. I use a reusable FastAPI dependency called get_current_user to validate the token and identify the current user."

### Memory trick

```text
JWT = ID card
Bearer token = carrying the ID card
Depends() = security guard checking the ID
```

---

# 2. FastAPI `Depends()` Explanation

`Depends()` is FastAPI's dependency injection mechanism.

It allows reusable logic to be shared between endpoints.

Examples include:

```text
get_db()
get_current_user()
```

For example:

```python
@app.get("/companies")
def get_companies(
    current_user=Depends(get_current_user)
):
    ...
```

FastAPI runs `get_current_user()` before the endpoint continues.

### Why it is useful

Without dependencies, authentication logic would have to be repeated in many endpoints.

With dependencies, the same authentication logic can be reused.

---

# 3. Pydantic Schema Validation

Pydantic is used to validate incoming API data.

For example:

```python
class JobCreate(BaseModel):
    title: str
    company_id: int
    url: str
```

If the client sends invalid data, FastAPI returns a validation error before the service logic executes.

Pydantic is therefore responsible for:

* Type validation
* Required fields
* Field constraints
* Request parsing
* Response serialization

---

# 4. Rule-Based Verification Engine

JobShield uses a **deterministic rule-based verification system**.

The basic flow is:

```text
Input
  ↓
Analyzer
  ↓
Detected patterns
  ↓
SignalDetector
  ↓
Risk signals
  ↓
RiskEngine
  ↓
Risk score
```

Example:

```text
Payment request       +30
Personal email        +10
Urgent language       +10
---------------------------
Total                  50
```

The score is then converted into a risk level.

The important point is:

> "The final risk score is calculated by predefined rules rather than an AI or machine-learning model."

This makes the result easier to understand and test.

---

# ❓ 52 Interview Questions & Answers

# Category 1: Python Core

## Q1. What is the difference between synchronous and asynchronous functions in Python?

**Answer:**

A synchronous function runs one operation at a time and waits for it to finish before continuing.

An asynchronous function uses `async def` and can use `await` for operations that involve waiting, such as network requests.

### In JobShield

Async functionality is useful when the application needs to make HTTP requests to webpages.

### Follow-up: When should you not use async?

For CPU-heavy work, async by itself does not make the computation faster.

### Simple memory trick

```text
sync  → wait
async → don't block while waiting
```

---

## Q2. How does password hashing work, and why should passwords not be stored directly?

**Answer:**

Passwords should not be stored as plain text.

Instead, the application stores a password hash. During login, the entered password is checked against the stored hash.

A password hashing algorithm such as bcrypt is designed to make brute-force attacks more difficult.

### In JobShield

Passwords are hashed before being stored in MySQL.

---

## Q3. Explain Python type hints and Pydantic validation.

**Answer:**

Type hints tell Python developers what type of value is expected.

For example:

```python
name: str
age: int
```

Pydantic performs runtime validation of API data.

### In JobShield

Pydantic schemas validate incoming JSON requests before the application processes them.

---

## Q4. What are Python context managers?

**Answer:**

A context manager manages resources automatically.

The `with` statement is commonly used for this.

Example:

```python
with open("file.txt") as file:
    data = file.read()
```

After the block finishes, the resource is cleaned up.

### In JobShield

Context-manager style resource handling is used where appropriate for HTTP clients and testing.

---

## Q5. What is the difference between list, tuple, set, and dictionary?

**Answer:**

```text
List   → ordered, mutable collection
Tuple  → ordered, immutable collection
Set    → unique values
Dict   → key-value pairs
```

Example:

```python
names = ["A", "B"]       # list
point = (10, 20)         # tuple
domains = {"gmail.com"}  # set
user = {"id": 1}         # dictionary
```

### In JobShield

A set is useful when checking whether a domain belongs to a predefined collection of free email providers.

---

# Category 2: FastAPI

## Q6. Why did you use FastAPI?

**Answer:**

I chose FastAPI because it is well suited for building REST APIs in Python.

It provides:

* Request validation through Pydantic
* Automatic API documentation
* Dependency injection
* Async support
* Clear route definitions
* Good developer experience

### In JobShield

FastAPI is the main backend framework.

---

## Q7. How does FastAPI generate Swagger documentation?

**Answer:**

FastAPI uses route definitions, Python type hints, and Pydantic schemas to generate an OpenAPI specification automatically.

The documentation is available at:

```text
/docs
/redoc
```

This makes it easy to test and understand the API.

---

## Q8. What is `APIRouter`?

**Answer:**

`APIRouter` helps divide API endpoints into separate modules.

For example:

```text
auth.py
companies.py
jobs.py
verification.py
reports.py
```

These routers can then be included in the main FastAPI application.

### Why?

It keeps the project organized instead of putting every endpoint into `main.py`.

---

## Q9. How do exception handlers work in FastAPI?

**Answer:**

Exception handlers allow the application to return a consistent response when an error occurs.

For example, JobShield can return:

```json
{
    "success": false,
    "error": {
        "code": "NOT_FOUND",
        "message": "Company not found"
    }
}
```

This provides a consistent API response structure.

---

## Q10. What are path parameters, query parameters, and request bodies?

**Answer:**

### Path parameter

Part of the URL:

```text
/jobs/10
```

Here `10` is the ID.

### Query parameter

Comes after `?`:

```text
/jobs?page=1&limit=10
```

### Request body

JSON data sent with the request:

```json
{
    "title": "Data Analyst",
    "company_id": 10
}
```

---

# Category 3: REST API

## Q11. What are important REST API principles?

**Answer:**

Important REST principles include:

* Client-server separation
* Statelessness
* Uniform interface
* Resource-based URLs
* Standard HTTP methods

### In JobShield

The Streamlit frontend communicates with the FastAPI backend through HTTP REST APIs.

---

## Q12. What is the difference between PUT and PATCH?

**Answer:**

`PUT` is generally used to replace a resource.

`PATCH` is used to partially update a resource.

Example:

```text
PUT   /companies/10
PATCH /companies/10
```

If only the company name needs to change, PATCH is appropriate.

---

## Q13. Explain common HTTP status codes.

**Answer:**

```text
200 → successful request
201 → resource created
204 → successful request with no response body
400 → bad request
401 → authentication required/invalid
403 → authenticated but not allowed
404 → resource not found
409 → conflict
422 → validation error
500 → server error
```

---

## Q14. Why is API pagination useful?

**Answer:**

Imagine there are thousands of jobs.

Returning all of them in one response can increase response size and database work.

Pagination allows the client to request smaller portions.

Example:

```text
/jobs?page=1&limit=20
```

Instead of returning 10,000 records, the API returns only the required records.

---

## Q15. Why should passwords never be returned in API responses?

**Answer:**

Passwords and password hashes are sensitive information.

They should never be included in normal API responses.

The response schema should expose only safe user information such as:

```text
id
email
name
status
```

---

# Category 4: JWT & Authentication

## Q16. What is the structure of a JWT?

**Answer:**

A JWT has three parts:

```text
Header.Payload.Signature
```

### Header

Contains information about the token type and signing algorithm.

### Payload

Contains claims such as:

```text
sub
exp
iat
```

### Signature

Used to verify that the token was signed by the trusted server.

---

## Q17. What is the difference between session authentication and JWT authentication?

**Answer:**

With traditional session authentication, the server maintains session information.

With JWT authentication, the client carries the signed token with each request.

The server validates the token to identify the user.

### In JobShield

JWT is used for authentication of protected API endpoints.

---

## Q18. What does `OAuth2PasswordBearer` do in FastAPI?

**Answer:**

It extracts the Bearer token from the HTTP Authorization header.

For example:

```text
Authorization: Bearer eyJ...
```

It does not by itself perform all authentication logic. The application still needs to validate and decode the token.

---

## Q19. How can a JWT be invalidated before expiration?

**Answer:**

JWTs are normally stateless.

If immediate invalidation is required, the application can use approaches such as:

* Token versioning
* Token blacklist
* Short token expiration with refresh-token mechanisms

The exact approach depends on the application's requirements.

---

## Q20. Why should JWT secrets be stored in environment variables?

**Answer:**

The JWT signing secret should not be hardcoded in source code.

If the secret becomes public, an attacker could potentially create forged tokens.

Therefore secrets are stored in environment configuration such as:

```text
.env
```

and should not be committed to Git.

---

# Category 5: Pydantic

## Q21. What is `Field()` in Pydantic?

**Answer:**

`Field()` allows us to define additional validation rules and metadata.

For example:

```python
name: str = Field(min_length=2)
```

It can also be used for descriptions and API documentation.

---

## Q22. What is `EmailStr`?

**Answer:**

`EmailStr` is a Pydantic type used to validate email-format input.

For example:

```python
email: EmailStr
```

This prevents obviously invalid email values from passing request validation.

---

## Q23. What does `ConfigDict(from_attributes=True)` do?

**Answer:**

It allows Pydantic to create a response model from object attributes.

This is useful when returning SQLAlchemy ORM objects.

For example:

```text
SQLAlchemy object
       ↓
Pydantic response model
       ↓
JSON
```

---

## Q24. What is the difference between `model_dump()` and `model_dump_json()`?

**Answer:**

`model_dump()` returns a Python dictionary.

```python
data = model.model_dump()
```

`model_dump_json()` returns JSON-formatted data.

```python
data = model.model_dump_json()
```

---

## Q25. How can you create custom validation in Pydantic?

**Answer:**

Pydantic provides validators such as:

```python
@field_validator
```

This can be used when normal type validation is not enough.

For example, we could validate a custom URL or field format.

---

# Category 6: SQLAlchemy & ORM

## Q26. What is an ORM?

**Answer:**

ORM stands for Object Relational Mapping.

It allows database tables to be represented as Python classes.

For example:

```text
Company class
      ↓
companies table
```

Instead of writing every SQL statement manually, SQLAlchemy provides Python-based database operations.

---

## Q27. What is a primary key?

**Answer:**

A primary key uniquely identifies a record in a table.

Example:

```text
users
----------------
id
email
password
```

`id` can be the primary key.

---

## Q28. What is a foreign key?

**Answer:**

A foreign key connects one table to another.

For example:

```text
jobs.company_id
        ↓
companies.id
```

This establishes a relationship between jobs and companies.

---

## Q29. What does `relationship()` do in SQLAlchemy?

**Answer:**

`relationship()` defines an ORM-level relationship between models.

For example:

```text
Company
   ↓
Jobs
```

A company can have multiple jobs.

This allows the relationship to be accessed naturally through SQLAlchemy models.

---

## Q30. What is cascading in SQLAlchemy?

**Answer:**

Cascading controls what happens to related records when a parent record is changed or deleted.

For example, if a company is deleted, related records may also be deleted depending on the configured relationship and database constraints.

### Interview tip

Only mention the exact cascade configuration that is actually present in your code.

---

# Category 7: MySQL & Database Design

## Q31. Why did you use MySQL?

**Answer:**

I used MySQL because JobShield contains structured relational data such as users, companies, jobs, recruiters, reports, and verification results.

MySQL provides:

* Relational tables
* Primary and foreign keys
* Constraints
* Indexing
* Transactions
* ACID properties

It is a good fit for this type of application.

---

## Q32. What is a database index?

**Answer:**

An index helps the database find records more efficiently.

For example, if we frequently search users by email:

```text
users.email
```

an index can improve that lookup.

However, indexes also require additional storage and can add overhead to insert/update operations, so they should be used where they provide value.

---

## Q33. What is database migration?

**Answer:**

A migration is a controlled way of changing the database structure over time.

For example:

```text
Version 1
users(id, email)

       ↓ migration

Version 2
users(id, email, created_at)
```

A migration system such as Alembic can track these changes.

### Important for JobShield

The application currently creates database tables through SQLAlchemy at startup. If Alembic migrations are added later, they should be used as the controlled schema-change mechanism.

---

## Q34. What are `schema.sql` and `seed.sql`?

**Answer:**

If included in the project:

`schema.sql` contains SQL statements for creating database structures.

`seed.sql` contains sample or initial data.

They are useful for manual database setup and development.

---

## Q35. What is the difference between CHAR and VARCHAR?

**Answer:**

`CHAR` stores fixed-length strings.

`VARCHAR` stores variable-length strings up to a defined limit.

For example, names and email addresses are generally suitable for variable-length string fields.

---

# Category 8: Verification & Risk Engine

## Q36. Why is JobShield a risk assessment tool instead of a binary fraud detector?

**Answer:**

Because the system works with available evidence and predefined signals.

A website may be unavailable, a company may have limited online information, or a recruiter may use a legitimate third-party email service.

Therefore, the system reports detected signals and a risk level instead of claiming:

```text
"This company is definitely fake."
```

### Interview answer

> "I designed it as a risk assessment system because the available information may be incomplete. The goal is to provide evidence and warning signals rather than make an absolute claim."

---

## Q37. How is the final risk score calculated?

**Answer:**

The RiskEngine receives structured signals.

Each signal can have a predefined score impact.

For example:

```text
Payment Request     +30
Registration Fee    +25
Domain Mismatch     +15
Urgency             +10
```

The engine combines the applicable weights and keeps the final score within the defined range of 0–100.

It then maps the score to a risk level.

---

## Q38. How does EmailAnalyzer detect a domain mismatch?

**Answer:**

It compares available company/domain information with the sender's email domain.

For example:

```text
Company website:
example.com

Recruiter:
hr@example.com
```

These domains align.

But:

```text
Company website:
example.com

Recruiter:
example@gmail.com
```

would be treated differently because Gmail is a free email provider.

This is only one signal and does not by itself prove fraud.

---

## Q39. What types of signals can receive high severity?

**Answer:**

Examples include:

* Upfront payment requests
* Registration fees
* Paid training requirements
* Equipment/security deposits

These signals can have higher weights because they are directly relevant to common job-scam patterns.

---

## Q40. Why are free email providers flagged?

**Answer:**

A recruiter using a free email address can be a warning signal because it does not match the company's official domain.

For example:

```text
hr@company.com
```

is different from:

```text
company.hr@gmail.com
```

However, a free email address alone does not prove that an opportunity is fraudulent.

It is treated as one signal among several.

---

# Category 9: HTTP Requests & Webpage Analysis

## Q41. How does JobAnalyzer handle an unreachable webpage?

**Answer:**

The application makes an HTTP request with a timeout.

If the webpage cannot be reached or the request fails, the application catches the error and records the limitation instead of allowing the entire API request to crash.

### Important point

A failed webpage request means:

> "The page could not be checked."

It should not automatically mean:

> "The job is fraudulent."

---

## Q42. Why use HTTPX?

**Answer:**

HTTPX supports both synchronous and asynchronous HTTP requests.

This fits well with FastAPI applications when the application needs to make network requests to external webpages.

---

## Q43. What does BeautifulSoup do?

**Answer:**

BeautifulSoup is an HTML parsing library.

It can help extract information such as:

```text
<title>
meta tags
Open Graph metadata
visible page text
links
```

### In JobShield

It can help JobAnalyzer inspect the HTML content available from a job webpage.

---

## Q44. What does URLAnalyzer check?

**Answer:**

URLAnalyzer can check basic URL characteristics such as:

* URL format
* HTTP vs HTTPS
* Domain information
* Suspicious URL patterns
* Whether the URL contains an IP address
* Other predefined URL rules

The result becomes input for the verification and risk calculation process.

---

## Q45. What happens if an external webpage cannot be checked?

**Answer:**

The verification process should handle the failure gracefully.

For example:

```text
Website unavailable
        ↓
Record limitation
        ↓
Continue with available information
        ↓
Return result with appropriate status
```

The system should not invent information about a webpage it could not access.

---

# Category 10: Testing & Quality

## Q46. Why use Pytest?

**Answer:**

Pytest allows us to automatically test application behavior.

Instead of manually checking every endpoint after every code change, automated tests can verify important functionality repeatedly.

---

## Q47. What would you test in JobShield?

**Answer:**

I would test:

```text
Authentication
Registration
Login
Company APIs
Job APIs
Verification APIs
Risk calculation
Signal detection
Reports
Validation errors
```

---

## Q48. How would you test an API endpoint?

**Answer:**

FastAPI provides a `TestClient` that allows tests to call endpoints similarly to a real client.

For example:

```python
response = client.get("/api/v1/companies")
```

We can then check:

```python
assert response.status_code == 200
```

and verify the response body.

---

## Q49. Why should external HTTP calls be mocked in tests?

**Answer:**

Tests should not depend on an external website being available.

If the test directly calls a real website, it can fail because of:

* Network problems
* Website downtime
* Rate limits
* Website changes

Mocking makes tests faster and more predictable.

---

## Q50. What is the purpose of testing the RiskEngine separately?

**Answer:**

The RiskEngine contains important business rules.

For example:

```text
Payment Request → +30
Domain Mismatch → +15
```

Testing it separately allows us to verify that the score is calculated correctly for different combinations of signals.

---

# Category 11: Docker & DevOps

## Q51. Explain the multi-container setup.

**Answer:**

JobShield can run using three containers:

```text
1. jobshield_frontend
   → Streamlit

2. jobshield_backend
   → FastAPI

3. jobshield_mysql
   → MySQL
```

The communication is:

```text
Streamlit
    ↓ HTTP
FastAPI
    ↓ SQLAlchemy / PyMySQL
MySQL
```

---

## Q52. How does `depends_on` with `service_healthy` work?

**Answer:**

Docker Compose can define a health check for MySQL.

The backend can depend on the MySQL service being healthy before starting.

The basic idea is:

```text
Start MySQL
    ↓
MySQL health check
    ↓
Healthy
    ↓
Start backend
```

This reduces startup problems where the backend tries to connect before MySQL is ready.

---

# 🧠 Most Important Questions to Prepare First

If you have limited interview preparation time, focus on these first:

```text
1. Explain your project
2. Explain the architecture
3. Why FastAPI?
4. What is REST API?
5. GET vs POST vs PUT vs PATCH
6. What is JWT?
7. How does JWT authentication work?
8. What is Depends()?
9. What is Pydantic?
10. Why MySQL?
11. What is SQLAlchemy?
12. Primary key vs foreign key
13. Explain your database tables
14. How does email verification work?
15. How does job verification work?
16. How is the risk score calculated?
17. Why rule-based instead of AI?
18. What is HTTPX?
19. What is BeautifulSoup?
20. How did you test the project?
21. Why Docker?
22. What are the limitations of the project?
```

---

# 🧩 One-Shot Memory Map

Remember JobShield in this order:

```text
USER
 ↓
STREAMLIT
 ↓
REST API
 ↓
FASTAPI
 ↓
PYDANTIC
 ↓
JWT AUTH
 ↓
SERVICE
 ↓
ANALYZER
 ↓
SIGNAL DETECTOR
 ↓
RISK ENGINE
 ↓
SQLALCHEMY
 ↓
MYSQL
```

### Each layer in one word

```text
Streamlit    → UI
FastAPI      → API
Pydantic     → Validation
JWT          → Authentication
Service      → Logic
Analyzer     → Checking
Signal       → Evidence
RiskEngine   → Score
SQLAlchemy   → Database access
MySQL        → Storage
Docker       → Deployment
Pytest       → Testing
```

---

# 🎯 Final Project Explanation

If the interviewer says:

> **"Explain your JobShield project."**

Use this:

> "JobShield is a Python-based job and company verification platform that I built using FastAPI, REST APIs, MySQL, and Streamlit. The purpose is to help users assess suspicious job offers, recruiter emails, and job URLs.
>
> The user submits information through the REST API. FastAPI receives the request and Pydantic validates it. After authentication, the service layer sends the information to the appropriate analyzer. The analyzers check things such as email domains, payment requests, suspicious links, urgency, URL characteristics, and available company or job information.
>
> The SignalDetector converts these findings into structured risk signals. The RiskEngine then applies predefined weights and calculates a score between 0 and 100 along with a risk level. The verification result and signals are stored in MySQL using SQLAlchemy.
>
> I used JWT for authentication, HTTPX for HTTP requests, BeautifulSoup for webpage parsing, Pytest for testing, and Docker for deployment. The Streamlit frontend communicates with the FastAPI backend through REST APIs rather than directly accessing the database."

---

# ⚠️ Project Limitations

If asked about limitations, give an honest answer:

> "The main limitation is that verification depends on the information available from the submitted website, email, or company. Some websites may block automated requests, require JavaScript, or provide limited information. Also, the risk score is a rule-based assessment and has not been statistically validated as a probability of fraud. Therefore, the system provides warning signals and supporting evidence rather than guaranteeing whether a job or company is genuine."

---

# 🚫 Technologies You Should NOT Claim

For the current version of JobShield, do not say that you used:

```text
LLM
Generative AI
Machine Learning
NLP models
Embeddings
Vector databases
RAG
LangChain
LangGraph
AI agents
MCP
Fraud prediction model
AI fraud detection
```

The project is easier and more believable to explain as:

```text
Python
   ↓
FastAPI
   ↓
REST API
   ↓
Pydantic
   ↓
JWT
   ↓
Rule-Based Verification
   ↓
Risk Engine
   ↓
SQLAlchemy
   ↓
MySQL
```

That is the technical story you should consistently use throughout your resume, README, architecture document, interview answers, and project explanation.
