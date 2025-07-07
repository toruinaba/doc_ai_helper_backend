"""
Tests for the FunctionRegistry class.
"""

import pytest
from typing import Dict, Any

from doc_ai_helper_backend.services.llm.functions.function_registry import (
    FunctionRegistry,
)
from doc_ai_helper_backend.models.llm import FunctionDefinition


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

    def test_list_functions(self):
        """Test listing all function names."""
        registry = FunctionRegistry()

        def func1():
            return "func1"

        def func2():
            return "func2"

        registry.register_function("func1", func1)
        registry.register_function("func2", func2)

        names = registry.list_functions()
        assert len(names) == 2
        assert "func1" in names
        assert "func2" in names

    def test_clear_functions(self):
        """Test clearing all functions."""
        registry = FunctionRegistry()

        def func1():
            return "func1"

        registry.register_function("func1", func1)
        assert len(registry.list_functions()) == 1

        registry.clear()
        assert len(registry.list_functions()) == 0

    def test_get_all_functions(self):
        """Test getting all functions dictionary."""
        registry = FunctionRegistry()

        def func1():
            return "func1"

        def func2():
            return "func2"

        registry.register_function("func1", func1)
        registry.register_function("func2", func2)

        all_functions = registry.get_all_functions()
        assert len(all_functions) == 2
        assert "func1" in all_functions
        assert "func2" in all_functions
        assert callable(all_functions["func1"])
        assert callable(all_functions["func2"])


class TestFunctionRegistryAdvanced:
    """Advanced tests for FunctionRegistry functionality."""

    def test_register_function_with_defaults(self):
        """Test registering a function with default parameters."""
        registry = FunctionRegistry()

        def func_with_defaults():
            return "test"

        registry.register_function("test_func", func_with_defaults)

        definition = registry.get_function_definition("test_func")
        assert definition.name == "test_func"
        assert definition.description == "Function test_func"
        assert definition.parameters == {
            "type": "object",
            "properties": {},
            "required": [],
        }

    def test_register_function_overwrites(self):
        """Test that re-registering a function overwrites the previous one."""
        registry = FunctionRegistry()

        def func1():
            return "func1"

        def func2():
            return "func2"

        registry.register_function("test_func", func1, "First function")
        registry.register_function("test_func", func2, "Second function")

        definition = registry.get_function_definition("test_func")
        assert definition.description == "Second function"

        func = registry.get_function("test_func")
        assert func() == "func2"

    def test_unregister_nonexistent_function(self):
        """Test unregistering a non-existent function."""
        registry = FunctionRegistry()

        result = registry.unregister_function("nonexistent")
        assert result is False

    def test_backward_compatibility_methods(self):
        """Test backward compatibility methods."""
        registry = FunctionRegistry()

        def test_func():
            return "test"

        registry.register_function("test_func", test_func)

        # Test get_all_function_definitions (backward compatibility)
        definitions = registry.get_all_function_definitions()
        assert len(definitions) == 1
        assert definitions[0].name == "test_func"
