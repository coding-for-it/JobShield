"""
Test setup: tests run against a real MySQL server, but in a SEPARATE database
called `jobshield_test`, so your real `jobshield` data is never touched.

Requirement: MySQL must be running and the user from .env must be allowed to
create databases (the default setup in the README does this).
"""
import os

# Must be set BEFORE the app is imported so the app connects to the test database.
os.environ["MYSQL_DATABASE"] = "jobshield_test"

import pymysql
import pytest
from pathlib import Path
from fastapi.testclient import TestClient

from app.core.config import settings
from app.main import app

SQL_DIR = Path(__file__).resolve().parent.parent / "sql"
SCHEMA_FILES = [SQL_DIR / "schema.sql", SQL_DIR / "analytics_schema.sql"]
TABLES = ["posting_signals", "job_postings", "reports", "verification_signals", "verification_results", "recruiters", "jobs", "companies", "users"]


def _server_connection():
    """Connection to the MySQL server without selecting a database."""
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        charset="utf8mb4",
        autocommit=True,
    )


def _schema_statements():
    """Read the schema files and return their statements, skipping CREATE DATABASE / USE."""
    statements = []
    for schema_file in SCHEMA_FILES:
        lines = [l for l in schema_file.read_text().splitlines() if not l.strip().startswith("--")]
        statements += [s.strip() for s in "\n".join(lines).split(";") if s.strip()]
    return [s for s in statements if not s.upper().startswith(("CREATE DATABASE", "USE "))]


@pytest.fixture(scope="session", autouse=True)
def test_database():
    """Create the jobshield_test database and tables once per test run."""
    conn = _server_connection()
    with conn.cursor() as cur:
        cur.execute("CREATE DATABASE IF NOT EXISTS jobshield_test CHARACTER SET utf8mb4")
        cur.execute("USE jobshield_test")
        for statement in _schema_statements():
            cur.execute(statement)
    conn.close()
    yield


@pytest.fixture(autouse=True)
def clean_tables(test_database):
    """Empty every table before each test so tests do not affect each other."""
    conn = _server_connection()
    with conn.cursor() as cur:
        cur.execute("USE jobshield_test")
        cur.execute("SET FOREIGN_KEY_CHECKS = 0")
        for table in TABLES:
            cur.execute(f"TRUNCATE TABLE {table}")
        cur.execute("SET FOREIGN_KEY_CHECKS = 1")
    conn.close()
    yield


@pytest.fixture
def client():
    """FastAPI TestClient (talks to the real test database through the normal get_db)."""
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def auth_headers(client):
    """Register and log in a test user, returning Bearer Authorization headers."""
    client.post(
        "/api/v1/auth/register",
        json={"name": "Test User", "email": "testuser@example.com", "password": "StrongPassword123"},
    )
    res = client.post(
        "/api/v1/auth/login",
        json={"email": "testuser@example.com", "password": "StrongPassword123"},
    )
    return {"Authorization": f"Bearer {res.json()['access_token']}"}
