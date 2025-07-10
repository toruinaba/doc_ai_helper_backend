"""
Tests for function utility functions.
"""

import pytest
from typing import Dict, Any
from doc_ai_helper_backend.services.llm.functions.function_validation import (
    execute_function_safely,
)


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
