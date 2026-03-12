from pydantic_ai import Tool


def calculator(a: float, b: float, operation: str = "add") -> float:
    """Perform a mathematical operation on two numbers."""
    if operation == "add":
        return a + b
    if operation == "subtract":
        return a - b
    if operation == "multiply":
        return a * b
    if operation == "divide":
        if b == 0:
            msg = "Cannot divide by zero"
            raise ValueError(msg)
        return a / b
    msg = f"Unknown operation: {operation}"
    raise ValueError(msg)


calculator_tool = Tool(
    calculator,
    name="calculator",
    description="Performs basic mathematical operations",
)
