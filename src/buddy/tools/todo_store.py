from __future__ import annotations

from typing import Literal, TypedDict


class TodoItem(TypedDict):
    content: str
    status: Literal["pending", "in_progress", "completed", "cancelled"]
    priority: Literal["low", "medium", "high"]
    id: str


_todos: list[TodoItem] = []


def get_todos() -> list[TodoItem]:
    return list(_todos)


def set_todos(todos: list[TodoItem]) -> None:
    global _todos
    _todos = list(todos)
