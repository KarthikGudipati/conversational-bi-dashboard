"""
sql_executor.py — Safe, read‑only SQL execution against SQLite.
"""

import re
from app.database import get_connection

# Patterns that indicate a write / DDL operation
_FORBIDDEN_PATTERNS = re.compile(
    r"\b(INSERT|UPDATE|DELETE|DROP|ALTER|CREATE|REPLACE|ATTACH|DETACH|VACUUM|REINDEX)\b",
    re.IGNORECASE,
)

MAX_ROWS = 500  # Hard cap to avoid blowing up JSON payloads


def execute_query(sql: str) -> list[dict]:
    """
    Execute a read‑only SQL statement and return the result set as a
    list of dictionaries.

    Raises ValueError if the SQL contains write operations.
    """
    # Guard: reject anything that is not a pure SELECT
    if _FORBIDDEN_PATTERNS.search(sql):
        raise ValueError(
            "Only SELECT queries are allowed. "
            "The generated SQL contained a forbidden keyword."
        )

    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(sql)
        columns = [description[0] for description in cursor.description or []]
        rows = cursor.fetchmany(MAX_ROWS)
        return [dict(zip(columns, row)) for row in rows]
    finally:
        conn.close()
