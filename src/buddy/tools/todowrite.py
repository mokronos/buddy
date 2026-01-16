from __future__ import annotations

from buddy.tools.todo_store import TodoItem, set_todos

_ALLOWED_STATUS = {"pending", "in_progress", "completed", "cancelled"}
_ALLOWED_PRIORITY = {"low", "medium", "high"}
_REQUIRED_FIELDS = {"content", "status", "priority", "id"}


def _validate_item(item: TodoItem, index: int) -> None:
    missing = _REQUIRED_FIELDS - set(item)
    if missing:
        msg = f"Todo item {index} missing fields: {', '.join(sorted(missing))}"
        raise ValueError(msg)

    if item["status"] not in _ALLOWED_STATUS:
        msg = f"Todo item {index} has invalid status '{item['status']}'"
        raise ValueError(msg)

    if item["priority"] not in _ALLOWED_PRIORITY:
        msg = f"Todo item {index} has invalid priority '{item['priority']}'"
        raise ValueError(msg)

    if not item["content"].strip():
        msg = f"Todo item {index} content cannot be empty"
        raise ValueError(msg)

    if not item["id"].strip():
        msg = f"Todo item {index} id cannot be empty"
        raise ValueError(msg)


def todowrite(todos: list[TodoItem]) -> list[TodoItem]:
    """Create or replace the in-memory todo list.

    Args:
        todos: List of todo items with content, status, priority, and id.

    Returns:
        The updated todo list stored in memory.
    """
    for index, item in enumerate(todos):
        _validate_item(item, index)

    set_todos(todos)
    return todos
