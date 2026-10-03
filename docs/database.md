# 🗄️ JobShield — Database Architecture & Concepts Guide

Comprehensive guide to the relational database design, Entity-Relationship (ER) structure, indexes, cascading rules, and SQLAlchemy ORM models used in **JobShield**.

---

## 📌 Relational Database Concepts Quick Reference

1. **Primary Key (PK)**: A unique identifier attribute for each row in a database table (e.g., `users.id`, `companies.id`).
2. **Foreign Key (FK)**: An attribute that establishes a link to the Primary Key of another table, maintaining referential integrity (e.g., `jobs.company_id` referencing `companies.id`).
3. **One-to-Many Relationship**: A database relationship where a single record in Table A relates to multiple records in Table B.
   - Example: **1 Company** has **Many Jobs** (`companies.id` -> `jobs.company_id`).
   - Example: **1 User** submits **Many Verification Results** (`users.id` -> `verification_results.user_id`).
   - Example: **1 Verification Result** contains **Many Verification Signals** (`verification_results.id` -> `verification_signals.verification_id`).
4. **Unique Constraint**: Ensures that all values in a specified column are distinct across the table.
   - Example: `users.email` is defined as `UNIQUE` to prevent multiple accounts registered with the same email.
5. **Database Index**: A performance data structure (B-Tree in MySQL) that accelerates row lookups from $O(N)$ full table scans to $O(\log N)$ logarithmic searches.
   - Example: Indexes on `companies.name`, `companies.domain`, `jobs.title`, `recruiters.email_domain`.
6. **SQL JOIN**: An operation combining rows from two or more tables based on a related column.
   - Example: Joining `jobs` and `companies` tables on `jobs.company_id = companies.id`.
7. **ORM (Object-Relational Mapping)**: A programming technique that maps relational database tables into Python classes (SQLAlchemy models), allowing database interactions using Python code instead of raw SQL strings.
8. **Alembic Database Migration**: A tool that tracks schema modifications over time and applies SQL DDL scripts cleanly.

---

## 📐 Entity Relationship (ER) Diagram

```
+----------------+          +-------------------+          +-----------------+
|     USERS      | 1      * | VERIFICATION_RES  | 1      * | VERIF_SIGNALS   |
+----------------+----------+-------------------+----------+-----------------+
| id (PK)        |          | id (PK)           |          | id (PK)         |
| name           |          | user_id (FK)      |          | verif_id (FK)   |
| email (UQ,IDX) |          | company_id (FK)   |          | signal_type     |
| hashed_pass    |          | job_id (FK)       |          | severity        |
| is_active      |          | risk_score        |          | title           |
| created_at     |          | risk_level        |          | evidence        |
+----------------+          +-------------------+          +-----------------+
        | 1                          | *
        |                            |
        | *                          |
+----------------+                   |
|    REPORTS     |                   |
+----------------+                   |
| id (PK)        |                   |
| user_id (FK)   |                   |
| company_id(FK) |                   |
| status         |                   |
+----------------+                   |
                                     |
+----------------+ 1               * |
|   COMPANIES    |-------------------+
+----------------+
| id (PK)        |
| name (IDX)     | 1               * +-----------------+
| domain (IDX)   |-------------------|      JOBS       |
| verified_dom   |                   +-----------------+
+----------------+                   | id (PK)         |
        | 1                          | company_id (FK) |
        |                            | title (IDX)     |
        | *                          +-----------------+
+----------------+
|   RECRUITERS   |
+----------------+
| id (PK)        |
| company_id (FK)|
| email_domain   |
+----------------+
```

---

## 🗃️ Tables & SQLAlchemy Models Breakdown

### 1. `users` Model (`app/models/user.py`)
- `id` (INTEGER, PK, Autoincrement)
- `name` (VARCHAR(100), NOT NULL)
- `email` (VARCHAR(255), UNIQUE, INDEX, NOT NULL)
- `hashed_password` (VARCHAR(255), NOT NULL)
- `is_active` (BOOLEAN, DEFAULT TRUE)
- `created_at`, `updated_at` (DATETIME)
- **Relationships**: `verifications` (cascade delete), `reports` (cascade delete)

---

### 2. `companies` Model (`app/models/company.py`)
- `id` (INTEGER, PK)
- `name` (VARCHAR(150), INDEX, NOT NULL)
- `website` (VARCHAR(255), NULLABLE)
- `domain` (VARCHAR(150), INDEX, NULLABLE)
- `description` (TEXT, NULLABLE)
- `careers_url` (VARCHAR(255), NULLABLE)
- `verified_domain` (BOOLEAN, DEFAULT FALSE)
- `created_at`, `updated_at` (DATETIME)
- **Relationships**: `jobs` (cascade delete), `recruiters` (cascade delete), `verifications`, `reports`

---

### 3. `jobs` Model (`app/models/job.py`)
- `id` (INTEGER, PK)
- `company_id` (INTEGER, FK -> `companies.id`, INDEX, NOT NULL)
- `title` (VARCHAR(200), INDEX, NOT NULL)
- `description` (TEXT, NULLABLE)
- `location` (VARCHAR(150), NULLABLE)
- `job_url` (VARCHAR(500), NULLABLE)
- `salary_text` (VARCHAR(150), NULLABLE)
- `source` (VARCHAR(100), NULLABLE)
- `created_at`, `updated_at` (DATETIME)
- **Relationships**: `company`, `verifications`, `reports`

---

### 4. `recruiters` Model (`app/models/recruiter.py`)
- `id` (INTEGER, PK)
- `company_id` (INTEGER, FK -> `companies.id`, INDEX, NOT NULL)
- `name` (VARCHAR(150), NOT NULL)
- `email` (VARCHAR(255), INDEX, NOT NULL)
- `email_domain` (VARCHAR(150), INDEX, NOT NULL)
- `created_at` (DATETIME)
- **Relationships**: `company`

---

### 5. `verification_results` Model (`app/models/verification.py`)
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK -> `users.id`, INDEX, NOT NULL)
- `company_id` (INTEGER, FK -> `companies.id`, NULLABLE)
- `job_id` (INTEGER, FK -> `jobs.id`, NULLABLE)
- `verification_type` (VARCHAR(50), NOT NULL)  -- 'email', 'job', 'company'
- `risk_score` (INTEGER, DEFAULT 0)
- `risk_level` (VARCHAR(50), DEFAULT 'LOW')
- `verification_status` (VARCHAR(50), DEFAULT 'INCONCLUSIVE')
- `summary` (TEXT, NULLABLE)
- `created_at` (DATETIME)
- **Relationships**: `user`, `company`, `job`, `signals` (cascade delete)

---

### 6. `verification_signals` Model (`app/models/verification_signal.py`)
- `id` (INTEGER, PK)
- `verification_id` (INTEGER, FK -> `verification_results.id`, INDEX, NOT NULL)
- `signal_type` (VARCHAR(100), NOT NULL)
- `severity` (VARCHAR(50), NOT NULL)
- `title` (VARCHAR(200), NOT NULL)
- `description` (TEXT, NULLABLE)
- `evidence` (TEXT, NULLABLE)
- `score_impact` (INTEGER, DEFAULT 0)
- `created_at` (DATETIME)
- **Relationships**: `verification`

---

### 7. `reports` Model (`app/models/report.py`)
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK -> `users.id`, INDEX, NOT NULL)
- `company_id` (INTEGER, FK -> `companies.id`, NULLABLE)
- `job_id` (INTEGER, FK -> `jobs.id`, NULLABLE)
- `report_type` (VARCHAR(100), NOT NULL)
- `description` (TEXT, NOT NULL)
- `status` (VARCHAR(50), DEFAULT 'PENDING')
- `created_at` (DATETIME)
- **Relationships**: `user`, `company`, `job`
