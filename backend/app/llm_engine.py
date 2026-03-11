"""
llm_engine.py — Google Gemini integration for NL→SQL and data summarization.

Requires the env‑var  GEMINI_API_KEY  (or a .env file loaded by the caller).
"""

import os
import re
import json
from google import genai
from app.database import get_schema_ddl

# ── Client bootstrap ────────────────────────────────────────────────

_client: genai.Client | None = None

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")


def _get_client() -> genai.Client:
    global _client
    if _client is None:
        api_key = os.getenv("GEMINI_API_KEY", "")
        if not api_key:
            raise RuntimeError(
                "GEMINI_API_KEY is not set. "
                "Export it as an environment variable or add it to a .env file."
            )
        _client = genai.Client(api_key=api_key)
    return _client


# ── Conversation history formatting ─────────────────────────────────

def _format_history(history: list[dict]) -> str:
    """
    Convert session history into a text block the LLM can understand.
    Each turn shows what the user asked and what SQL was generated.
    """
    if not history:
        return ""

    lines = ["### Conversation History"]
    for turn in history:
        if turn["role"] == "user":
            lines.append(f"**User:** {turn['prompt']}")
        elif turn["role"] == "assistant" and turn.get("sql"):
            lines.append(f"**Generated SQL:** {turn['sql']}")
    lines.append("")  # trailing newline
    return "\n".join(lines)


# ── NL → SQL ────────────────────────────────────────────────────────

NL2SQL_SYSTEM = """\
You are an expert SQLite database engineer.
Your job is to convert a business question into a valid, read‑only SQLite SELECT query.

Rules:
1. Use ONLY the tables and columns provided in the schema below.
2. Output ONLY the raw SQL query — no markdown fences, no explanation.
3. Never generate INSERT, UPDATE, DELETE, DROP, ALTER, or any DDL.
4. If the question is ambiguous, make a reasonable assumption and proceed.
5. Always alias calculated columns with descriptive names.
6. Use standard SQLite functions and date handling.
7. If the user's question refers to a previous query (e.g. "now filter…",
   "sort that by…", "also show…"), use the conversation history to
   understand what they are referring to and refine the previous SQL
   accordingly.
"""


async def generate_sql_from_prompt(
    prompt: str,
    schema: dict,
    history: list[dict] | None = None,
) -> str:
    """Call Gemini to translate *prompt* into a SQL SELECT statement."""
    ddl = get_schema_ddl()
    if not ddl:
        raise ValueError("Database schema is empty — upload a CSV first.")

    history_block = _format_history(history or [])

    user_message = (
        f"### Database Schema\n{ddl}\n\n"
        f"{history_block}"
        f"### User Question\n{prompt}\n\n"
        "Return ONLY the SQL query."
    )

    client = _get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            {"role": "user", "parts": [{"text": NL2SQL_SYSTEM + "\n\n" + user_message}]}
        ],
    )

    sql = _extract_sql(response.text or "")
    if not sql:
        raise ValueError("The LLM did not return a valid SQL query.")
    return sql


def _extract_sql(raw: str) -> str:
    """
    Strip markdown code‑fences and whitespace, returning the first
    SELECT statement found.
    """
    # Remove ```sql … ``` wrappers if present
    cleaned = re.sub(r"```(?:sql)?\s*", "", raw)
    cleaned = cleaned.replace("```", "").strip()

    # Find the SELECT statement
    match = re.search(r"(SELECT\s.+)", cleaned, re.IGNORECASE | re.DOTALL)
    if match:
        sql = match.group(1).strip().rstrip(";") + ";"
        return sql
    return cleaned


# ── Data summary ────────────────────────────────────────────────────

SUMMARY_SYSTEM = """\
You are an expert data analyst. Given a user's question and the JSON result
set from their database query, write a 1–2 sentence plain‑English insight
that highlights the most notable finding. Be specific with numbers.
If this is a follow‑up question, incorporate context from the conversation
history to make the insight more relevant.
"""


async def generate_summary(
    prompt: str,
    data: list[dict],
    history: list[dict] | None = None,
) -> str:
    """Generate a human‑readable analytical summary of *data*."""
    # Limit data sent to LLM to first 50 rows for token efficiency
    preview = json.dumps(data[:50], default=str)

    history_block = _format_history(history or [])

    user_message = (
        f"### User Question\n{prompt}\n\n"
        f"{history_block}"
        f"### Query Result (JSON)\n{preview}\n\n"
        "Write a concise insight."
    )

    client = _get_client()
    response = client.models.generate_content(
        model=MODEL_NAME,
        contents=[
            {"role": "user", "parts": [{"text": SUMMARY_SYSTEM + "\n\n" + user_message}]}
        ],
    )

    return (response.text or "No summary available.").strip()
