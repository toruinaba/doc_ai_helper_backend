"""
Tests for the function calling utility functions.
"""

import pytest
import json
from typing import Dict, Any

from doc_ai_helper_backend.services.llm.functions import (
    FunctionRegistry,
    FunctionCallManager,
    validate_function_call_arguments,
    execute_function_safely,
)
from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
    ToolCall,
    ToolChoice,
)


class TestFunctionRegistry:
    """Tests for the FunctionRegistry."""

    def test_register_function(self):
        """Test registering a function."""
        registry = FunctionRegistry()

        def sample_function(param1: str, param2: int = 10) -> str:
            """A sample function for testing."""
            return f"Result: {param1}, {param2}"

        registry.register_function(
            name="sample_function",
            function=sample_function,
            description="A test function",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string", "description": "First parameter"},
                    "param2": {
                        "type": "integer",
                        "description": "Second parameter",
                        "default": 10,
                    },
                },
                "required": ["param1"],
            },
        )

        # Check function is registered
        assert "sample_function" in [
            f.name for f in registry.get_all_function_definitions()
        ]

        # Check function definition
        definition = registry.get_function_definition("sample_function")
        assert definition.name == "sample_function"
        assert definition.description == "A test function"

        # Check function exists
        func = registry.get_function("sample_function")
        assert func is not None

    def test_get_function_definitions(self):
        """Test getting function definitions."""
        registry = FunctionRegistry()

        def func1():
            return "func1"

        def func2():
            return "func2"

        registry.register_function("func1", func1, "Function 1")
        registry.register_function("func2", func2, "Function 2")

        definitions = registry.get_all_function_definitions()
        assert len(definitions) == 2
        assert all(isinstance(d, FunctionDefinition) for d in definitions)

        names = [d.name for d in definitions]
        assert "func1" in names
        assert "func2" in names

    def test_unregister_function(self):
        """Test unregistering a function."""
        registry = FunctionRegistry()

        def sample_function():
            return "test"

        registry.register_function("sample_function", sample_function)
        assert registry.get_function("sample_function") is not None

        registry.unregister_function("sample_function")
        assert registry.get_function("sample_function") is None

    def test_get_nonexistent_function(self):
        """Test getting a non-existent function."""
        registry = FunctionRegistry()

        assert registry.get_function("nonexistent") is None


class TestFunctionRegistryAdvanced:
    """Advanced tests for FunctionRegistry."""

    def test_register_function_overwrite(self):
        """Test overwriting an existing function."""
        registry = FunctionRegistry()

        def original_function():
            return "original"

        def new_function():
            return "new"

        # Register original function
        registry.register_function("test_func", original_function, "Original function")

        # Register new function with same name (should overwrite)
        registry.register_function("test_func", new_function, "New function")

        functions = registry.get_all_functions()
        assert functions["test_func"] == new_function

        definitions = registry.get_all_function_definitions()
        assert len(definitions) == 1
        assert definitions[0].description == "New function"

    def test_get_function_definition_not_found(self):
        """Test getting non-existent function definition."""
        registry = FunctionRegistry()

        definition = registry.get_function_definition("nonexistent")
        assert definition is None

    def test_get_function_not_found(self):
        """Test getting non-existent function."""
        registry = FunctionRegistry()

        function = registry.get_function("nonexistent")
        assert function is None

    def test_clear_registry(self):
        """Test clearing the registry."""
        registry = FunctionRegistry()

        def test_func():
            return "test"

        registry.register_function("test_func", test_func, "Test function")
        assert len(registry.get_all_functions()) == 1

        registry.clear()
        assert len(registry.get_all_functions()) == 0
        assert len(registry.get_all_function_definitions()) == 0

    def test_register_function_with_complex_parameters(self):
        """Test registering function with complex parameter schema."""
        registry = FunctionRegistry()

        def complex_function(
            required_str: str, optional_int: int = 42, nested_obj: Dict[str, Any] = None
        ):
            return f"Result: {required_str}, {optional_int}, {nested_obj}"

        complex_parameters = {
            "type": "object",
            "properties": {
                "required_str": {
                    "type": "string",
                    "description": "A required string parameter",
                },
                "optional_int": {
                    "type": "integer",
                    "description": "An optional integer parameter",
                    "default": 42,
                    "minimum": 0,
                    "maximum": 100,
                },
                "nested_obj": {
                    "type": "object",
                    "description": "A nested object parameter",
                    "properties": {
                        "key1": {"type": "string"},
                        "key2": {"type": "number"},
                    },
                    "additionalProperties": False,
                },
            },
            "required": ["required_str"],
            "additionalProperties": False,
        }

        registry.register_function(
            name="complex_function",
            function=complex_function,
            description="A function with complex parameters",
            parameters=complex_parameters,
        )

        definition = registry.get_function_definition("complex_function")
        assert definition is not None
        assert definition.parameters == complex_parameters
        assert "nested_obj" in definition.parameters["properties"]


class TestFunctionCallManager:
    """Tests for FunctionCallManager."""

    def test_manager_initialization(self):
        """Test manager initialization."""
        manager = FunctionCallManager()
        assert manager.function_registry is not None

        # Test with custom registry
        custom_registry = FunctionRegistry()
        manager_with_registry = FunctionCallManager(custom_registry)
        assert manager_with_registry.function_registry is custom_registry

    def test_register_function_through_manager(self):
        """Test registering function through manager."""
        manager = FunctionCallManager()

        def test_func():
            return "test"

        manager.register_function("test_func", test_func, "Test function")

        available_functions = manager.get_available_functions()
        assert len(available_functions) == 1
        assert available_functions[0].name == "test_func"


class TestFunctionCallManagerAdvanced:
    """Advanced tests for FunctionCallManager."""

    @pytest.fixture
    def manager_with_functions(self):
        """Create a manager with pre-registered functions."""
        manager = FunctionCallManager()

        def add_numbers(a: int, b: int) -> int:
            """Add two numbers."""
            return a + b

        def concatenate_strings(str1: str, str2: str = "") -> str:
            """Concatenate two strings."""
            return str1 + str2

        def divide_numbers(a: float, b: float) -> float:
            """Divide two numbers."""
            if b == 0:
                raise ValueError("Division by zero")
            return a / b

        manager.function_registry.register_function(
            "add_numbers",
            add_numbers,
            "Add two numbers",
            {
                "type": "object",
                "properties": {"a": {"type": "integer"}, "b": {"type": "integer"}},
                "required": ["a", "b"],
            },
        )

        manager.function_registry.register_function(
            "concatenate_strings",
            concatenate_strings,
            "Concatenate strings",
            {
                "type": "object",
                "properties": {
                    "str1": {"type": "string"},
                    "str2": {"type": "string", "default": ""},
                },
                "required": ["str1"],
            },
        )

        manager.function_registry.register_function(
            "divide_numbers",
            divide_numbers,
            "Divide two numbers",
            {
                "type": "object",
                "properties": {"a": {"type": "number"}, "b": {"type": "number"}},
                "required": ["a", "b"],
            },
        )

        return manager

    async def test_execute_function_call_success(self, manager_with_functions):
        """Test successful function call execution."""
        function_call = FunctionCall(name="add_numbers", arguments='{"a": 5, "b": 3}')

        result = await manager_with_functions.execute_function_call(function_call)

        assert result["success"] is True
        assert result["result"] == 8
        assert result["error"] is None  # Check for None rather than absence

    async def test_execute_function_call_function_not_found(
        self, manager_with_functions
    ):
        """Test function call with non-existent function."""
        function_call = FunctionCall(
            name="nonexistent_function", arguments='{"param": "value"}'
        )

        result = await manager_with_functions.execute_function_call(function_call)

        assert result["success"] is False
        assert "not found" in result["error"]
        assert result["result"] is None

    async def test_execute_function_call_invalid_json(self, manager_with_functions):
        """Test function call with invalid JSON arguments."""
        function_call = FunctionCall(
            name="add_numbers", arguments='{"a": 5, "b": invalid_json}'
        )

        result = await manager_with_functions.execute_function_call(function_call)

        assert result["success"] is False
        assert (
            "JSON" in result["error"] or "arguments" in result["error"]
        )  # More flexible check
        assert result["result"] is None

    async def test_execute_function_call_invalid_arguments(
        self, manager_with_functions
    ):
        """Test function call with invalid arguments."""
        function_call = FunctionCall(
            name="add_numbers", arguments='{"a": "not_a_number", "b": 3}'
        )

        result = await manager_with_functions.execute_function_call(function_call)

        assert result["success"] is False
        assert "Invalid arguments" in result["error"]
        assert result["result"] is None

    async def test_execute_function_call_function_error(self, manager_with_functions):
        """Test function call that raises an exception."""
        function_call = FunctionCall(
            name="divide_numbers", arguments='{"a": 10, "b": 0}'
        )

        result = await manager_with_functions.execute_function_call(function_call)

        assert result["success"] is False
        assert "Division by zero" in result["error"]
        assert result["result"] is None

    async def test_execute_function_call_with_optional_params(
        self, manager_with_functions
    ):
        """Test function call with optional parameters."""
        # Test with optional parameter provided
        function_call = FunctionCall(
            name="concatenate_strings", arguments='{"str1": "Hello", "str2": " World"}'
        )

        result = await manager_with_functions.execute_function_call(function_call)

        assert result["success"] is True
        assert result["result"] == "Hello World"

        # Test with optional parameter omitted
        function_call = FunctionCall(
            name="concatenate_strings", arguments='{"str1": "Hello"}'
        )

        result = await manager_with_functions.execute_function_call(function_call)

        assert result["success"] is True
        assert result["result"] == "Hello"

    def test_get_available_functions(self, manager_with_functions):
        """Test getting available functions."""
        functions = manager_with_functions.get_available_functions()

        assert len(functions) == 3
        function_names = [f.name for f in functions]
        assert "add_numbers" in function_names
        assert "concatenate_strings" in function_names
        assert "divide_numbers" in function_names

    def test_register_function_convenience_method(self):
        """Test registering function using manager's convenience method."""
        manager = FunctionCallManager()

        def test_function(param: str) -> str:
            return f"Test: {param}"

        manager.register_function(
            "test_function",
            test_function,
            "Test function",
            {
                "type": "object",
                "properties": {"param": {"type": "string"}},
                "required": ["param"],
            },
        )

        functions = manager.get_available_functions()
        assert len(functions) == 1
        assert functions[0].name == "test_function"

    @pytest.mark.asyncio
    async def test_execute_function_call_with_invalid_json_arguments(
        self, manager_with_functions
    ):
        """無効なJSON引数でのファンクションコール実行テスト"""
        from doc_ai_helper_backend.models.llm import FunctionCall

        function_call = FunctionCall(
            name="add_numbers",  # 存在する関数を使用
            arguments="invalid json { incomplete",  # 無効なJSON
        )

        result = await manager_with_functions.execute_function_call(function_call)
        assert result["success"] is False
        assert "Invalid JSON" in result["error"]
        assert result["result"] is None

    @pytest.mark.asyncio
    async def test_execute_function_call_with_execution_error(
        self, manager_with_functions
    ):
        """ファンクション実行時のエラーハンドリングテスト"""
        from doc_ai_helper_backend.models.llm import FunctionCall

        # エラーを発生させる関数を登録
        def error_function(message: str = "test") -> str:
            raise ValueError("Test execution error")

        manager_with_functions.function_registry.register_function(
            "error_function",
            error_function,
            "Test error function",
            {
                "type": "object",
                "properties": {"message": {"type": "string"}},
                "required": [],
            },
        )

        function_call = FunctionCall(
            name="error_function", arguments='{"message": "test"}'
        )

        result = await manager_with_functions.execute_function_call(function_call)
        assert result["success"] is False
        assert "Execution error" in result["error"]
        assert "Test execution error" in result["error"]
        assert result["result"] is None

    @pytest.mark.asyncio
    async def test_execute_tool_calls_with_empty_list(self, manager_with_functions):
        """空のツールコールリストでの実行テスト"""
        from doc_ai_helper_backend.models.llm import ToolCall, FunctionCall

        # 空のリストをテスト
        results = await manager_with_functions.execute_tool_calls([])
        # 空のリストは空の結果を返す
        assert len(results) == 0

    @pytest.mark.asyncio
    async def test_execute_tool_calls_with_multiple_tools(self, manager_with_functions):
        """複数のツールコール実行テスト"""
        from doc_ai_helper_backend.models.llm import ToolCall, FunctionCall

        # テスト用関数を登録
        def test_function_1(**kwargs):
            return {"message": "function_1_result"}

        def test_function_2(**kwargs):
            return {"message": "function_2_result"}

        manager_with_functions.function_registry.register_function(
            "test_function_1", test_function_1, "Test function 1", {}
        )
        manager_with_functions.function_registry.register_function(
            "test_function_2", test_function_2, "Test function 2", {}
        )

        tool_calls = [
            ToolCall(
                id="test_tool_1",
                type="function",
                function=FunctionCall(name="test_function_1", arguments="{}"),
            ),
            ToolCall(
                id="test_tool_2",
                type="function",
                function=FunctionCall(name="test_function_2", arguments="{}"),
            ),
        ]

        results = await manager_with_functions.execute_tool_calls(tool_calls)
        assert len(results) == 2
        assert results[0]["tool_call_id"] == "test_tool_1"
        assert results[1]["tool_call_id"] == "test_tool_2"
        assert results[0]["result"]["success"] is True
        assert results[1]["result"]["success"] is True


class TestValidateFunctionCallArguments:
    """Test the validate_function_call_arguments function."""

    def test_valid_arguments(self):
        """Test validation with valid arguments."""
        function_call = FunctionCall(
            name="test_function", arguments='{"param1": "value1", "param2": 42}'
        )

        function_def = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"},
                },
                "required": ["param1", "param2"],
            },
        )

        result = validate_function_call_arguments(function_call, function_def)
        assert result is True

    def test_missing_required_parameter(self):
        """Test validation with missing required parameter."""
        function_call = FunctionCall(
            name="test_function", arguments='{"param1": "value1"}'
        )

        function_def = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"},
                },
                "required": ["param1", "param2"],
            },
        )

        result = validate_function_call_arguments(function_call, function_def)
        assert result is False

    def test_invalid_json_arguments(self):
        """Test validation with invalid JSON."""
        function_call = FunctionCall(
            name="test_function", arguments='{"param1": invalid_json}'
        )

        function_def = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        result = validate_function_call_arguments(function_call, function_def)
        assert result is False

    def test_extra_parameters_allowed(self):
        """Test validation with extra parameters (should NOT be allowed based on implementation)."""
        function_call = FunctionCall(
            name="test_function",
            arguments='{"param1": "value1", "extra_param": "extra_value"}',
        )

        function_def = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={
                "type": "object",
                "properties": {"param1": {"type": "string"}},
                "required": ["param1"],
            },
        )

        result = validate_function_call_arguments(function_call, function_def)
        assert (
            result is False
        )  # Extra parameters are not allowed based on implementation

    def test_optional_parameters(self):
        """Test validation with optional parameters."""
        function_call = FunctionCall(
            name="test_function", arguments='{"param1": "value1"}'
        )

        function_def = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer", "default": 10},
                },
                "required": ["param1"],
            },
        )

        result = validate_function_call_arguments(function_call, function_def)
        assert result is True


class TestExecuteFunctionSafely:
    """Test the execute_function_safely function."""

    def test_successful_execution(self):
        """Test successful function execution."""

        def add_function(a: int, b: int) -> int:
            return a + b

        functions = {"add_function": add_function}
        arguments = {"a": 5, "b": 3}

        result = execute_function_safely("add_function", arguments, functions)

        assert result["success"] is True
        assert result["result"] == 8
        assert result["error"] is None  # Check for None rather than absence

    def test_function_not_found(self):
        """Test execution with non-existent function."""
        functions = {}
        arguments = {"param": "value"}

        result = execute_function_safely("nonexistent", arguments, functions)

        assert result["success"] is False
        assert "not found" in result["error"]
        assert result["result"] is None

    def test_function_raises_exception(self):
        """Test execution when function raises an exception."""

        def error_function():
            raise ValueError("Test error message")

        functions = {"error_function": error_function}
        arguments = {}

        result = execute_function_safely("error_function", arguments, functions)

        assert result["success"] is False
        assert "Test error message" in result["error"]
        assert result["result"] is None

    def test_function_with_keyword_arguments(self):
        """Test execution with keyword arguments."""

        def keyword_function(name: str, age: int = 25, city: str = "Unknown") -> str:
            return f"{name} is {age} years old and lives in {city}"

        functions = {"keyword_function": keyword_function}
        arguments = {"name": "Alice", "age": 30, "city": "New York"}

        result = execute_function_safely("keyword_function", arguments, functions)

        assert result["success"] is True
        assert "Alice is 30 years old and lives in New York" in result["result"]

    def test_function_with_no_arguments(self):
        """Test execution of function that takes no arguments."""

        def no_args_function() -> str:
            return "No arguments needed"

        functions = {"no_args_function": no_args_function}
        arguments = {}

        result = execute_function_safely("no_args_function", arguments, functions)

        assert result["success"] is True
        assert result["result"] == "No arguments needed"

    def test_function_returns_complex_data(self):
        """Test execution of function that returns complex data."""

        def complex_function(data: str) -> Dict[str, Any]:
            return {
                "input": data,
                "length": len(data),
                "processed": True,
                "metadata": {"timestamp": "2023-01-01", "version": "1.0"},
            }

        functions = {"complex_function": complex_function}
        arguments = {"data": "test input"}

        result = execute_function_safely("complex_function", arguments, functions)

        assert result["success"] is True
        assert isinstance(result["result"], dict)
        assert result["result"]["input"] == "test input"
        assert result["result"]["length"] == 10
        assert result["result"]["processed"] is True


class TestFunctionManagerIntegration:
    """Integration tests for function management components."""

    def test_full_workflow(self):
        """Test the complete workflow from registration to execution."""
        # Create a new manager
        manager = FunctionCallManager()

        # Register a function
        def calculate_area(length: float, width: float) -> float:
            """Calculate the area of a rectangle."""
            return length * width

        manager.register_function(
            name="calculate_area",
            function=calculate_area,
            description="Calculate the area of a rectangle",
            parameters={
                "type": "object",
                "properties": {
                    "length": {"type": "number", "description": "Length of rectangle"},
                    "width": {"type": "number", "description": "Width of rectangle"},
                },
                "required": ["length", "width"],
            },
        )

        # Verify registration
        available_functions = manager.get_available_functions()
        assert len(available_functions) == 1
        assert available_functions[0].name == "calculate_area"

        # Create and execute a function call
        function_call = FunctionCall(
            name="calculate_area", arguments='{"length": 5.0, "width": 3.0}'
        )

        # Execute the function call
        import asyncio

        result = asyncio.run(manager.execute_function_call(function_call))

        assert result["success"] is True
        assert result["result"] == 15.0

    def test_multiple_functions_management(self):
        """Test managing multiple functions."""
        manager = FunctionCallManager()

        # Register multiple functions
        def func1(x: int) -> int:
            return x * 2

        def func2(s: str) -> str:
            return s.upper()

        def func3(a: list) -> int:
            return len(a)

        functions = [
            ("double", func1, "Double a number"),
            ("uppercase", func2, "Convert to uppercase"),
            ("count_items", func3, "Count items in list"),
        ]

        for name, func, desc in functions:
            manager.register_function(name, func, desc)

        # Verify all functions are registered
        available = manager.get_available_functions()
        assert len(available) == 3

        function_names = [f.name for f in available]
        assert "double" in function_names
        assert "uppercase" in function_names
        assert "count_items" in function_names
