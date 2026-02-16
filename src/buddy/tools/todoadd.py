from buddy.tools.todo_store import TodoItem, add_todos


def todoadd(todos: list[TodoItem]) -> list[TodoItem]:
    """Add todo items to the current list.

    Args:
        todos: Todo items to append. Each item id must be unique.

    Returns:
        The updated todo list.
    """
    return add_todos(todos)
