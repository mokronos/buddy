from __future__ import annotations

from pathlib import Path
from typing import Literal, TypedDict

from buddy.session_store import SessionStore


class TodoItem(TypedDict):
    content: str
    status: Literal["pending", "in_progress", "completed", "cancelled"]
    priority: Literal["low", "medium", "high"]
    id: str


_STORE = SessionStore(Path(".buddy") / "sessions.db")
_SCOPE = "default"


def get_todos() -> list[TodoItem]:
    todos = _STORE.load_todos(_SCOPE)
    return [todo for todo in todos if isinstance(todo, dict)]


def set_todos(todos: list[TodoItem]) -> None:
    _STORE.save_todos(_SCOPE, [dict(todo) for todo in todos])
