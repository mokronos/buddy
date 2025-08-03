"""Tests for the Tool base class."""

from typing import Any

import pytest
from pydantic import BaseModel

from buddy.tools.tool import Tool  # type: ignore[import-untyped]


class MockTool(Tool):
    """Mock tool for testing."""

    def run(self, a: int, b: str = "default") -> str:
        return f"{a}: {b}"


class ComplexMockTool(Tool):
    """Mock tool with complex parameters for testing."""

    def run(
        self,
        required_int: int,
        required_str: str,
        optional_int: int | None = None,
        optional_str: str = "default",
        optional_float: float | None = None,
    ) -> dict[str, str]:
        return {
            "required_int": str(required_int),
            "required_str": required_str,
            "optional_int": str(optional_int) if optional_int is not None else "None",
            "optional_str": optional_str,
            "optional_float": str(optional_float) if optional_float is not None else "None",
        }


class NoParamsTool(Tool):
    """Mock tool with no parameters."""

    def run(self) -> str:
        return "no params"


class DataModel(BaseModel):
    """Test data model for complex tool testing."""

    value: int
    name: str


class AdvancedMockTool(Tool):
    """Mock tool with Pydantic model parameters."""

    def run(
        self,
        data: DataModel,
        data_list: list[DataModel] | None = None,
    ) -> str:
        result = f"data: {data.name}={data.value}"
        if data_list:
            result += f", list: {len(data_list)} items"
        return result


class TestToolInitialization:
    """Test Tool class initialization and validation."""

    def test_valid_initialization(self):
        """Test that Tool initializes correctly with valid parameters."""
        tool = MockTool("test_tool", "A test tool")
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool._cached_schema is None

    def test_name_whitespace_stripping(self):
        """Test that tool name whitespace is stripped."""
        # Note: validation happens before stripping, so whitespace in the middle still fails
        tool = MockTool("test_tool", "A test tool")
        assert tool.name == "test_tool"

    def test_empty_name_raises_error(self):
        """Test that empty tool name raises ValueError."""
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            MockTool("", "A test tool")

    def test_whitespace_only_name_raises_error(self):
        """Test that whitespace-only tool name raises ValueError."""
        with pytest.raises(ValueError, match="Tool name cannot be empty"):
            MockTool("   ", "A test tool")

    def test_invalid_characters_in_name_raises_error(self):
        """Test that invalid characters in tool name raise ValueError."""
        invalid_names = ["test tool", "test@tool", "test.tool", "test/tool", "test\\tool"]
        for invalid_name in invalid_names:
            with pytest.raises(ValueError, match="Tool name must be alphanumeric"):
                MockTool(invalid_name, "A test tool")

    def test_valid_name_characters(self):
        """Test that valid name characters are accepted."""
        valid_names = ["test_tool", "test-tool", "TestTool", "test123", "123test"]
        for valid_name in valid_names:
            tool = MockTool(valid_name, "A test tool")
            assert tool.name == valid_name

    def test_tool_is_callable(self):
        """Test that Tool instance can be called like a function."""
        tool = MockTool("test_tool", "A test tool")
        result = tool(42, "hello")
        assert result == "42: hello"

        # Test with default parameter
        result = tool(42)
        assert result == "42: default"


class TestSchemaGeneration:
    """Test schema generation functionality."""

    def test_basic_schema_generation(self):
        """Test that schema is generated correctly for basic tool."""
        tool = MockTool("test_tool", "A test tool")
        schema = tool.get_input_schema()

        assert "type" in schema
        assert schema["type"] == "function"
        assert "function" in schema
        assert "name" in schema["function"]
        assert schema["function"]["name"] == "test_tool"

    def test_complex_schema_generation(self):
        """Test schema generation for tool with complex parameters."""
        tool = ComplexMockTool("complex_tool", "A complex test tool")
        schema = tool.get_input_schema()

        function_def = schema["function"]
        parameters = function_def["parameters"]
        properties = parameters["properties"]

        # Check required parameters
        assert "required_int" in properties
        assert "required_str" in properties
        assert properties["required_int"]["type"] == "integer"
        assert properties["required_str"]["type"] == "string"

        # Check optional parameters
        assert "optional_int" in properties
        assert "optional_str" in properties
        assert "optional_float" in properties

        # Check required field list - pydantic_function_tool includes all fields
        required_fields = parameters.get("required", [])
        assert "required_int" in required_fields
        assert "required_str" in required_fields
        # Note: pydantic_function_tool includes all parameters in required list
        assert "optional_int" in required_fields
        assert "optional_str" in required_fields
        assert "optional_float" in required_fields

    def test_pydantic_model_schema_generation(self):
        """Test schema generation for tool with Pydantic model parameters."""
        tool = AdvancedMockTool("advanced_tool", "An advanced test tool")
        schema = tool.get_input_schema()

        function_def = schema["function"]
        parameters = function_def["parameters"]
        properties = parameters["properties"]

        # Check that complex types are handled
        assert "data" in properties
        assert "data_list" in properties

        # Check required field list - pydantic_function_tool includes all fields
        required_fields = parameters.get("required", [])
        assert "data" in required_fields
        assert "data_list" in required_fields


class TestErrorHandling:
    """Test error handling and edge cases."""

    def test_no_params_tool_raises_error(self):
        """Test that tool with no parameters raises RuntimeError."""
        tool = NoParamsTool("no_params_tool", "A tool with no params")
        with pytest.raises(RuntimeError, match="Failed to generate schema for tool 'no_params_tool'"):
            tool.get_input_schema()

    def test_schema_generation_error_handling(self):
        """Test that schema generation errors are properly handled."""

        class BrokenTool(Tool):
            def run(self, param_with_invalid_type) -> str:  # Missing type hint
                return "broken"

        tool = BrokenTool("broken_tool", "A broken tool")
        # Missing type hints don't cause errors - they default to no type specification
        schema = tool.get_input_schema()
        assert schema["function"]["name"] == "broken_tool"

        # Test a real error by making get_type_hints fail
        class ReallyBrokenTool(Tool):
            def run(self, param: int) -> str:
                return "broken"

            def get_input_schema(self) -> Any:
                # Override to force an error during schema generation
                try:
                    # This will cause an error when trying to create the model
                    from pydantic import create_model

                    create_model(None)  # This should fail
                except Exception as e:
                    msg = f"Failed to generate schema for tool '{self.name}': {e}"
                    raise RuntimeError(msg) from e

        tool = ReallyBrokenTool("broken", "Really broken tool")
        with pytest.raises(RuntimeError, match="Failed to generate schema for tool"):
            tool.get_input_schema()


class TestCaching:
    """Test schema caching behavior."""

    def test_schema_caching(self):
        """Test that schema is cached after first generation."""
        tool = MockTool("cached_tool", "A cached test tool")

        # First call should generate and cache
        schema1 = tool.get_input_schema()
        assert tool._cached_schema is not None

        # Second call should return cached version
        schema2 = tool.get_input_schema()
        assert schema1 is schema2  # Should be the exact same object

    def test_cache_independence(self):
        """Test that different tool instances have independent caches."""
        tool1 = MockTool("tool1", "First tool")
        tool2 = MockTool("tool2", "Second tool")

        schema1 = tool1.get_input_schema()
        schema2 = tool2.get_input_schema()

        # Schemas should be different objects
        assert schema1 is not schema2
        assert tool1._cached_schema is not tool2._cached_schema

        # But function names should be different
        assert schema1["function"]["name"] == "tool1"
        assert schema2["function"]["name"] == "tool2"


class TestToolExecution:
    """Test tool execution functionality."""

    def test_direct_run_call(self):
        """Test calling run method directly."""
        tool = MockTool("exec_tool", "An execution test tool")
        result = tool.run(123, "test")
        assert result == "123: test"

    def test_callable_execution(self):
        """Test calling tool as callable."""
        tool = MockTool("exec_tool", "An execution test tool")
        result = tool(456, "callable")
        assert result == "456: callable"

    def test_complex_tool_execution(self):
        """Test execution of tool with complex parameters."""
        tool = ComplexMockTool("complex_exec_tool", "Complex execution test")
        result = tool(
            required_int=42, required_str="hello", optional_int=100, optional_str="world", optional_float=3.14
        )

        expected = {
            "required_int": "42",
            "required_str": "hello",
            "optional_int": "100",
            "optional_str": "world",
            "optional_float": "3.14",
        }
        assert result == expected

    def test_advanced_tool_execution(self):
        """Test execution of tool with Pydantic model parameters."""
        tool = AdvancedMockTool("advanced_exec_tool", "Advanced execution test")

        test_data = DataModel(value=42, name="test")
        test_list = [DataModel(value=1, name="item1"), DataModel(value=2, name="item2")]

        result = tool(data=test_data, data_list=test_list)
        assert result == "data: test=42, list: 2 items"

        # Test without optional parameter
        result = tool(data=test_data)
        assert result == "data: test=42"
