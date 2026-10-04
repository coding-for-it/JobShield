-- JobShield analytics tables (labelled job-posting dataset used for data analysis)
-- Kept separate from schema.sql so re-running schema.sql never deletes a loaded dataset.
-- Run AFTER schema.sql:  source sql/analytics_schema.sql

USE jobshield;

DROP TABLE IF EXISTS posting_signals;
DROP TABLE IF EXISTS job_postings;

-- 8. Job postings: one row per posting, with the known label (fraudulent) and our rule-engine score
CREATE TABLE job_postings (
    id INT AUTO_INCREMENT PRIMARY KEY,
    source_job_id INT NOT NULL,
    dataset_name VARCHAR(100) NOT NULL,
    title VARCHAR(255) NULL,
    country VARCHAR(50) NULL,
    state VARCHAR(100) NULL,
    city VARCHAR(255) NULL,
    department VARCHAR(255) NULL,
    salary_min INT NULL,
    salary_max INT NULL,
    has_salary BOOLEAN NOT NULL DEFAULT FALSE,
    has_company_profile BOOLEAN NOT NULL DEFAULT FALSE,
    has_requirements BOOLEAN NOT NULL DEFAULT FALSE,
    has_benefits BOOLEAN NOT NULL DEFAULT FALSE,
    telecommuting BOOLEAN NOT NULL DEFAULT FALSE,
    has_company_logo BOOLEAN NOT NULL DEFAULT FALSE,
    has_questions BOOLEAN NOT NULL DEFAULT FALSE,
    employment_type VARCHAR(50) NULL,
    required_experience VARCHAR(50) NULL,
    required_education VARCHAR(100) NULL,
    industry VARCHAR(100) NULL,
    job_function VARCHAR(100) NULL,
    description TEXT NULL,
    description_length INT NOT NULL DEFAULT 0,
    fraudulent BOOLEAN NOT NULL,
    risk_score INT NOT NULL DEFAULT 0,
    risk_level VARCHAR(50) NOT NULL DEFAULT 'LOW',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    UNIQUE KEY uq_postings_source (dataset_name, source_job_id),
    INDEX idx_postings_fraudulent (fraudulent),
    INDEX idx_postings_employment_type (employment_type),
    INDEX idx_postings_industry (industry),
    INDEX idx_postings_country (country),
    INDEX idx_postings_risk_score (risk_score)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 9. Posting signals: which rules fired on which posting (lets us measure each rule separately)
CREATE TABLE posting_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    posting_id INT NOT NULL,
    signal_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    score_impact INT NOT NULL DEFAULT 0,
    INDEX idx_posting_signals_posting (posting_id),
    INDEX idx_posting_signals_type (signal_type),
    CONSTRAINT fk_posting_signals_posting FOREIGN KEY (posting_id) REFERENCES job_postings(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
