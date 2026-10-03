import os

import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv

load_dotenv()


# MySQL configuration
MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
MYSQL_PORT = int(os.getenv("MYSQL_PORT", "3306"))
MYSQL_DATABASE = os.getenv("MYSQL_DATABASE", "jobshield")
MYSQL_USER = os.getenv("MYSQL_USER", "jobshield_user")
MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "jobshield_pass")


def get_db_connection():
    """
    Create and return a connection to the MySQL database.
    """

    try:
        connection = mysql.connector.connect(
            host=MYSQL_HOST,
            port=MYSQL_PORT,
            database=MYSQL_DATABASE,
            user=MYSQL_USER,
            password=MYSQL_PASSWORD,
            autocommit=True
        )

        return connection

    except Error as e:
        raise Exception(f"Database connection failed: {e}")


def execute_query(query: str, params: tuple = ()):
    """
    Execute INSERT, UPDATE, or DELETE query.

    Returns:
        int: ID of the newly inserted record.
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor()
        cursor.execute(query, params)

        return cursor.lastrowid

    finally:
        cursor.close()
        connection.close()


def fetch_one(query: str, params: tuple = ()):
    """
    Execute a SELECT query and return one row as a dictionary.

    Returns:
        dict or None
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)

        return cursor.fetchone()

    finally:
        cursor.close()
        connection.close()


def fetch_all(query: str, params: tuple = ()):
    """
    Execute a SELECT query and return all rows as dictionaries.

    Returns:
        list
    """

    connection = get_db_connection()

    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute(query, params)

        return cursor.fetchall()

    finally:
        cursor.close()
        connection.close()


def init_db():
    """
    Create all required JobShield tables if they do not already exist.
    """

    queries = [
        """
        CREATE TABLE IF NOT EXISTS users (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(100) NOT NULL,
            email VARCHAR(255) NOT NULL UNIQUE,
            hashed_password VARCHAR(255) NOT NULL,
            is_active BOOLEAN DEFAULT TRUE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS companies (
            id INT PRIMARY KEY AUTO_INCREMENT,
            name VARCHAR(150) NOT NULL,
            website VARCHAR(255),
            domain VARCHAR(150),
            description TEXT,
            careers_url VARCHAR(255),
            verified_domain BOOLEAN DEFAULT FALSE,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS jobs (
            id INT PRIMARY KEY AUTO_INCREMENT,
            company_id INT NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            location VARCHAR(150),
            job_url VARCHAR(500),
            salary_text VARCHAR(150),
            source VARCHAR(100),
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (company_id)
                REFERENCES companies(id)
                ON DELETE CASCADE
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS recruiters (
            id INT PRIMARY KEY AUTO_INCREMENT,
            company_id INT NOT NULL,
            name VARCHAR(150) NOT NULL,
            email VARCHAR(255) NOT NULL,
            email_domain VARCHAR(150) NOT NULL,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (company_id)
                REFERENCES companies(id)
                ON DELETE CASCADE
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS verification_results (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            company_id INT,
            job_id INT,
            verification_type VARCHAR(50) NOT NULL,
            risk_score INT NOT NULL DEFAULT 0,
            risk_level VARCHAR(50) NOT NULL DEFAULT 'LOW',
            verification_status VARCHAR(50) NOT NULL DEFAULT 'INCONCLUSIVE',
            summary TEXT,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (company_id)
                REFERENCES companies(id)
                ON DELETE SET NULL,

            FOREIGN KEY (job_id)
                REFERENCES jobs(id)
                ON DELETE SET NULL
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS verification_signals (
            id INT PRIMARY KEY AUTO_INCREMENT,
            verification_id INT NOT NULL,
            signal_type VARCHAR(100) NOT NULL,
            severity VARCHAR(50) NOT NULL,
            title VARCHAR(200) NOT NULL,
            description TEXT,
            evidence TEXT,
            score_impact INT NOT NULL DEFAULT 0,
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (verification_id)
                REFERENCES verification_results(id)
                ON DELETE CASCADE
        )
        """,

        """
        CREATE TABLE IF NOT EXISTS reports (
            id INT PRIMARY KEY AUTO_INCREMENT,
            user_id INT NOT NULL,
            company_id INT,
            job_id INT,
            report_type VARCHAR(100) NOT NULL,
            description TEXT NOT NULL,
            status VARCHAR(50) NOT NULL DEFAULT 'PENDING',
            created_at DATETIME DEFAULT CURRENT_TIMESTAMP,

            FOREIGN KEY (user_id)
                REFERENCES users(id)
                ON DELETE CASCADE,

            FOREIGN KEY (company_id)
                REFERENCES companies(id)
                ON DELETE SET NULL,

            FOREIGN KEY (job_id)
                REFERENCES jobs(id)
                ON DELETE SET NULL
        )
        """
    ]

    connection = get_db_connection()

    try:
        cursor = connection.cursor()

        for query in queries:
            cursor.execute(query)

        connection.commit()

    finally:
        cursor.close()
        connection.close()