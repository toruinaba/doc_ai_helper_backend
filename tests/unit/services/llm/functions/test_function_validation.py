"""
Tests for function validation utilities.
"""

import pytest
from doc_ai_helper_backend.services.llm.functions.function_validation import (
    validate_function_call_arguments,
)
from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
)


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
