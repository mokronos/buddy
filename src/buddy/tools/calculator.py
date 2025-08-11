class CalculatorTool(Tool):
    """Tool to perform basic mathematical operations."""

    def __init__(self) -> None:
        super().__init__(name="calculator", description="Performs basic mathematical operations")

    def run(self, a: float, b: float, operation: str = "add") -> float:
        """Perform a mathematical operation on two numbers.

        Args:
            a: The first number
            b: The second number
            operation: The operation to perform (add, subtract, multiply, divide)

        Returns:
            The result of the mathematical operation
        """
        if operation == "add":
            return a + b
        elif operation == "subtract":
            return a - b
        elif operation == "multiply":
            return a * b
        elif operation == "divide":
            if b == 0:
                msg = "Cannot divide by zero"
                raise ValueError(msg)
            return a / b
        else:
            msg = f"Unknown operation: {operation}"
            raise ValueError(msg)
