import inspect
from abc import ABC, abstractmethod
from typing import Any, get_type_hints

from openai import pydantic_function_tool
from pydantic import create_model


def _raise_no_params_error(tool_name: str) -> None:
    """Raise error for tools with no valid parameters."""
    msg = f"Tool '{tool_name}' has no valid parameters"
    raise ValueError(msg)


class Tool(ABC):
    """Abstract base class for all tools in the agent system.

    Tools are functions that the agent can call to interact with external systems,
    perform computations, or gather information. Each tool automatically generates
    an OpenAI-compatible function schema from its run method's type hints.

    Example:
        class CalculatorTool(Tool):
            def run(self, a: int, b: int, operation: str = "add") -> int:
                if operation == "add":
                    return a + b
                elif operation == "multiply":
                    return a * b
                return 0

        tool = CalculatorTool("calculator", "Performs basic math operations")
        schema = tool.get_input_schema()  # Auto-generated from type hints
    """

    def __init__(self, name: str, description: str) -> None:
        """Initialize the tool with a name and description.

        Args:
            name: Unique identifier for the tool
            description: Human-readable description of what the tool does

        Raises:
            ValueError: If name is empty or contains invalid characters
        """
        if not name or not name.strip():
            msg = "Tool name cannot be empty"
            raise ValueError(msg)
        if not name.replace("_", "").replace("-", "").isalnum():
            msg = "Tool name must be alphanumeric with optional underscores or hyphens"
            raise ValueError(msg)

        self.name = name.strip()
        self.description = description
        self._cached_schema: Any = None

    def __call__(self, *args: Any, **kwargs: Any) -> Any:
        """Make the tool callable as a function."""
        return self.run(*args, **kwargs)

    @abstractmethod
    def run(self, *args: Any, **kwargs: Any) -> Any:
        """Execute the tool's functionality.

        This method must be implemented by subclasses. The method signature
        with type hints will be used to automatically generate the tool's
        input schema.

        Returns:
            The result of the tool execution
        """
        pass

    def get_input_schema(self) -> Any:
        """Generate OpenAI-compatible function schema from the run method.

        Uses inspect and type hints to automatically create a Pydantic model
        and convert it to an OpenAI function tool schema. Results are cached
        after first generation.

        Returns:
            OpenAI function tool schema

        Raises:
            ValueError: If the tool has no valid parameters
            RuntimeError: If schema generation fails for any reason
        """
        if self._cached_schema is not None:
            return self._cached_schema

        try:
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

            if not fields:
                _raise_no_params_error(self.name)

            model = create_model(self.name, **fields)  # type: ignore[call-overload]
            schema = pydantic_function_tool(model)
            self._cached_schema = schema
        except Exception as e:
            msg = f"Failed to generate schema for tool '{self.name}': {e}"
            raise RuntimeError(msg) from e
        else:
            return self._cached_schema
