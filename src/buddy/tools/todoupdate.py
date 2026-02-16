from buddy.tools.todo_store import TodoPatch, TodoUpdateResult, update_todo


def todoupdate(id: str, patch: TodoPatch) -> TodoUpdateResult:
    """Update fields of an existing todo by id.

    Args:
        id: Todo id to update.
        patch: Partial update for content, status, and/or priority.

    Returns:
        The updated item diff and latest todo list.
    """
    return update_todo(id, patch)
