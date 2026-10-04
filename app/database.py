"""
Database access using plain SQL and PyMySQL (no ORM).

How it works:
- Each API request opens ONE MySQL connection (get_db) and closes it when done.
- Services write normal SQL with %s placeholders. The driver fills the values in
  safely, which is what protects us from SQL injection.
- Rows come back as dictionaries, e.g. {"id": 1, "name": "TechCorp"}.
- We commit explicitly, so a multi-step operation is one transaction.
"""
from typing import Any, Dict, Generator, List, Optional, Sequence

import pymysql
from pymysql.connections import Connection
from pymysql.cursors import DictCursor

from app.core.config import settings


def get_connection() -> Connection:
    """Open a new MySQL connection using the values from .env."""
    return pymysql.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DATABASE,
        charset="utf8mb4",
        cursorclass=DictCursor,
        autocommit=False,
    )


def get_db() -> Generator[Connection, None, None]:
    """FastAPI dependency: one connection per request, always closed afterwards."""
    conn = get_connection()
    try:
        yield conn
    except Exception:
        conn.rollback()  # undo half-finished work if something failed
        raise
    finally:
        conn.close()


def fetch_one(db: Connection, sql: str, params: Sequence[Any] = ()) -> Optional[Dict[str, Any]]:
    """Run a SELECT and return the first row (or None)."""
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.fetchone()


def fetch_all(db: Connection, sql: str, params: Sequence[Any] = ()) -> List[Dict[str, Any]]:
    """Run a SELECT and return all rows."""
    with db.cursor() as cur:
        cur.execute(sql, params)
        return list(cur.fetchall())


def execute(db: Connection, sql: str, params: Sequence[Any] = ()) -> int:
    """Run an INSERT / UPDATE / DELETE. Returns the new row id for inserts.
    Does NOT commit - the caller calls db.commit() when the whole operation is done."""
    with db.cursor() as cur:
        cur.execute(sql, params)
        return cur.lastrowid


def update_row(db: Connection, table: str, row_id: int, fields: Dict[str, Any]) -> None:
    """Partial update: UPDATE <table> SET col = %s, ... WHERE id = %s.

    `table` and the column names are never typed by a user: they come from our own
    code and from Pydantic schema field names. Only the VALUES come from the user,
    and those always go through %s placeholders.
    """
    if not fields:
        return
    set_clause = ", ".join(f"{column} = %s" for column in fields)
    execute(db, f"UPDATE {table} SET {set_clause} WHERE id = %s", [*fields.values(), row_id])
    db.commit()
