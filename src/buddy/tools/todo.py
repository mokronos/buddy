from buddy.tools.todo_store import (
    TodoItem,
    TodoPatch,
    TodoUpdateResult,
    add_todos,
    delete_todos,
    get_todos,
    replace_todos,
    update_todo,
)


def todoread() -> list[TodoItem]:
    """Read the current in-memory todo list."""
    return get_todos()


def todoadd(todos: list[TodoItem]) -> list[TodoItem]:
    """Add todo items to the current list.

    Args:
        todos: Todo items to append. Each item id must be unique.

    Returns:
        The updated todo list.
    """
    return add_todos(todos)


def todoupdate(id: str, patch: TodoPatch) -> TodoUpdateResult:
    """Update fields of an existing todo by id.

    Args:
        id: Todo id to update.
        patch: Partial update for content, status, and/or priority.

    Returns:
        The updated item diff and latest todo list.
    """
    return update_todo(id, patch)


def tododelete(ids: list[str]) -> list[TodoItem]:
    """Delete todo items by id.

    Args:
        ids: Todo ids to remove.

    Returns:
        The updated todo list.
    """
    return delete_todos(ids)


def todowrite(todos: list[TodoItem]) -> list[TodoItem]:
    """Create or replace the in-memory todo list.

    Args:
        todos: List of todo items with content, status, priority, and id.

    Returns:
        The updated todo list stored in memory.
    """
    return replace_todos(todos)
