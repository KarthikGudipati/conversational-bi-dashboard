"""
database.py — SQLite connection management and schema introspection.

Uses a single on-disk database stored in  backend/data/marketing.db.
"""

import sqlite3
import os

DB_DIR = os.path.join(os.path.dirname(os.path.dirname(__file__)), "data")
DB_PATH = os.path.join(DB_DIR, "marketing.db")


def _ensure_db_dir() -> None:
    """Create the data directory if it does not exist."""
    os.makedirs(DB_DIR, exist_ok=True)


def get_connection() -> sqlite3.Connection:
    """Return a new connection with row‑factory enabled."""
    _ensure_db_dir()
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def get_schema_info() -> dict[str, list[dict]]:
    """
    Introspect all user tables and return a mapping of
    table_name → list of {column_name, column_type}.
    """
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch all non-system tables
    cursor.execute(
        "SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    tables = [row["name"] for row in cursor.fetchall()]

    schema: dict[str, list[dict]] = {}
    for table in tables:
        cursor.execute(f"PRAGMA table_info('{table}');")
        columns = [
            {"column_name": col["name"], "column_type": col["type"]}
            for col in cursor.fetchall()
        ]
        schema[table] = columns

    conn.close()
    return schema


def get_schema_ddl() -> str:
    """
    Return a string containing CREATE TABLE statements for every user
    table — used as context for the LLM prompt.
    """
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute(
        "SELECT name, sql FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%';"
    )
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return ""

    return "\n\n".join(row["sql"] for row in rows if row["sql"])
