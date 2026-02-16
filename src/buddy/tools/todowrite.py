from buddy.tools.todo_store import TodoItem, replace_todos


def todowrite(todos: list[TodoItem]) -> list[TodoItem]:
    """Create or replace the in-memory todo list.

    Args:
        todos: List of todo items with content, status, priority, and id.

    Returns:
        The updated todo list stored in memory.
    """
    return replace_todos(todos)
