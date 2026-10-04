-- JobShield Database Schema for MySQL 8.0

CREATE DATABASE IF NOT EXISTS jobshield CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE jobshield;

-- Drop tables in reverse foreign key dependency order
DROP TABLE IF EXISTS reports;
DROP TABLE IF EXISTS verification_signals;
DROP TABLE IF EXISTS verification_results;
DROP TABLE IF EXISTS recruiters;
DROP TABLE IF EXISTS jobs;
DROP TABLE IF EXISTS companies;
DROP TABLE IF EXISTS users;

-- 1. Users table
CREATE TABLE users (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) NOT NULL UNIQUE,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT TRUE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_users_email (email)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 2. Companies table
CREATE TABLE companies (
    id INT AUTO_INCREMENT PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    website VARCHAR(255) NULL,
    domain VARCHAR(150) NULL,
    description TEXT NULL,
    careers_url VARCHAR(255) NULL,
    verified_domain BOOLEAN DEFAULT FALSE NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_companies_name (name),
    INDEX idx_companies_domain (domain)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 3. Jobs table
CREATE TABLE jobs (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    location VARCHAR(150) NULL,
    job_url VARCHAR(500) NULL,
    salary_text VARCHAR(150) NULL,
    source VARCHAR(100) NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_jobs_company_id (company_id),
    INDEX idx_jobs_title (title),
    CONSTRAINT fk_jobs_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 4. Recruiters table
CREATE TABLE recruiters (
    id INT AUTO_INCREMENT PRIMARY KEY,
    company_id INT NOT NULL,
    name VARCHAR(150) NOT NULL,
    email VARCHAR(255) NOT NULL,
    email_domain VARCHAR(150) NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_recruiters_company_id (company_id),
    INDEX idx_recruiters_email (email),
    INDEX idx_recruiters_email_domain (email_domain),
    CONSTRAINT fk_recruiters_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 5. Verification Results table
CREATE TABLE verification_results (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_id INT NULL,
    job_id INT NULL,
    verification_type VARCHAR(50) NOT NULL,
    risk_score INT NOT NULL DEFAULT 0,
    risk_level VARCHAR(50) NOT NULL DEFAULT 'LOW',
    verification_status VARCHAR(50) NOT NULL DEFAULT 'INCONCLUSIVE',
    summary TEXT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_verification_user_id (user_id),
    INDEX idx_verification_company_id (company_id),
    INDEX idx_verification_job_id (job_id),
    CONSTRAINT fk_verification_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_verification_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
    CONSTRAINT fk_verification_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 6. Verification Signals table
CREATE TABLE verification_signals (
    id INT AUTO_INCREMENT PRIMARY KEY,
    verification_id INT NOT NULL,
    signal_type VARCHAR(100) NOT NULL,
    severity VARCHAR(50) NOT NULL,
    title VARCHAR(200) NOT NULL,
    description TEXT NULL,
    evidence TEXT NULL,
    score_impact INT NOT NULL DEFAULT 0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_signals_verification_id (verification_id),
    CONSTRAINT fk_signals_verification FOREIGN KEY (verification_id) REFERENCES verification_results(id) ON DELETE CASCADE
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 7. Reports table
CREATE TABLE reports (
    id INT AUTO_INCREMENT PRIMARY KEY,
    user_id INT NOT NULL,
    company_id INT NULL,
    job_id INT NULL,
    report_type VARCHAR(100) NOT NULL,
    description TEXT NOT NULL,
    status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP NOT NULL,
    INDEX idx_reports_user_id (user_id),
    INDEX idx_reports_company_id (company_id),
    INDEX idx_reports_job_id (job_id),
    CONSTRAINT fk_reports_user FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE,
    CONSTRAINT fk_reports_company FOREIGN KEY (company_id) REFERENCES companies(id) ON DELETE SET NULL,
    CONSTRAINT fk_reports_job FOREIGN KEY (job_id) REFERENCES jobs(id) ON DELETE SET NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
