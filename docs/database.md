# 🗄️ JobShield — Database Architecture & Concepts Guide

Comprehensive guide to the relational database design, Entity-Relationship (ER) structure, indexes, cascading rules, and the tables defined in `sql/schema.sql` for **JobShield**.

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
7. **Parameterized Query**: A SQL statement with `%s` placeholders where values go (e.g. `SELECT * FROM users WHERE email = %s`). The driver sends the values separately from the SQL text, so user input can never change the meaning of the query. This is what prevents SQL injection.
8. **Transaction**: A group of SQL statements that succeed or fail together. JobShield saves a verification result and all its signals, then calls `commit()` once; if something fails in between, `rollback()` undoes it.

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

## 🗃️ Tables Breakdown (`sql/schema.sql`)

### 1. `users` table
- `id` (INTEGER, PK, Autoincrement)
- `name` (VARCHAR(100), NOT NULL)
- `email` (VARCHAR(255), UNIQUE, INDEX, NOT NULL)
- `hashed_password` (VARCHAR(255), NOT NULL)
- `is_active` (BOOLEAN, DEFAULT TRUE)
- `created_at`, `updated_at` (DATETIME)

---

### 2. `companies` table
- `id` (INTEGER, PK)
- `name` (VARCHAR(150), INDEX, NOT NULL)
- `website` (VARCHAR(255), NULLABLE)
- `domain` (VARCHAR(150), INDEX, NULLABLE)
- `description` (TEXT, NULLABLE)
- `careers_url` (VARCHAR(255), NULLABLE)
- `verified_domain` (BOOLEAN, DEFAULT FALSE)
- `created_at`, `updated_at` (DATETIME)

---

### 3. `jobs` table
- `id` (INTEGER, PK)
- `company_id` (INTEGER, FK -> `companies.id`, INDEX, NOT NULL)
- `title` (VARCHAR(200), INDEX, NOT NULL)
- `description` (TEXT, NULLABLE)
- `location` (VARCHAR(150), NULLABLE)
- `job_url` (VARCHAR(500), NULLABLE)
- `salary_text` (VARCHAR(150), NULLABLE)
- `source` (VARCHAR(100), NULLABLE)
- `created_at`, `updated_at` (DATETIME)

---

### 4. `recruiters` table
- `id` (INTEGER, PK)
- `company_id` (INTEGER, FK -> `companies.id`, INDEX, NOT NULL)
- `name` (VARCHAR(150), NOT NULL)
- `email` (VARCHAR(255), INDEX, NOT NULL)
- `email_domain` (VARCHAR(150), INDEX, NOT NULL)
- `created_at` (DATETIME)

---

### 5. `verification_results` table
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

---

### 6. `verification_signals` table
- `id` (INTEGER, PK)
- `verification_id` (INTEGER, FK -> `verification_results.id`, INDEX, NOT NULL)
- `signal_type` (VARCHAR(100), NOT NULL)
- `severity` (VARCHAR(50), NOT NULL)
- `title` (VARCHAR(200), NOT NULL)
- `description` (TEXT, NULLABLE)
- `evidence` (TEXT, NULLABLE)
- `score_impact` (INTEGER, DEFAULT 0)
- `created_at` (DATETIME)

---

### 7. `reports` table
- `id` (INTEGER, PK)
- `user_id` (INTEGER, FK -> `users.id`, INDEX, NOT NULL)
- `company_id` (INTEGER, FK -> `companies.id`, NULLABLE)
- `job_id` (INTEGER, FK -> `jobs.id`, NULLABLE)
- `report_type` (VARCHAR(100), NOT NULL)
- `description` (TEXT, NOT NULL)
- `status` (VARCHAR(50), DEFAULT 'PENDING')
- `created_at` (DATETIME)

---

## 🔗 Delete Rules (defined in `sql/schema.sql`)

| When this is deleted... | ...this happens | Why |
| :--- | :--- | :--- |
| a **user** | their verification results and reports are deleted (`ON DELETE CASCADE`) | data belongs to the user |
| a **company** | its jobs and recruiters are deleted (`CASCADE`) | they cannot exist without the company |
| a **company** | `company_id` in verification results and reports becomes `NULL` (`SET NULL`) | keep the history even if the company record is removed |
| a **job** | `job_id` in verification results and reports becomes `NULL` (`SET NULL`) | same reason |
| a **verification result** | its signals are deleted (`CASCADE`) | signals belong to one result |

The application code does not delete child rows by hand — MySQL does it because of these foreign-key rules.

---

## Part B tables (`sql/analytics_schema.sql`)

Kept in a separate file so re-running `schema.sql` never deletes a loaded dataset.

### 8. `job_postings`
One row per posting from the labelled dataset. Holds the cleaned columns (country/state/city split out, salary parsed to `salary_min`/`salary_max`, yes/no columns as 0/1), the known label `fraudulent`, and the rule engine's `risk_score` and `risk_level`. `UNIQUE (dataset_name, source_job_id)` prevents loading the same posting twice. Indexes on `fraudulent`, `employment_type`, `industry`, `country`, `risk_score` support the group-by queries.

### 9. `posting_signals`
One row per rule that fired on a posting (`signal_type`, `severity`, `score_impact`). `posting_id` is a foreign key to `job_postings` with `ON DELETE CASCADE`, so emptying postings removes their signals. This table lets SQL measure each rule on its own (precision, coverage, lift).

The loader empties both tables before each load, so they always hold one dataset.
