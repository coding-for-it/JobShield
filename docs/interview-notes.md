# 🎓 JobShield — Interview Master Guide & 50 Technical Q&As

This document contains interview cheat sheets, system explanations, and **50 structured interview questions & answers** tailored to explain **JobShield** in technical interviews for Python, Backend, API, Data, and Software Engineering roles.

---

## ⏱️ Elevator Summaries

### 30-Second Pitch
> "I built JobShield, an API-first Job and Company Verification Platform using Python, FastAPI, MySQL, and Streamlit. JobShield analyzes suspicious job offers, recruiter emails, and job URLs to detect scam indicators like payment demands, domain mismatches, and free recruiter emails. It uses a simple rule-based engine to generate a risk score from 0 to 100 and explains exactly which signals caused that score."

### 1-Minute Pitch
> "JobShield is a RESTful backend platform built with FastAPI and MySQL 8, using plain SQL through the PyMySQL driver. It addresses the growing problem of job placement scams by evaluating recruitment offers against evidence-based signals. The architecture separates authentication via JWT and bcrypt password hashing, Pydantic request validation, a modular service layer, and a deterministic risk scoring engine. It also features a web scraper using `httpx` and `BeautifulSoup4` to inspect job listing URLs. The frontend is built in Streamlit, which communicates exclusively with the backend via HTTP REST endpoints. The project has 57 automated pytest tests and can run with Docker Compose."

### 2-Minute Technical Deep Dive
> "Architecturally, JobShield is designed as an API-first monolith adhering to clean layered principles. The entry point is a FastAPI application enforcing JWT bearer authentication through FastAPI's `Depends(get_current_user)` dependency injection mechanism. 
> Request bodies and path parameters are validated by Pydantic v2 schemas. Database access uses plain parameterized SQL through PyMySQL: each request gets one MySQL connection, services run the queries, and I commit explicitly so multi-step saves are one transaction. 
> The core business logic resides in the verification engine. When an email or job URL is submitted, dedicated analyzers (`EmailAnalyzer`, `JobAnalyzer`, `URLAnalyzer`, `CompanyAnalyzer`) extract domain properties and text triggers. `SignalDetector` compiles signals with severity and score impacts, which `RiskEngine` calculates into a clamped 0-100 risk score and risk level (`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`). 
> To demonstrate strict client-server decoupling, the Streamlit UI interacts with FastAPI strictly through HTTP REST calls via an `APIClient`. The backend has 57 pytest test cases that run against a separate `jobshield_test` MySQL database, and it can be started with Docker Compose."

---

## 🏗️ Deep-Dive System Architecture & Concepts

### 1. JWT Authentication Flow
1. **User Registration**: Client posts email/password to `/api/v1/auth/register`. Password is hashed with `bcrypt.hashpw()`.
2. **User Login**: Client posts credentials to `/api/v1/auth/login`. Server verifies email & hash, then signs a JWT containing `sub` (user_id), `exp` (expiration), and `iat` (issued at timestamp) using `HS256` secret.
3. **Protected API Access**: Client sends `Authorization: Bearer <jwt_token>` header.
4. **Dependency Resolution**: `Depends(get_current_user)` extracts header, decodes JWT, queries database for active user, and injects `current_user` into route functions.

### 2. FastAPI `Depends()` Explanation
`Depends()` is FastAPI's Dependency Injection system. It allows reusable logic—such as the database connection (`get_db`) or security checks (`get_current_user`)—to be injected into endpoints automatically. This avoids duplicated code, ensures proper cleanup (e.g., closing the DB connection in a `finally` block), and simplifies testing via dependency overrides (`app.dependency_overrides`).

### 3. Pydantic v2 Schema Validation
Pydantic guarantees input data parsing and type safety at runtime. Request schemas enforce email formatting (`EmailStr`), string lengths, and constraints. Response schemas (`response_model`) take the row dictionary from MySQL and return only the fields declared in the schema, which strips sensitive fields like `hashed_password`.

### 4. Why a Rule-Based Risk Engine
- **Risk Engine (`risk_engine.py`)**: Adds up weighted signals (e.g., Payment Request = +30, Registration Fee = +25, Domain Mismatch = +15) and clamps the total to 0-100.
- **Why rules and not AI**: Every score is explainable (the user sees each signal and its evidence), reproducible (same input = same score), free to run, and easy to test. For a fraud-warning tool, being able to *explain* a result matters more than being clever.
- **Honest limitation**: The weights are my own heuristics, not trained on real fraud data. A next step would be to tune them using real reported cases from the `reports` table.

---

## ❓ 50 Interview Questions & Answers

### Category 1: Python Core & Advanced

#### Q1. What is the difference between synchronous and asynchronous functions in Python?
- **Answer**: Synchronous functions execute sequentially and block the main thread during I/O. Asynchronous functions (`async def`) use an event loop and non-blocking I/O (`await`), allowing Python to perform other tasks while waiting for HTTP requests or DB queries.
- **In JobShield**: We used `async def` in verification routes and `httpx.AsyncClient` for web scraping/external API calls so the application remains responsive during HTTP network operations.
- **Follow-up**: *When should you NOT use async in Python?* (When performing heavy CPU-bound computations, as async does not provide multithreading for CPU tasks).

#### Q2. How does `bcrypt` password hashing work, and why not use MD5 or SHA256?
- **Answer**: MD5 and SHA256 are fast cryptographic hashes prone to rainbow table attacks. `bcrypt` is a slow, adaptive hashing algorithm that incorporates a random salt and a configurable work factor, making brute-force cracking computationally expensive.
- **In JobShield**: We hashed passwords in `app/core/security.py` using `bcrypt.hashpw()` before saving them to MySQL.
- **Follow-up**: *What is a salt in password hashing?* (Random data appended to input password before hashing to prevent identical passwords from producing identical hashes).

#### Q3. Explain Python type hints and Pydantic validation.
- **Answer**: Type hints provide static type annotations. Pydantic enforces type hints at runtime, performing data conversion, validation, and raising descriptive `ValidationError` exceptions on invalid inputs.
- **In JobShield**: All route payloads use Pydantic models (e.g., `UserCreate`, `JobCreate`) to validate incoming JSON automatically.
- **Follow-up**: *What is the difference between Pydantic v1 and v2?* (Pydantic v2 is rewritten in Rust (`pydantic-core`), is up to 20x faster, and uses `ConfigDict` instead of `class Config`).

#### Q4. What are Python context managers and how does the `with` statement work?
- **Answer**: Context managers implement `__enter__` and `__exit__` methods (or use `@contextmanager` generators) to manage resources cleanly.
- **In JobShield**: Used `with TestClient(app)` in pytest and `async with httpx.AsyncClient()` for safe resource disposal.
- **Follow-up**: *How does `yield` work in a FastAPI dependency?* (Code before `yield` runs before endpoint execution; code after `yield` runs after response is sent for cleanup).

#### Q5. What is the difference between `list`, `tuple`, `set`, and `dict` in Python?
- **Answer**: `list` is ordered/mutable; `tuple` is ordered/immutable; `set` is unordered/unique; `dict` stores key-value pairs with $O(1)$ average lookup time.
- **In JobShield**: Used `set` in `EmailAnalyzer.FREE_EMAIL_DOMAINS` for $O(1)$ domain checks.

---

### Category 2: FastAPI Framework

#### Q6. What makes FastAPI faster than Django or Flask?
- **Answer**: FastAPI is built on Starlette (ASGI web framework) and Pydantic. ASGI supports native async I/O out of the box, offering higher throughput than WSGI frameworks.
- **In JobShield**: We built our entire REST API layer using FastAPI with high-performance OpenAPI schema generation.

#### Q7. How does FastAPI automatically generate OpenAPI/Swagger documentation?
- **Answer**: FastAPI inspects route parameter type hints and Pydantic schemas, translating them into OpenAPI 3.0 JSON specifications available at `/docs` and `/redoc`.

#### Q8. What is the role of `APIRouter` in FastAPI?
- **Answer**: `APIRouter` allows modularizing endpoints into separate files/packages, grouping related routes with common prefixes and tags.
- **In JobShield**: Created dedicated routers in `app/api/routes/` (`auth.py`, `companies.py`, `jobs.py`, `verification.py`) combined in `app/api/router.py`.

#### Q9. How do exception handlers work in FastAPI?
- **Answer**: Exception handlers capture specific exceptions thrown anywhere in the application and return custom formatted JSON responses.
- **In JobShield**: Implemented `CustomAPIException` in `app/core/exceptions.py` returning standard `{"success": false, "error": {"code": ..., "message": ...}}` JSON.

#### Q10. What are FastAPI path parameters vs. query parameters vs. request bodies?
- **Answer**: Path parameters are part of the URL path (`/jobs/{id}`); Query parameters follow `?` (`/jobs?page=1`); Request bodies are JSON payloads sent in HTTP POST/PATCH requests.

---

### Category 3: REST API Principles

#### Q11. What are the key constraints of a RESTful API?
- **Answer**: Statelessness, Client-Server separation, Uniform Interface, Cacheability, Layered System, and Code-on-Demand (optional).
- **In JobShield**: Implemented stateless JWT tokens; client (Streamlit) interacts with server strictly through HTTP REST endpoints.

#### Q12. When should you use `PUT` vs `PATCH` HTTP methods?
- **Answer**: `PUT` replaces the entire target resource; `PATCH` applies partial modifications to specific fields.
- **In JobShield**: Used `PATCH /api/v1/companies/{id}` to update specific fields without overwriting unmodified columns.

#### Q13. Explain common HTTP status codes used in JobShield.
- **200 OK**: Successful GET/POST operation.
- **201 Created**: Resource created successfully.
- **204 No Content**: Successful deletion without response body.
- **401 Unauthorized**: Missing or invalid JWT token.
- **403 Forbidden**: Inactive account or unauthorized action.
- **404 Not Found**: Requested entity does not exist.
- **409 Conflict**: Duplicate registration email.
- **422 Validation Error**: Pydantic input validation failure.

#### Q14. How does API pagination improve backend scalability?
- **Answer**: Returning large datasets in a single response causes high memory usage and slow response times. Pagination limits DB query sizes using `LIMIT` and `OFFSET`.
- **In JobShield**: List endpoints take `page` and `limit`; the SQL uses `LIMIT %s OFFSET %s`, and a generic `PaginatedResponse[T]` in `app/utils/pagination.py` adds total/total_pages.

#### Q15. Why should passwords never be returned in API response models?
- **Answer**: Returning password hashes exposes sensitive data to network sniffing, client-side logging, or XSS vulnerabilities. In `UserResponse`, `hashed_password` is excluded.

---

### Category 4: JWT & Authentication

#### Q16. What is JSON Web Token (JWT) structure?
- **Answer**: A JWT consists of three dot-separated Base64Url parts: `Header.Payload.Signature`.
- **Header**: Algorithm & token type.
- **Payload**: Claims (`sub`, `exp`, `iat`).
- **Signature**: HMAC SHA256 of header + payload signed with secret key.

#### Q17. What is the difference between stateful session auth and stateless JWT auth?
- **Answer**: Stateful sessions store session IDs in server memory/database. Stateless JWTs store user identity inside the token signed by the server, allowing horizontally scalable server verification without database sessions.

#### Q18. How does `OAuth2PasswordBearer` work in FastAPI?
- **Answer**: It extracts the Bearer token string from the `Authorization: Bearer <token>` HTTP header.

#### Q19. How do you revoke or invalidate a JWT before expiration?
- **Answer**: Since JWTs are stateless, instant revocation requires a token blacklist in Redis or maintaining token version counters in the database.

#### Q20. Why must `JWT_SECRET_KEY` be stored in `.env` environment variables?
- **Answer**: Hardcoding secrets in source control exposes signatures to unauthorized parties, allowing token forgery.

---

### Category 5: Pydantic Data Validation

#### Q21. What is `Field()` in Pydantic v2?
- **Answer**: `Field()` defines field-level metadata, constraints (e.g., `min_length`, `ge`), descriptions, and OpenAPI example values.

#### Q22. How does `EmailStr` validate email format?
- **Answer**: It uses `email-validator` library to parse email syntax, domain format, and ASCII normalization.

#### Q23. How does a MySQL row become the JSON the client receives?
- **Answer**: PyMySQL returns each row as a Python dictionary. FastAPI validates it against the route's `response_model` (a Pydantic class), keeps only the declared fields, and converts types such as `datetime` to JSON.
- **In JobShield**: `UserResponse` has no `hashed_password` field, so the password hash is never sent even though the row contains it.

#### Q24. What is the difference between `model_dump()` and `model_dump_json()`?
- **Answer**: `model_dump()` converts a Pydantic model into a Python dictionary; `model_dump_json()` serializes it directly to a JSON string.

#### Q25. How do you perform custom field validation in Pydantic?
- **Answer**: Using the `@field_validator` decorator.

---

### Category 6: Database Access with Plain SQL (PyMySQL)

#### Q26. Why did you use plain SQL instead of an ORM?
- **Answer**: The project has 7 tables and simple queries, so plain SQL keeps it easy to read and shows I understand SQL directly. Every query is visible in the code, with no hidden behavior. The trade-off: more code to write by hand (no automatic mapping) and no automatic schema migrations.
- **Follow-up**: *When would you choose an ORM?* (Large projects with many tables and relationships, where it saves repetitive code and helps with migrations.)

#### Q27. What is a Primary Key and Foreign Key?
- **Answer**: Primary Key uniquely identifies a record in a table. Foreign Key references the Primary Key of another table, establishing referential integrity.
- **In JobShield**: `jobs.company_id` references `companies.id`, so a job cannot point to a company that does not exist.

#### Q28. How do you prevent SQL injection?
- **Answer**: Never build SQL by joining user text into the string. Use placeholders and pass values separately, so the driver treats them as data, never as SQL.
- **In JobShield**: `fetch_one(db, "SELECT * FROM users WHERE email = %s", (email,))`. Even a search like `' OR 1=1; DROP TABLE users;--` is just treated as text and matches nothing.
- **Follow-up**: *Your `update_row` helper puts column names in the SQL text, is that safe?* (Yes: the column names come from our own Pydantic schema fields, never from the user. Only values come from the user, and those use `%s`.)

#### Q29. How do you handle transactions?
- **Answer**: The connection has `autocommit=False`, so nothing is saved until I call `db.commit()`. If an error happens, `get_db` calls `rollback()` and closes the connection.
- **In JobShield**: A verification inserts one row in `verification_results` and several in `verification_signals`, then commits once, so you never get a result saved with only half of its signals.

#### Q30. What cascading behaviors did you use in JobShield?
- **Answer**: Defined in `sql/schema.sql`: `ON DELETE CASCADE` on `jobs.company_id` so deleting a company removes its jobs and recruiters. `ON DELETE SET NULL` on `verification_results.company_id` so history is kept if a company is deleted.
- **Note**: The Python code does not delete child rows itself; MySQL does it.

#### Q30b. What is the N+1 query problem and did you avoid it?
- **Answer**: Fetching a list, then running one extra query per item (1 + N queries). 
- **In JobShield**: The verification history loads all results, then fetches ALL their signals with a single `WHERE verification_id IN (...)` query and groups them in Python, so it is 2 queries total instead of 1 + N.

---

### Category 7: Database Design & MySQL

#### Q31. Why use MySQL 8.0 for JobShield?
- **Answer**: MySQL 8 is an enterprise relational database offering ACID compliance, foreign key constraints, JSON support, and high performance indexing.

#### Q32. What database indexes were added in JobShield?
- **Answer**: Indexes on `users.email`, `companies.name`, `companies.domain`, `jobs.company_id`, `jobs.title`, `recruiters.email_domain`, and `verification_results.user_id` to optimize filter and lookup queries.

#### Q33. How would you change the database schema later without losing data?
- **Answer**: Write an `ALTER TABLE` script (e.g. `ADD COLUMN`) and run it on the existing database instead of re-running `schema.sql`, which drops tables. In a bigger team I would keep numbered migration scripts or use a migration tool such as Flyway or Alembic.
- **Honest note**: Right now the project has only `schema.sql` (fresh install) and `seed.sql` (sample data).

#### Q34. What is the role of `sql/schema.sql` and `sql/seed.sql`?
- **Answer**: `schema.sql` creates the database and all 7 tables with indexes and foreign keys; `seed.sql` adds a sample user (`user@example.com`), companies, jobs and recruiters for testing. The app itself never creates tables.

#### Q35. What is the difference between `CHAR` and `VARCHAR` in MySQL?
- **Answer**: `CHAR` is fixed-length; `VARCHAR` is variable-length up to specified max characters, saving storage space.

---

### Category 8: Verification & Risk Engine Logic

#### Q36. Why is JobShield designed as a risk assessment tool rather than a binary fraud detector?
- **Answer**: Fraud detection in recruitment relies on incomplete external signals. Binary claims ("100% fake") carry legal risk. Providing evidence-based risk scores empowers candidates with actionable advice.

#### Q37. How is the final risk score calculated in `risk_engine.py`?
- **Answer**: By summing signal impact weights (e.g., Payment Request +30, Registration Fee +25, Domain Mismatch +15), clamping the score between 0 and 100, and assigning a risk level (`LOW`, `MODERATE`, `HIGH`, `VERY_HIGH`).

#### Q38. How does `EmailAnalyzer` detect domain mismatches?
- **Answer**: It extracts base domains from the sender's email and company website using `urlparse` and string parsing, flagging discrepancies.

#### Q39. What signals trigger a `CRITICAL` severity rating?
- **Answer**: Direct upfront monetary payment demands, registration fees, paid training course demands, or equipment security deposits.

#### Q40. Why are free email providers (`@gmail.com`, `@yahoo.com`) flagged?
- **Answer**: Legitimate corporate recruiters send communications from official corporate domain servers.

---

### Category 9: External APIs & Web Scraping

#### Q41. How does `JobAnalyzer` handle unreachable web pages or blocking?
- **Answer**: Uses `httpx.AsyncClient` wrapped in `try...except` blocks with a short timeout (6.0s). If blocked or unreachable, it captures the limitation cleanly without crashing the API.

#### Q42. Why use `httpx` instead of `requests` in FastAPI?
- **Answer**: `requests` is synchronous and blocks the event loop. `httpx` provides async HTTP requests compatible with `asyncio`.

#### Q43. What does `BeautifulSoup4` extract from scraped job pages?
- **Answer**: Title tags, `og:title`, `og:site_name`, meta descriptions, and visible body text.

#### Q44. How does `CompanyAnalyzer` check a company website?
- **Answer**: It requests the website with a 5-second timeout and records whether it is reachable, whether it uses HTTPS, and whether the page mentions careers/jobs. `SignalDetector` then turns that into signals (e.g. `UNREACHABLE_WEBSITE` +10, HTTPS `-10`).

#### Q45. How does the application maintain functionality if an external API fails?
- **Answer**: Every network call is wrapped in `try...except` with a timeout. A failure never crashes the API; it becomes a signal (e.g. `UNREACHABLE_WEBSITE`) or an error note in the result.

---

### Category 10: Design Decisions

#### Q46. Why is the risk score rule-based instead of using machine learning?
- **Answer**: Rules are explainable, reproducible and need no training data. The user sees each signal with its evidence, which builds trust. ML needs a labelled fraud dataset, which this project does not have.
- **Follow-up**: *How would you improve it?* (Collect user reports, label them, tune the weights, and possibly train a model once there is enough data. Keep the rule signals as explainable features.)

#### Q47. Why does the Streamlit app call the API instead of querying MySQL directly?
- **Answer**: It keeps the UI and the logic separate: the same API could serve a mobile app or another client, and the database password never lives in the frontend. All validation and authentication happen in one place (the API).

#### Q48. Why a separate `services/` layer between routes and SQL?
- **Answer**: Routes only handle HTTP (inputs, status codes). Services hold the logic and SQL, so they are easy to read, reuse (e.g. `JobService` reuses `CompanyService.get_company`) and test.

---

### Category 11: Testing & Quality Assurance

#### Q49. How do the tests avoid damaging real data?
- **Answer**: `tests/conftest.py` points the app at a separate database called `jobshield_test`, creates its tables from `sql/schema.sql`, and empties all tables before every test. The tests use FastAPI's `TestClient` and the real MySQL, so SQL mistakes are actually caught.
- **Follow-up**: *Why not SQLite for tests?* (SQL differs between databases; testing on the same engine as production finds real problems.)

#### Q50. What test coverage was achieved in JobShield?
- **Answer**: 57 test cases covering Auth, Companies CRUD, Jobs CRUD, Verification signal calculation, Risk scoring, Reports, the data-cleaning (ETL) functions, the posting rule analyzer, and the analytics endpoints.

---

### Category 12: Docker & DevOps

#### Q51. Explain the multi-container setup in `docker-compose.yml`.
- **Answer**: Defines 3 isolated containers: `jobshield_mysql` (MySQL 8 database), `jobshield_backend` (FastAPI backend), and `jobshield_frontend` (Streamlit UI).

#### Q52. How does `depends_on` with `service_healthy` work in Docker Compose?
- **Answer**: Ensures the backend container waits until MySQL is fully initialized and passing ping healthchecks before launching Uvicorn.
