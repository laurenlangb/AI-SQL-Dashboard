"""Retrieve the database components from the DATABASE_PATH"""
import sqlite3
from contextlib import contextmanager

from app.config import DATABASE_PATH

# Discover the table name from the database.
with sqlite3.connect(f"file:{DATABASE_PATH}?mode=ro", uri=True) as _conn:
    TABLE_NAME = _conn.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchone()[0]


@contextmanager
def get_db_connection():
    connection = sqlite3.connect(f"file:{DATABASE_PATH}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row

    try:
        yield connection
    finally:
        connection.close()


def fetch_rows():
    with get_db_connection() as connection:
        rows = connection.execute(f"SELECT * FROM {TABLE_NAME}").fetchall()

    return [dict(row) for row in rows]


def get_schema():
    with get_db_connection() as connection:
        columns = connection.execute(f"PRAGMA table_info({TABLE_NAME})").fetchall()

    # Empty PRAGMA result means no table exists.
    if not columns:
        raise sqlite3.OperationalError(f"no such table: {TABLE_NAME}")

    return {
        "table": TABLE_NAME,
        "columns": [
            {"name": column["name"], "type": column["type"]} for column in columns
        ],
    }


def run_query(sql: str) -> list[dict]:
    with get_db_connection() as connection:
        rows = connection.execute(sql).fetchall()

    return [dict(row) for row in rows]
