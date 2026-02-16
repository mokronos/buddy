from buddy.tools.todo_store import TodoItem, TodoPatch, update_todo


def todoupdate(id: str, patch: TodoPatch) -> list[TodoItem]:
    """Update fields of an existing todo by id.

    Args:
        id: Todo id to update.
        patch: Partial update for content, status, and/or priority.

    Returns:
        The updated todo list.
    """
    return update_todo(id, patch)
