"""
Tests for the function calling utility functions.
"""

import pytest
import json
from typing import Dict, Any

from doc_ai_helper_backend.services.llm.utils.functions import (
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
                    "param2": {"type": "integer", "description": "Second parameter", "default": 10}
                },
                "required": ["param1"]
            }
        )
        
        # Check function is registered
        assert "sample_function" in [f.name for f in registry.get_all_function_definitions()]
        
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


class TestFunctionCallValidation:
    """Tests for function call validation."""

    def test_validate_function_call_arguments_valid(self):
        """Test validating valid function call arguments."""
        function_call = FunctionCall(
            name="test_function",
            arguments='{"param1": "value1", "param2": 42}'
        )
        
        function_def = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={
                "type": "object",
                "properties": {
                    "param1": {"type": "string"},
                    "param2": {"type": "integer"}
                },
                "required": ["param1"]
            }
        )
        
        # Should not raise an exception
        result = validate_function_call_arguments(function_call, function_def)
        assert result is True

    def test_validate_function_call_arguments_invalid_json(self):
        """Test validating function call with invalid JSON."""
        function_call = FunctionCall(
            name="test_function",
            arguments='{"param1": "value1", "param2": }'  # Invalid JSON
        )
        
        function_def = FunctionDefinition(
            name="test_function",
            description="Test function",
            parameters={"type": "object", "properties": {}}
        )
        
        result = validate_function_call_arguments(function_call, function_def)
        assert result is False


class TestExecuteFunctionSafely:
    """Tests for safe function execution."""

    def test_execute_function_safely_success(self):
        """Test successful safe function execution."""
        def test_function(param1: str, param2: int) -> str:
            return f"Success: {param1}, {param2}"
        
        functions = {"test_function": test_function}
        arguments = {"param1": "hello", "param2": 42}
        
        result = execute_function_safely("test_function", arguments, functions)
        assert result["success"] is True
        assert result["result"] == "Success: hello, 42"
        # The function may include an error field set to None, which is acceptable
        if "error" in result:
            assert result["error"] is None

    def test_execute_function_safely_error(self):
        """Test safe function execution with error."""
        def failing_function():
            raise ValueError("Test error")
        
        functions = {"failing_function": failing_function}
        arguments = {}
        
        result = execute_function_safely("failing_function", arguments, functions)
        assert result["success"] is False
        assert "error" in result
        assert "Test error" in result["error"]

    def test_execute_function_safely_invalid_arguments(self):
        """Test safe function execution with invalid arguments."""
        def test_function(param1: str):
            return f"Result: {param1}"
        
        functions = {"test_function": test_function}
        arguments = {"wrong_param": "value"}  # Wrong parameter name
        
        result = execute_function_safely("test_function", arguments, functions)
        assert result["success"] is False
        assert "error" in result


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
