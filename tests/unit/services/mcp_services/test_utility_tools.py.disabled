"""
Test for MCP utility tools functionality.

This module contains unit tests for the utility tools used in MCP server.
"""

import pytest
import json
import re
from unittest.mock import AsyncMock, patch
from datetime import datetime

from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
    get_current_time,
    count_text_characters,
    validate_email_format,
    generate_random_data,
    calculate_simple_math,
    calculate,  # Alias
    format_text,
)


class TestUtilityTools:
    """Test the MCP utility tools functionality."""

    @pytest.mark.asyncio
    async def test_get_current_time_basic(self):
        """Test basic current time functionality."""
        result = await get_current_time()

        # Should return JSON string
        assert isinstance(result, str)

        # Parse and validate JSON structure
        time_data = json.loads(result)
        assert time_data["success"] is True
        assert "current_time" in time_data
        assert "timezone" in time_data
        assert "format" in time_data
        assert "timestamp" in time_data
        assert "iso_format" in time_data

        # Default values should be set
        assert time_data["timezone"] == "UTC"
        assert time_data["format"] == "ISO"

    @pytest.mark.asyncio
    async def test_get_current_time_different_formats(self):
        """Test current time with different formats."""
        formats = ["ISO", "readable", "timestamp", "custom"]

        for fmt in formats:
            result = await get_current_time(format=fmt)
            time_data = json.loads(result)

            assert time_data["success"] is True
            assert time_data["format"] == fmt
            assert "current_time" in time_data

    @pytest.mark.asyncio
    async def test_get_current_time_different_timezones(self):
        """Test current time with different timezones."""
        timezones = ["UTC", "JST", "EST"]

        for tz in timezones:
            result = await get_current_time(timezone=tz)
            time_data = json.loads(result)

            assert time_data["success"] is True
            assert time_data["timezone"] == tz

    @pytest.mark.asyncio
    async def test_count_text_characters_basic(self):
        """Test basic text character counting."""
        text = "Hello World! 123"

        result = await count_text_characters(text)

        # Should return JSON string
        assert isinstance(result, str)

        # Parse and validate JSON structure
        count_data = json.loads(result)
        assert count_data["success"] is True
        assert count_data["all_characters"] == len(text)
        assert count_data["words"] == 3  # "Hello", "World!", "123"
        assert count_data["lines"] == 1
        assert "analysis" in count_data

    @pytest.mark.asyncio
    async def test_count_text_characters_different_types(self):
        """Test text character counting with different count types."""
        text = "Hello World! 123\nSecond line"
        count_types = ["all", "no_spaces", "alphanumeric", "words", "lines"]

        for count_type in count_types:
            result = await count_text_characters(text, count_type)
            count_data = json.loads(result)

            assert count_data["success"] is True
            assert count_data["count_type"] == count_type
            assert "primary_count" in count_data

    @pytest.mark.asyncio
    async def test_count_text_characters_empty_text(self):
        """Test character counting with empty text."""
        result = await count_text_characters("")

        count_data = json.loads(result)
        assert count_data["success"] is True
        assert count_data["all_characters"] == 0
        assert count_data["words"] == 0
        assert count_data["lines"] == 0

    @pytest.mark.asyncio
    async def test_count_text_characters_japanese_text(self):
        """Test character counting with Japanese text."""
        text = "こんにちは世界！Hello World"

        result = await count_text_characters(text)
        count_data = json.loads(result)

        assert count_data["success"] is True
        assert count_data["analysis"]["has_japanese"] is True
        assert count_data["all_characters"] == len(text)

    @pytest.mark.asyncio
    async def test_validate_email_format_valid_emails(self):
        """Test email validation with valid email addresses."""
        valid_emails = [
            "test@example.com",
            "user.name@domain.co.jp",
            "user+tag@example.org",
            "123@456.com",
        ]

        for email in valid_emails:
            result = await validate_email_format(email)
            email_data = json.loads(result)

            assert email_data["success"] is True
            assert email_data["is_valid"] is True
            assert email_data["has_at_symbol"] is True
            assert email_data["has_domain"] is True

    @pytest.mark.asyncio
    async def test_validate_email_format_invalid_emails(self):
        """Test email validation with invalid email addresses."""
        invalid_emails = [
            "notanemail",
            "@example.com",
            "test@",
            "test.example.com",
            "test @example.com",  # Space
        ]

        for email in invalid_emails:
            result = await validate_email_format(email)
            email_data = json.loads(result)

            assert email_data["success"] is True
            assert email_data["is_valid"] is False

    @pytest.mark.asyncio
    async def test_validate_email_format_edge_cases(self):
        """Test email validation edge cases."""
        # Very long email
        long_email = "a" * 250 + "@example.com"
        result = await validate_email_format(long_email)
        email_data = json.loads(result)
        assert email_data["validation_details"]["length_ok"] is False

        # Email with spaces
        spaced_email = " test@example.com "
        result = await validate_email_format(spaced_email)
        email_data = json.loads(result)
        assert email_data["email"] == "test@example.com"  # Should be stripped

    @pytest.mark.asyncio
    async def test_generate_random_data_string(self):
        """Test random string generation."""
        result = await generate_random_data("string", 10)

        data = json.loads(result)
        assert data["success"] is True
        assert data["data_type"] == "string"
        assert data["length"] == 10
        assert len(data["generated_data"]) == 10

    @pytest.mark.asyncio
    async def test_generate_random_data_number(self):
        """Test random number generation."""
        result = await generate_random_data("number", 5)

        data = json.loads(result)
        assert data["success"] is True
        assert data["data_type"] == "number"
        assert isinstance(int(data["generated_data"]), int)

    @pytest.mark.asyncio
    async def test_generate_random_data_uuid(self):
        """Test UUID generation."""
        result = await generate_random_data("uuid")

        data = json.loads(result)
        assert data["success"] is True
        assert data["data_type"] == "uuid"
        # UUID format validation
        uuid_pattern = r"^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"
        assert re.match(uuid_pattern, data["generated_data"])

    @pytest.mark.asyncio
    async def test_generate_random_data_password(self):
        """Test password generation."""
        result = await generate_random_data("password", 12)

        data = json.loads(result)
        assert data["success"] is True
        assert data["data_type"] == "password"
        assert len(data["generated_data"]) == 12

    @pytest.mark.asyncio
    async def test_calculate_simple_math_basic(self):
        """Test basic mathematical calculations."""
        expressions = [
            ("2+3", 5),
            ("10-4", 6),
            ("3*4", 12),
            ("15/3", 5.0),
            ("2+3*4", 14),
            ("(2+3)*4", 20),
        ]

        for expression, expected in expressions:
            result = await calculate_simple_math(expression)
            calc_data = json.loads(result)

            assert calc_data["success"] is True
            assert calc_data["expression"] == expression
            assert calc_data["result"] == expected

    @pytest.mark.asyncio
    async def test_calculate_simple_math_alias(self):
        """Test mathematical calculation using alias function."""
        result = await calculate("5+5")
        calc_data = json.loads(result)

        assert calc_data["success"] is True
        assert calc_data["result"] == 10

    @pytest.mark.asyncio
    async def test_calculate_simple_math_invalid_expressions(self):
        """Test mathematical calculations with invalid expressions."""
        invalid_expressions = [
            "2+import",  # Prohibited keyword
            "2+eval(3)",  # Prohibited keyword
            "2+a",  # Invalid character
            "2+__builtins__",  # Prohibited keyword
        ]

        for expression in invalid_expressions:
            result = await calculate_simple_math(expression)
            calc_data = json.loads(result)

            assert calc_data["success"] is False
            assert "error" in calc_data

    @pytest.mark.asyncio
    async def test_calculate_simple_math_division_by_zero(self):
        """Test division by zero handling."""
        result = await calculate_simple_math("5/0")
        calc_data = json.loads(result)

        assert calc_data["success"] is False
        assert "error" in calc_data

    @pytest.mark.asyncio
    async def test_format_text_uppercase(self):
        """Test text formatting to uppercase."""
        text = "hello world"
        result = await format_text(text, "uppercase")

        format_data = json.loads(result)
        assert format_data["success"] is True
        assert format_data["formatted_text"] == "HELLO WORLD"
        assert format_data["style"] == "uppercase"

    @pytest.mark.asyncio
    async def test_format_text_different_styles(self):
        """Test text formatting with different styles."""
        text = "Hello World"
        styles = {
            "uppercase": "HELLO WORLD",
            "lowercase": "hello world",
            "title": "Hello World",
            "reverse": "dlroW olleH",
        }

        for style, expected in styles.items():
            result = await format_text(text, style)
            format_data = json.loads(result)

            assert format_data["success"] is True
            assert format_data["formatted_text"] == expected
            assert format_data["style"] == style

    @pytest.mark.asyncio
    async def test_format_text_unknown_style(self):
        """Test text formatting with unknown style."""
        text = "Hello World"
        result = await format_text(text, "unknown")

        format_data = json.loads(result)
        assert format_data["success"] is True
        assert format_data["formatted_text"] == text  # Should remain unchanged
        assert format_data["style"] == "unknown"

    @pytest.mark.asyncio
    async def test_format_text_empty_text(self):
        """Test text formatting with empty text."""
        result = await format_text("", "uppercase")

        format_data = json.loads(result)
        assert format_data["success"] is True
        assert format_data["formatted_text"] == ""
