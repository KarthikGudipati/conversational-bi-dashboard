"""
session_store.py — In-memory conversation session store.

Maintains per-session conversation history so follow-up queries
can reference prior questions and SQL results.
"""

import time
import uuid
from dataclasses import dataclass, field

# ── Configuration ────────────────────────────────────────────────────

MAX_TURNS_PER_SESSION = 20
SESSION_TTL_SECONDS = 30 * 60  # 30 minutes


# ── Data structures ─────────────────────────────────────────────────

@dataclass
class ConversationTurn:
    role: str          # "user" or "assistant"
    prompt: str        # the natural-language question
    sql: str = ""      # the generated SQL (only for assistant turns)


@dataclass
class Session:
    session_id: str
    turns: list[ConversationTurn] = field(default_factory=list)
    last_active: float = field(default_factory=time.time)


# ── Store ────────────────────────────────────────────────────────────

_sessions: dict[str, Session] = {}


def _is_expired(session: Session) -> bool:
    return (time.time() - session.last_active) > SESSION_TTL_SECONDS


def create_session() -> str:
    """Create a new session and return its ID."""
    sid = str(uuid.uuid4())
    _sessions[sid] = Session(session_id=sid)
    return sid


def get_history(session_id: str) -> list[dict]:
    """
    Return the conversation history for the given session as a list of
    dicts: [{"role": ..., "prompt": ..., "sql": ...}, ...].
    Returns an empty list if the session doesn't exist or has expired.
    """
    session = _sessions.get(session_id)
    if session is None or _is_expired(session):
        # Clean up expired session
        _sessions.pop(session_id, None)
        return []

    session.last_active = time.time()
    return [
        {"role": t.role, "prompt": t.prompt, "sql": t.sql}
        for t in session.turns
    ]


def add_turn(session_id: str, prompt: str, sql: str) -> None:
    """
    Record a completed query turn (user question + generated SQL).
    Creates the session if it doesn't exist.
    """
    if session_id not in _sessions:
        _sessions[session_id] = Session(session_id=session_id)

    session = _sessions[session_id]
    session.last_active = time.time()

    # Add user turn + assistant turn
    session.turns.append(ConversationTurn(role="user", prompt=prompt))
    session.turns.append(ConversationTurn(role="assistant", prompt=prompt, sql=sql))

    # Cap history length
    if len(session.turns) > MAX_TURNS_PER_SESSION * 2:
        session.turns = session.turns[-(MAX_TURNS_PER_SESSION * 2):]


def clear_session(session_id: str) -> None:
    """Remove a session entirely."""
    _sessions.pop(session_id, None)
