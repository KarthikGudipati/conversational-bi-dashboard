"""
Conversational BI Dashboard — FastAPI Backend
Entry point: registers CORS, routes, and lifespan events.
"""

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from app.database import get_schema_info
from app.llm_engine import generate_sql_from_prompt, generate_summary
from app.sql_executor import execute_query
from app.chart_selector import recommend_chart
from app.csv_loader import load_csv_to_sqlite
from app.session_store import (
    create_session,
    get_history,
    add_turn,
    clear_session,
)

from dotenv import load_dotenv
import os

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")

# ── Pydantic schemas ────────────────────────────────────────────────

class QueryRequest(BaseModel):
    prompt: str
    session_id: Optional[str] = None

class QueryResponse(BaseModel):
    prompt: str
    sql: str
    data: list[dict]
    chart_config: dict
    summary: str
    session_id: str

class UploadResponse(BaseModel):
    message: str
    table_name: str
    rows_loaded: int
    columns_detected: list[str]

class SchemaResponse(BaseModel):
    tables: dict

class SessionClearRequest(BaseModel):
    session_id: str

class SessionClearResponse(BaseModel):
    message: str


# ── FastAPI app ──────────────────────────────────────────────────────

app = FastAPI(
    title="Conversational BI Dashboard API",
    version="1.0.0",
    description="Natural‑language queries → SQL → interactive charts",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Routes ───────────────────────────────────────────────────────────

@app.post("/query", response_model=QueryResponse)
async def query_endpoint(req: QueryRequest):
    """
    Accept a natural‑language prompt, convert it to SQL via Gemini,
    execute the query, pick the best chart type, and return everything.
    Maintains conversation context via session_id.
    """
    try:
        # 0. Resolve session
        session_id = req.session_id or create_session()
        history = get_history(session_id)

        # 1. Retrieve the current database schema
        schema = get_schema_info()
        if not schema:
            raise HTTPException(
                status_code=400,
                detail="No tables found. Please upload a CSV first.",
            )

        # 2. Convert natural language → SQL (with conversation context)
        sql = await generate_sql_from_prompt(req.prompt, schema, history=history)

        # 3. Execute the SQL against SQLite
        data = execute_query(sql)

        # 4. Determine the best chart type
        chart_config = recommend_chart(data, sql, req.prompt)

        # 5. Generate a short analytical summary (with conversation context)
        summary = await generate_summary(req.prompt, data, history=history)

        # 6. Record this turn in session history
        add_turn(session_id, req.prompt, sql)

        return QueryResponse(
            prompt=req.prompt,
            sql=sql,
            data=data,
            chart_config=chart_config,
            summary=summary,
            session_id=session_id,
        )

    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/session/clear", response_model=SessionClearResponse)
async def clear_session_endpoint(req: SessionClearRequest):
    """Clear conversation history for a session."""
    clear_session(req.session_id)
    return SessionClearResponse(message="Session cleared successfully")


@app.post("/upload_csv", response_model=UploadResponse)
async def upload_csv_endpoint(file: UploadFile = File(...)):
    """
    Upload a CSV file and load it into the SQLite database.
    The data is always written to the 'campaign_performance' table.
    Encoding is auto-detected (UTF-8 with latin1 fallback).
    """
    if not file.filename or not file.filename.endswith(".csv"):
        raise HTTPException(status_code=400, detail="Only .csv files are accepted.")

    try:
        contents = await file.read()
        table_name, rows_loaded, columns = load_csv_to_sqlite(
            file_bytes=contents,
            original_filename=file.filename,
            table_name="campaign_performance",
        )
        return UploadResponse(
            message="CSV uploaded successfully",
            table_name=table_name,
            rows_loaded=rows_loaded,
            columns_detected=columns,
        )
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/schema", response_model=SchemaResponse)
async def schema_endpoint():
    """Return the current database schema (tables → columns)."""
    return SchemaResponse(tables=get_schema_info())


@app.get("/health")
async def health_check():
    return {"status": "ok"}
