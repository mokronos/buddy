from __future__ import annotations

from buddy.tools.todo_store import TodoItem, get_todos


def todoread() -> list[TodoItem]:
    """Read the current in-memory todo list."""
    return get_todos()
