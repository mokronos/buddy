from buddy.tools.todo_store import TodoItem, delete_todos


def tododelete(ids: list[str]) -> list[TodoItem]:
    """Delete todo items by id.

    Args:
        ids: Todo ids to remove.

    Returns:
        The updated todo list.
    """
    return delete_todos(ids)
