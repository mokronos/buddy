from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from pydantic_ai import ModelMessagesTypeAdapter
from pydantic_core import to_jsonable_python


class SessionStore:
    def __init__(self, db_path: Path) -> None:
        self._db_path = db_path
        self._ensure_parent()
        self._init_schema()

    def list_sessions(self, limit: int = 20) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT session_id, created_at, updated_at FROM sessions ORDER BY updated_at DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [
            {"session_id": session_id, "created_at": created_at, "updated_at": updated_at}
            for session_id, created_at, updated_at in rows
        ]

    def get_session(self, session_id: str) -> dict[str, str] | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT session_id, created_at, updated_at FROM sessions WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        if row is None:
            return None
        return {"session_id": row[0], "created_at": row[1], "updated_at": row[2]}

    def load_chat_messages(self, session_id: str) -> list[dict[str, str]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT id, role, content FROM chat_messages WHERE session_id = ? ORDER BY id",
                (session_id,),
            ).fetchall()
        return [{"id": str(message_id), "role": role, "content": content} for message_id, role, content in rows]

    def append_chat_message(self, session_id: str, role: str, content: str) -> None:
        now = self._now()
        with self._connect() as conn:
            self._upsert_session(conn, session_id, now)
            conn.execute(
                "INSERT INTO chat_messages(session_id, role, content, created_at) VALUES(?, ?, ?, ?)",
                (session_id, role, content, now),
            )

    def load_messages(self, session_id: str) -> list[Any]:
        payloads = self.load_messages_payload(session_id)
        if not payloads:
            return []
        return ModelMessagesTypeAdapter.validate_python(payloads)

    def load_messages_payload(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT message_json FROM messages WHERE session_id = ? ORDER BY message_index",
                (session_id,),
            ).fetchall()
        return [json.loads(item[0]) for item in rows]

    def save_messages(self, session_id: str, messages: list[Any] | object) -> None:
        payloads = to_jsonable_python(messages)
        if not isinstance(payloads, list):
            payloads = []
        payloads = [item for item in payloads if isinstance(item, dict)]
        now = self._now()
        with self._connect() as conn:
            self._upsert_session(conn, session_id, now)
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.executemany(
                "INSERT INTO messages(session_id, message_index, message_json, created_at) VALUES(?, ?, ?, ?)",
                [(session_id, index, json.dumps(message), now) for index, message in enumerate(payloads)],
            )

    def load_events(self, session_id: str) -> list[dict[str, Any]]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT payload_json FROM events WHERE session_id = ? ORDER BY event_index",
                (session_id,),
            ).fetchall()
        return [json.loads(item[0]) for item in rows]

    def next_event_index(self, session_id: str) -> int:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT COALESCE(MAX(event_index) + 1, 0) FROM events WHERE session_id = ?",
                (session_id,),
            ).fetchone()
        return int(row[0]) if row else 0

    def append_event(self, session_id: str, event_index: int, payload: dict[str, Any]) -> None:
        payload_json = json.dumps(payload)
        now = self._now()
        event_type = payload.get("kind", "unknown")
        with self._connect() as conn:
            self._upsert_session(conn, session_id, now)
            conn.execute(
                "INSERT INTO events(session_id, event_index, event_type, payload_json, created_at)"
                " VALUES(?, ?, ?, ?, ?)",
                (session_id, event_index, event_type, payload_json, now),
            )

    def _ensure_parent(self) -> None:
        self._db_path.parent.mkdir(parents=True, exist_ok=True)

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._db_path)
        conn.execute("PRAGMA journal_mode=WAL")
        conn.execute("PRAGMA foreign_keys=ON")
        return conn

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(
                "CREATE TABLE IF NOT EXISTS sessions("
                " session_id TEXT PRIMARY KEY,"
                " created_at TEXT NOT NULL,"
                " updated_at TEXT NOT NULL,"
                " metadata_json TEXT NOT NULL"
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS messages("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " session_id TEXT NOT NULL,"
                " message_index INTEGER NOT NULL,"
                " message_json TEXT NOT NULL,"
                " created_at TEXT NOT NULL,"
                " FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE"
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS events("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " session_id TEXT NOT NULL,"
                " event_index INTEGER NOT NULL,"
                " event_type TEXT NOT NULL,"
                " payload_json TEXT NOT NULL,"
                " created_at TEXT NOT NULL,"
                " FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE"
                ")"
            )
            conn.execute(
                "CREATE TABLE IF NOT EXISTS chat_messages("
                " id INTEGER PRIMARY KEY AUTOINCREMENT,"
                " session_id TEXT NOT NULL,"
                " role TEXT NOT NULL,"
                " content TEXT NOT NULL,"
                " created_at TEXT NOT NULL,"
                " FOREIGN KEY(session_id) REFERENCES sessions(session_id) ON DELETE CASCADE"
                ")"
            )

    @staticmethod
    def _now() -> str:
        return datetime.now(tz=timezone.utc).isoformat()

    @staticmethod
    def _upsert_session(conn: sqlite3.Connection, session_id: str, now: str) -> None:
        conn.execute(
            "INSERT INTO sessions(session_id, created_at, updated_at, metadata_json)"
            " VALUES(?, ?, ?, ?)"
            " ON CONFLICT(session_id) DO UPDATE SET updated_at=excluded.updated_at",
            (session_id, now, now, "{}"),
        )
