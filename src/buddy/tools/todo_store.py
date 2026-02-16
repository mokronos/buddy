from pathlib import Path
from typing import Literal, TypedDict, cast

from buddy.session_store import SessionStore


class TodoItem(TypedDict):
    content: str
    status: Literal["pending", "in_progress", "completed", "cancelled"]
    priority: Literal["low", "medium", "high"]
    id: str


class TodoPatch(TypedDict, total=False):
    content: str
    status: Literal["pending", "in_progress", "completed", "cancelled"]
    priority: Literal["low", "medium", "high"]


class TodoUpdateResult(TypedDict):
    before: TodoItem
    after: TodoItem
    todos: list[TodoItem]


_STORE = SessionStore(Path("sessions.db"))
_SCOPE = "default"
_ALLOWED_STATUS = {"pending", "in_progress", "completed", "cancelled"}
_ALLOWED_PRIORITY = {"low", "medium", "high"}
_REQUIRED_FIELDS = {"content", "status", "priority", "id"}


def get_todos() -> list[TodoItem]:
    todos = _STORE.load_todos(_SCOPE)
    filtered = [todo for todo in todos if isinstance(todo, dict)]
    return cast(list[TodoItem], filtered)


def set_todos(todos: list[TodoItem]) -> None:
    _STORE.save_todos(_SCOPE, [dict(todo) for todo in todos])


def validate_todo_item(item: TodoItem, index: int) -> None:
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


def validate_todo_patch(patch: TodoPatch) -> None:
    if not patch:
        raise ValueError("Todo patch cannot be empty")

    unknown_fields = set(patch) - {"content", "status", "priority"}
    if unknown_fields:
        msg = f"Todo patch has unsupported fields: {', '.join(sorted(unknown_fields))}"
        raise ValueError(msg)

    if "content" in patch and not patch["content"].strip():
        raise ValueError("Todo patch content cannot be empty")

    if "status" in patch and patch["status"] not in _ALLOWED_STATUS:
        msg = f"Todo patch has invalid status '{patch['status']}'"
        raise ValueError(msg)

    if "priority" in patch and patch["priority"] not in _ALLOWED_PRIORITY:
        msg = f"Todo patch has invalid priority '{patch['priority']}'"
        raise ValueError(msg)


def validate_unique_ids(todos: list[TodoItem]) -> None:
    ids = [todo["id"] for todo in todos]
    duplicates = sorted({todo_id for todo_id in ids if ids.count(todo_id) > 1})
    if duplicates:
        msg = f"Duplicate todo id(s): {', '.join(duplicates)}"
        raise ValueError(msg)


def replace_todos(todos: list[TodoItem]) -> list[TodoItem]:
    for index, item in enumerate(todos):
        validate_todo_item(item, index)

    validate_unique_ids(todos)
    set_todos(todos)
    return todos


def add_todos(todos: list[TodoItem]) -> list[TodoItem]:
    current = get_todos()
    for index, item in enumerate(todos):
        validate_todo_item(item, index)

    used_ids = {item["id"] for item in current}
    normalized_new_todos: list[TodoItem] = []
    for item in todos:
        normalized_id = _next_available_id(item["id"], used_ids)
        normalized_item: TodoItem = {
            "id": normalized_id,
            "content": item["content"],
            "status": item["status"],
            "priority": item["priority"],
        }
        used_ids.add(normalized_id)
        normalized_new_todos.append(normalized_item)

    updated = [*current, *normalized_new_todos]
    validate_unique_ids(updated)
    set_todos(updated)
    return updated


def _next_available_id(base_id: str, used_ids: set[str]) -> str:
    if base_id not in used_ids:
        return base_id

    index = 2
    while True:
        candidate = f"{base_id}-{index}"
        if candidate not in used_ids:
            return candidate
        index += 1


def update_todo(todo_id: str, patch: TodoPatch) -> TodoUpdateResult:
    validate_todo_patch(patch)

    current = get_todos()
    updated: list[TodoItem] = []
    before_item: TodoItem | None = None
    after_item: TodoItem | None = None
    found = False

    for item in current:
        if item["id"] != todo_id:
            updated.append(item)
            continue

        found = True
        before_item = {
            "id": item["id"],
            "content": item["content"],
            "status": item["status"],
            "priority": item["priority"],
        }
        next_item: TodoItem = {
            "id": item["id"],
            "content": patch.get("content", item["content"]),
            "status": patch.get("status", item["status"]),
            "priority": patch.get("priority", item["priority"]),
        }
        validate_todo_item(next_item, 0)
        after_item = next_item
        updated.append(next_item)

    if not found:
        msg = f"Todo with id '{todo_id}' not found"
        raise ValueError(msg)

    set_todos(updated)
    if before_item is None or after_item is None:
        msg = f"Todo with id '{todo_id}' not found"
        raise ValueError(msg)

    return {
        "before": before_item,
        "after": after_item,
        "todos": updated,
    }


def delete_todos(ids: list[str]) -> list[TodoItem]:
    if not ids:
        raise ValueError("No todo ids provided")

    empty_ids = [todo_id for todo_id in ids if not todo_id.strip()]
    if empty_ids:
        raise ValueError("Todo ids cannot be empty")

    unique_ids = {todo_id for todo_id in ids}
    current = get_todos()
    current_ids = {item["id"] for item in current}
    missing = sorted(unique_ids - current_ids)
    if missing:
        msg = f"Todo id(s) not found: {', '.join(missing)}"
        raise ValueError(msg)

    updated = [item for item in current if item["id"] not in unique_ids]
    set_todos(updated)
    return updated
