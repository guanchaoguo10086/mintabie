"""SQLite-based session store for conversation persistence."""

import json
import logging
import sqlite3
import threading
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL,
    title TEXT DEFAULT '',
    system_prompt TEXT DEFAULT ''
);

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    role TEXT NOT NULL,
    content TEXT,
    tool_calls TEXT,
    tool_call_id TEXT,
    name TEXT,
    created_at REAL NOT NULL,
    FOREIGN KEY (session_id) REFERENCES sessions(id)
);

CREATE INDEX IF NOT EXISTS idx_messages_session
    ON messages(session_id, id);
"""


class SessionDB:
    """Thread-safe SQLite session store."""

    def __init__(self, db_path: str):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        self._conn = sqlite3.connect(db_path, check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self._conn.executescript(SCHEMA_SQL)
        self._conn.commit()

    def _row_to_dict(self, row: sqlite3.Row) -> dict:
        return dict(row) if row else {}

    def create_session(self, session_id: str, system_prompt: str = "") -> dict:
        now = time.time()
        with self._lock:
            self._conn.execute(
                "INSERT OR IGNORE INTO sessions (id, created_at, updated_at, system_prompt) VALUES (?, ?, ?, ?)",
                (session_id, now, now, system_prompt),
            )
            self._conn.commit()
        return self.get_session(session_id)

    def get_session(self, session_id: str) -> Optional[dict]:
        with self._lock:
            row = self._conn.execute(
                "SELECT * FROM sessions WHERE id = ?", (session_id,)
            ).fetchone()
        return self._row_to_dict(row) if row else None

    def update_title(self, session_id: str, title: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET title = ?, updated_at = ? WHERE id = ?",
                (title, time.time(), session_id),
            )
            self._conn.commit()

    def update_system_prompt(self, session_id: str, prompt: str) -> None:
        with self._lock:
            self._conn.execute(
                "UPDATE sessions SET system_prompt = ?, updated_at = ? WHERE id = ?",
                (prompt, time.time(), session_id),
            )
            self._conn.commit()

    def add_message(
        self,
        session_id: str,
        role: str,
        content: Optional[str] = None,
        tool_calls: Optional[List[dict]] = None,
        tool_call_id: Optional[str] = None,
        name: Optional[str] = None,
    ) -> int:
        now = time.time()
        tc_json = json.dumps(tool_calls) if tool_calls else None
        with self._lock:
            cur = self._conn.execute(
                """INSERT INTO messages
                   (session_id, role, content, tool_calls, tool_call_id, name, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?)""",
                (session_id, role, content, tc_json, tool_call_id, name, now),
            )
            self._conn.commit()
        return cur.lastrowid

    def get_messages(self, session_id: str, limit: int = 200) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                """SELECT * FROM messages
                   WHERE session_id = ?
                   ORDER BY id ASC
                   LIMIT ?""",
                (session_id, limit),
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def recent_sessions(self, limit: int = 10) -> List[dict]:
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM sessions ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [self._row_to_dict(r) for r in rows]

    def close(self):
        self._conn.close()
