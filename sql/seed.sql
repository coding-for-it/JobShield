-- JobShield Database Seed Script

USE jobshield;

-- Seed user: user@example.com / StrongPassword123 (password stored as a bcrypt hash)
INSERT INTO users (id, name, email, hashed_password, is_active, created_at, updated_at)
VALUES (1, 'Test User', 'user@example.com', '$2b$12$dRUWXrTzlQX4Qhv07vlFbe/Jo4T4qqmXksrjeiVhEU9rzveKRr3mO', TRUE, NOW(), NOW())
ON DUPLICATE KEY UPDATE id=id;

-- Seed Companies
INSERT INTO companies (id, name, website, domain, description, careers_url, verified_domain, created_at, updated_at)
VALUES 
(1, 'TechCorp Solutions', 'https://techcorp.com', 'techcorp.com', 'Leading cloud software engineering provider.', 'https://techcorp.com/careers', TRUE, NOW(), NOW()),
(2, 'Global Innovations Inc', 'https://globalinnovations.io', 'globalinnovations.io', 'Global IT consulting services firm.', 'https://globalinnovations.io/jobs', TRUE, NOW(), NOW()),
(3, 'QuickHire Recruiter Group', 'https://quickhire-placement.net', 'quickhire-placement.net', 'Third party recruiting agency.', NULL, FALSE, NOW(), NOW())
ON DUPLICATE KEY UPDATE id=id;

-- Seed Jobs
INSERT INTO jobs (id, company_id, title, description, location, job_url, salary_text, source, created_at, updated_at)
VALUES 
(1, 1, 'Junior Backend Developer (Python/FastAPI)', 'Build scalable RESTful APIs using Python, FastAPI, MySQL, and Docker.', 'Remote', 'https://techcorp.com/careers/backend-dev', '$70,000 - $85,000', 'Official Site', NOW(), NOW()),
(2, 2, 'Data Analyst', 'Analyze business datasets using SQL, Python, and BI tools.', 'Hybrid - New York', 'https://globalinnovations.io/jobs/data-analyst', '$65,000 - $75,000', 'LinkedIn', NOW(), NOW())
ON DUPLICATE KEY UPDATE id=id;

-- Seed Recruiters
INSERT INTO recruiters (id, company_id, name, email, email_domain, created_at)
VALUES 
(1, 1, 'Alice Smith', 'alice.smith@techcorp.com', 'techcorp.com', NOW()),
(2, 2, 'Robert Johnson', 'robert.j@globalinnovations.io', 'globalinnovations.io', NOW())
ON DUPLICATE KEY UPDATE id=id;
