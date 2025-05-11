from enum import Enum
from typing import Annotated
from langchain_core.tools import BaseTool
from pydantic import BaseModel

class Mode(Enum):
    ADD = "add"
    REMOVE = "remove"
    UPDATE = "update"
    VIEW = "view"

class PlannerInput(BaseModel):
    mode: Mode
    task: Annotated[str, "The task to add, remove, update or view"]
    index: Annotated[int, "The index of the task to remove or update"]


class Planner(BaseTool):
    name: str = "planner"
    description: str = "Add, remove, update or view your tasks or subtasks."
    args_schema: type[PlannerInput] = PlannerInput

    tasks: list = []

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)

        self.tasks = []

    def add_task(self, task: str) -> None:
        """Add a task to the planner."""
        self.tasks.append(task)

    def remove_task(self, index: int) -> None:
        """Remove a task from the planner."""
        self.tasks.pop(index)

    def update_task(self, index: int, task: str) -> None:
        """Update a task in the planner."""
        self.tasks[index] = task

    def view_tasks(self) -> str:
        """View the tasks in the planner."""
        tasks_str = "\n".join(f"{index + 1}. {task}" for index, task in enumerate(self.tasks))
        return "Tasks:\n" + tasks_str

    def _run(self, mode: Mode, task: Annotated[str, "The task to add, remove, update or view."], index: Annotated[int, "The index of the task to remove or update."]) -> str:

        match mode:
            case Mode.ADD:
                self.add_task(task)
                return f"Added task: {task}\n {self.view_tasks()}"
            case Mode.REMOVE:
                self.remove_task(index)
                return f"Removed task: {task}\n {self.view_tasks()}"
            case Mode.UPDATE:
                self.update_task(index, task)
                return f"Updated task: {task}\n {self.view_tasks()}"
            case Mode.VIEW:
                return self.view_tasks()
            case _:
                return "Invalid mode, use add, remove, update or view"
