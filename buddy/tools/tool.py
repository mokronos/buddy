import inspect
from abc import ABC, abstractmethod
from typing import Any, get_type_hints

from openai import pydantic_function_tool
from pydantic import BaseModel, create_model


class Tool(ABC):
    def __init__(self, name, description):
        self.name = name
        self.description = description

    def __call__(self, *args, **kwargs):
        return self.run(*args, **kwargs)

    @abstractmethod
    def run(self, *args, **kwargs):
        pass

    def get_input_schema(self):
        params = inspect.signature(self.run).parameters
        type_hints = get_type_hints(self.run)

        fields = {}

        for name, param in params.items():
            if name == "self":
                continue

            param_type = type_hints.get(name, Any)

            if param.default is inspect.Parameter.empty:
                fields[name] = (param_type, ...)
            else:
                fields[name] = (param_type, param.default)

        model = create_model(self.name, **fields)
        return pydantic_function_tool(model)


if __name__ == "__main__":

    class Apple(BaseModel):
        weight: int
        color: str
        shape: str

    class test_tool(BaseModel):
        a: int
        b: int
        c: str = "default"
        d: float | None = None
        e: int | None = None
        f: list[Apple] | None = None
        g: Apple | None = None

    class TestTool(Tool):
        def run(
            self,
            a: int,
            b: int,
            c: str = "default",
            d: float | None = None,
            e: int | None = None,
            f: list[Apple] | None = None,
            g: Apple | None = None,
        ):
            return a + b

    name = "test_tool"

    tool = TestTool(name, "Test Tool Description")

    infered = tool.get_input_schema()

    manual = pydantic_function_tool(test_tool)

    assert infered == manual
