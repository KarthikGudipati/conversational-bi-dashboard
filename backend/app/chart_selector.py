"""
chart_selector.py — Heuristic chart‑type recommender.

Analyses the shape of query results to pick the best visualisation.
Returns a config dict the React frontend can consume directly.
"""

import re
from datetime import datetime


# ── Helpers ──────────────────────────────────────────────────────────

def _is_numeric(value) -> bool:
    """Check whether a value is numeric (int / float)."""
    if isinstance(value, (int, float)):
        return True
    if isinstance(value, str):
        try:
            float(value)
            return True
        except ValueError:
            return False
    return False


def _is_date_like(value) -> bool:
    """Rough check for date‑shaped strings."""
    if not isinstance(value, str):
        return False
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%m-%d-%Y", "%d-%m-%Y", "%Y-%m", "%Y"):
        try:
            datetime.strptime(value.strip(), fmt)
            return True
        except ValueError:
            continue
    return False


def _classify_columns(data: list[dict]) -> dict[str, str]:
    """
    Return a mapping of column_name → 'numeric' | 'date' | 'category'
    based on the first non‑null value in each column.
    """
    if not data:
        return {}

    classification: dict[str, str] = {}
    for col in data[0].keys():
        # Find the first non-null value for this column
        sample = None
        for row in data[:20]:
            if row.get(col) is not None:
                sample = row[col]
                break

        if sample is None:
            classification[col] = "category"
        elif _is_date_like(sample):
            classification[col] = "date"
        elif _is_numeric(sample):
            classification[col] = "numeric"
        else:
            classification[col] = "category"

    return classification


# ── Public API ───────────────────────────────────────────────────────

def recommend_chart(
    data: list[dict],
    sql: str,
    prompt: str,
) -> dict:
    """
    Decide the best chart type and axis mapping for *data*.

    Returns a dict like:
        {
            "type": "bar",
            "xAxis": "campaign_name",
            "yAxis": ["clicks", "impressions"],
            "title": "Clicks & Impressions by Campaign"
        }
    """
    if not data:
        return {"type": "table", "xAxis": None, "yAxis": [], "title": "No data"}

    col_types = _classify_columns(data)
    num_rows = len(data)

    date_cols = [c for c, t in col_types.items() if t == "date"]
    numeric_cols = [c for c, t in col_types.items() if t == "numeric"]
    cat_cols = [c for c, t in col_types.items() if t == "category"]

    # ── Rule 1: Single KPI metric card ──────────────────────────────
    if num_rows == 1 and len(numeric_cols) == 1 and len(cat_cols) == 0:
        return {
            "type": "metric",
            "xAxis": None,
            "yAxis": numeric_cols,
            "title": numeric_cols[0].replace("_", " ").title(),
        }

    # ── Rule 2: Time‑series → line chart ────────────────────────────
    if date_cols and numeric_cols:
        return {
            "type": "line",
            "xAxis": date_cols[0],
            "yAxis": numeric_cols,
            "title": _auto_title(numeric_cols, date_cols[0]),
        }

    # ── Rule 3: Pie / donut when prompt implies proportions ─────────
    proportion_keywords = r"\b(share|percent|proportion|distribution|breakdown|split)\b"
    if (
        re.search(proportion_keywords, prompt, re.IGNORECASE)
        and cat_cols
        and len(numeric_cols) == 1
    ):
        return {
            "type": "pie",
            "xAxis": cat_cols[0],
            "yAxis": numeric_cols,
            "title": f"{numeric_cols[0].replace('_', ' ').title()} by {cat_cols[0].replace('_', ' ').title()}",
        }

    # ── Rule 4: Categorical + numeric → bar chart ───────────────────
    if cat_cols and numeric_cols:
        return {
            "type": "bar",
            "xAxis": cat_cols[0],
            "yAxis": numeric_cols,
            "title": _auto_title(numeric_cols, cat_cols[0]),
        }

    # ── Rule 5: Multiple numeric only → bar chart (use first col as x)
    if len(numeric_cols) >= 2:
        return {
            "type": "bar",
            "xAxis": numeric_cols[0],
            "yAxis": numeric_cols[1:],
            "title": _auto_title(numeric_cols[1:], numeric_cols[0]),
        }

    # ── Fallback: data table ────────────────────────────────────────
    return {
        "type": "table",
        "xAxis": None,
        "yAxis": [],
        "title": "Query Results",
    }


def _auto_title(metrics: list[str], dimension: str) -> str:
    """Build a human‑readable chart title from column names."""
    pretty = [m.replace("_", " ").title() for m in metrics[:3]]
    dim = dimension.replace("_", " ").title()
    return f"{', '.join(pretty)} by {dim}"
