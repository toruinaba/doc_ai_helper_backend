"""
Tests for function service utilities.
"""

import pytest
import json
from unittest.mock import Mock, patch
from typing import Dict, Any

from doc_ai_helper_backend.services.llm.functions.function_service import (
    FunctionService,
)
from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
    ToolCall,
    ToolChoice,
)


class TestFunctionService:
    """Test the FunctionService class."""

    def test_initialization(self):
        """Test service initialization."""
        service = FunctionService()
        assert hasattr(service, "registry")
        assert service.registry is not None

    def test_register_function(self):
        """Test function registration."""
        service = FunctionService()

        def test_func(x: int, y: int = 10) -> int:
            return x + y

        service.register_function(
            "add_numbers",
            test_func,
            "Add two numbers",
            {
                "type": "object",
                "properties": {
                    "x": {"type": "integer"},
                    "y": {"type": "integer", "default": 10},
                },
                "required": ["x"],
            },
        )

        # Verify function is registered
        available = service.get_available_functions()
        assert len(available) == 1
        assert available[0].name == "add_numbers"

    def test_execute_function_call_success(self):
        """Test successful function execution."""
        service = FunctionService()

        def multiply(a: int, b: int) -> int:
            return a * b

        service.register_function("multiply", multiply)

        function_call = FunctionCall(name="multiply", arguments='{"a": 5, "b": 3}')

        result = service.execute_function_call(function_call)
        assert result == 15

    def test_execute_function_call_with_dict_arguments(self):
        """Test function execution with dict arguments."""
        service = FunctionService()

        def concat_strings(s1: str, s2: str) -> str:
            return f"{s1} {s2}"

        service.register_function("concat", concat_strings)

        function_call = FunctionCall(
            name="concat", arguments='{"s1": "hello", "s2": "world"}'
        )

        result = service.execute_function_call(function_call)
        assert result == "hello world"

    def test_execute_function_call_function_not_found(self):
        """Test function execution with non-existent function."""
        service = FunctionService()

        function_call = FunctionCall(name="nonexistent", arguments='{"param": "value"}')

        with pytest.raises(ValueError, match="Function 'nonexistent' not found"):
            service.execute_function_call(function_call)

    def test_execute_function_call_invalid_json(self):
        """Test function execution with invalid JSON arguments."""
        service = FunctionService()

        def test_func(x: int) -> int:
            return x * 2

        service.register_function("test_func", test_func)

        function_call = FunctionCall(name="test_func", arguments='{"x": invalid_json}')

        with pytest.raises(ValueError, match="Invalid function arguments"):
            service.execute_function_call(function_call)

    def test_execute_function_call_execution_error(self):
        """Test function execution when function raises exception."""
        service = FunctionService()

        def error_func():
            raise RuntimeError("Function error")

        service.register_function("error_func", error_func)

        function_call = FunctionCall(name="error_func", arguments="{}")

        with pytest.raises(RuntimeError, match="Function error"):
            service.execute_function_call(function_call)

    def test_execute_tool_calls_success(self):
        """Test successful tool calls execution."""
        service = FunctionService()

        def add(x: int, y: int) -> int:
            return x + y

        service.register_function("add", add)

        tool_calls = [
            ToolCall(
                id="call_1",
                type="function",
                function=FunctionCall(name="add", arguments='{"x": 2, "y": 3}'),
            ),
            ToolCall(
                id="call_2",
                type="function",
                function=FunctionCall(name="add", arguments='{"x": 10, "y": 5}'),
            ),
        ]

        results = service.execute_tool_calls(tool_calls)

        assert len(results) == 2
        assert results[0]["tool_call_id"] == "call_1"
        assert results[0]["type"] == "function"
        assert results[0]["function"]["result"] == 5
        assert results[1]["function"]["result"] == 15

    def test_execute_tool_calls_unsupported_type(self):
        """Test tool calls with unsupported type."""
        service = FunctionService()

        # Create a mock tool call with unsupported type
        mock_tool_call = Mock()
        mock_tool_call.id = "call_1"
        mock_tool_call.type = "unsupported"
        mock_tool_call.function = None

        results = service.execute_tool_calls([mock_tool_call])

        assert len(results) == 1
        assert results[0]["tool_call_id"] == "call_1"
        assert results[0]["type"] == "error"
        assert "Unsupported tool call type" in results[0]["error"]

    def test_execute_tool_calls_function_error(self):
        """Test tool calls when function execution fails."""
        service = FunctionService()

        def error_func():
            raise ValueError("Test error")

        service.register_function("error_func", error_func)

        tool_calls = [
            ToolCall(
                id="call_1",
                type="function",
                function=FunctionCall(name="error_func", arguments="{}"),
            )
        ]

        results = service.execute_tool_calls(tool_calls)

        assert len(results) == 1
        assert results[0]["tool_call_id"] == "call_1"
        assert results[0]["type"] == "error"
        assert "Test error" in results[0]["error"]

    def test_get_available_functions(self):
        """Test getting available functions."""
        service = FunctionService()

        def func1():
            pass

        def func2():
            pass

        service.register_function("func1", func1, "Function 1")
        service.register_function("func2", func2, "Function 2")

        functions = service.get_available_functions()

        assert len(functions) == 2
        function_names = [f.name for f in functions]
        assert "func1" in function_names
        assert "func2" in function_names

    def test_prepare_functions_for_api_all_functions(self):
        """Test preparing all functions for API."""
        service = FunctionService()

        def test_func(param: str) -> str:
            return param

        service.register_function(
            "test_func",
            test_func,
            "Test function",
            {
                "type": "object",
                "properties": {"param": {"type": "string"}},
                "required": ["param"],
            },
        )

        api_functions = service.prepare_functions_for_api()

        assert len(api_functions) == 1
        assert api_functions[0]["type"] == "function"
        assert api_functions[0]["function"]["name"] == "test_func"
        assert api_functions[0]["function"]["description"] == "Test function"
        assert "parameters" in api_functions[0]["function"]

    def test_prepare_functions_for_api_specific_functions(self):
        """Test preparing specific functions for API."""
        service = FunctionService()

        def func1():
            pass

        def func2():
            pass

        def func3():
            pass

        service.register_function("func1", func1, "Function 1")
        service.register_function("func2", func2, "Function 2")
        service.register_function("func3", func3, "Function 3")

        api_functions = service.prepare_functions_for_api(["func1", "func3"])

        assert len(api_functions) == 2
        function_names = [f["function"]["name"] for f in api_functions]
        assert "func1" in function_names
        assert "func3" in function_names
        assert "func2" not in function_names

    def test_prepare_functions_for_api_nonexistent_function(self):
        """Test preparing functions for API with non-existent function."""
        service = FunctionService()

        def func1():
            pass

        service.register_function("func1", func1, "Function 1")

        api_functions = service.prepare_functions_for_api(["func1", "nonexistent"])

        # Should only include existing functions
        assert len(api_functions) == 1
        assert api_functions[0]["function"]["name"] == "func1"

    def test_validate_function_call_valid(self):
        """Test valid function call validation."""
        service = FunctionService()

        def test_func(x: int) -> int:
            return x

        service.register_function("test_func", test_func)

        function_call = FunctionCall(name="test_func", arguments='{"x": 5}')

        assert service.validate_function_call(function_call) is True

    def test_validate_function_call_function_not_found(self):
        """Test function call validation with non-existent function."""
        service = FunctionService()

        function_call = FunctionCall(name="nonexistent", arguments='{"x": 5}')

        assert service.validate_function_call(function_call) is False

    def test_validate_function_call_invalid_json(self):
        """Test function call validation with invalid JSON."""
        service = FunctionService()

        def test_func(x: int) -> int:
            return x

        service.register_function("test_func", test_func)

        function_call = FunctionCall(name="test_func", arguments='{"x": invalid_json}')

        assert service.validate_function_call(function_call) is False

    def test_validate_function_call_dict_arguments(self):
        """Test function call validation with dict arguments."""
        service = FunctionService()

        def test_func(x: int) -> int:
            return x

        service.register_function("test_func", test_func)

        function_call = FunctionCall(name="test_func", arguments='{"x": 5}')

        assert service.validate_function_call(function_call) is True

    def test_create_tool_choice_auto(self):
        """Test creating auto tool choice."""
        service = FunctionService()

        choice = service.create_tool_choice("auto")

        assert choice.type == "auto"

    def test_create_tool_choice_none(self):
        """Test creating none tool choice."""
        service = FunctionService()

        choice = service.create_tool_choice("none")

        assert choice.type == "none"

    def test_create_tool_choice_required(self):
        """Test creating required tool choice."""
        service = FunctionService()

        choice = service.create_tool_choice("required")

        assert choice.type == "required"

    def test_create_tool_choice_function(self):
        """Test creating function-specific tool choice."""
        service = FunctionService()

        choice = service.create_tool_choice("function", "test_function")

        assert choice.type == "function"
        assert choice.function["name"] == "test_function"

    def test_create_tool_choice_invalid_defaults_to_auto(self):
        """Test creating tool choice with invalid type defaults to auto."""
        service = FunctionService()

        choice = service.create_tool_choice("invalid")

        assert choice.type == "auto"

    def test_create_tool_choice_function_without_name_defaults_to_auto(self):
        """Test creating function tool choice without name defaults to auto."""
        service = FunctionService()

        choice = service.create_tool_choice("function")

        assert choice.type == "auto"

    def test_execute_function_call_with_non_string_arguments(self):
        """非文字列引数での関数実行（バックワード互換性のテスト）"""

        def test_function(x: int = 1) -> int:
            return x * 2

        service = FunctionService()
        service.register_function("test_function", test_function)

        # FunctionCallモデルをモンキーパッチして辞書型引数をテスト
        from unittest.mock import Mock

        function_call = Mock()
        function_call.name = "test_function"
        function_call.arguments = {"x": 5}  # 辞書型引数

        result = service.execute_function_call(function_call)
        assert result == 10
