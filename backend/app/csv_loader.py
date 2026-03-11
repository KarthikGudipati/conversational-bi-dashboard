"""
csv_loader.py — Ingest a CSV file (as raw bytes) into an SQLite table
using pandas. Supports automatic encoding detection with fallback.

Encoding strategy:
  1. Try reading as UTF-8 (handles the vast majority of well-formed CSVs).
  2. If a UnicodeDecodeError is raised, transparently retry with "latin1"
     (ISO-8859-1), which can decode any byte value 0x00-0xFF and covers
     most legacy Windows / European exports.
"""

import io
import re

import pandas as pd
from app.database import get_connection


# ── Public API ───────────────────────────────────────────────────────

def load_csv_to_sqlite(
    file_bytes: bytes,
    original_filename: str,
    table_name: str | None = None,
) -> tuple[str, int, list[str]]:
    """
    Parse *file_bytes* as CSV using pandas, automatically falling back
    from UTF-8 to latin1 encoding when needed, and write the resulting
    DataFrame into a SQLite table.

    Parameters
    ----------
    file_bytes : bytes
        Raw content of the uploaded CSV file.
    original_filename : str
        The original filename (used to derive a table name if none given).
    table_name : str | None
        Explicit table name. Falls back to a sanitised version of the
        filename when not provided.

    Returns
    -------
    tuple[str, int, list[str]]
        (table_name, rows_loaded, list_of_column_names)
    """

    # --- Step 1: Read CSV bytes into a pandas DataFrame ---------------
    #     Try UTF-8 first; on failure, fall back to latin1.
    df = _read_csv_with_fallback(file_bytes)

    if df.empty:
        raise ValueError("CSV file contains headers but no data rows.")

    # --- Step 2: Sanitise column names for SQL safety -----------------
    df.columns = [_sanitize(col) for col in df.columns]

    # --- Step 3: Determine the target table name ----------------------
    resolved_table = table_name or _table_name_from_file(original_filename)

    # --- Step 4: Write the DataFrame into SQLite ----------------------
    conn = get_connection()
    try:
        df.to_sql(
            resolved_table,
            conn,
            if_exists="replace",   # overwrite if the table already exists
            index=False,
        )
        conn.commit()
    finally:
        conn.close()

    return resolved_table, len(df), list(df.columns)


# ── Encoding-aware CSV reader ────────────────────────────────────────

def _read_csv_with_fallback(file_bytes: bytes) -> pd.DataFrame:
    """
    Attempt to read CSV bytes as UTF-8. If a UnicodeDecodeError occurs,
    retry with latin1 encoding which can decode any single-byte value.

    Using io.BytesIO so pandas receives a proper file-like object
    compatible with FastAPI's in-memory upload buffers.
    """

    # ── Primary attempt: UTF-8 ───────────────────────────────────────
    try:
        buffer = io.BytesIO(file_bytes)
        df = pd.read_csv(buffer, encoding="utf-8")
        return df
    except UnicodeDecodeError:
        pass  # fall through to the latin1 retry below

    # ── Fallback: latin1 (ISO-8859-1) ────────────────────────────────
    # latin1 maps every byte 0x00-0xFF to a valid character, so it will
    # never raise a UnicodeDecodeError. This successfully handles CSVs
    # exported from legacy Windows tools and European locale systems.
    buffer = io.BytesIO(file_bytes)
    df = pd.read_csv(buffer, encoding="latin1")
    return df


# ── Internal helpers ─────────────────────────────────────────────────

def _sanitize(name: str) -> str:
    """Turn an arbitrary header string into a safe SQL column name."""
    s = str(name).strip().lower()
    s = re.sub(r"[^a-z0-9]+", "_", s)
    s = s.strip("_")
    return s or "col"


def _table_name_from_file(filename: str) -> str:
    """Derive a table name from the uploaded filename."""
    base = filename.rsplit(".", 1)[0]
    return _sanitize(base)
