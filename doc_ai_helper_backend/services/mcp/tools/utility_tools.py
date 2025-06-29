"""
Utility tools for MCP server.

This module provides simple utility functions for testing and demonstration
of MCP tool integration with frontend applications.
"""

import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
import json
import re

logger = logging.getLogger(__name__)


async def get_current_time(timezone: str = "UTC", format: str = "ISO") -> str:
    """
    Get the current date and time in the specified timezone and format.

    Args:
        timezone: Timezone to use (UTC, JST, EST, etc.)
        format: Output format (ISO, readable, timestamp)

    Returns:
        JSON string containing current time information
    """
    try:
        current_time = datetime.now()

        # Format the time based on the requested format
        if format.lower() == "iso":
            formatted_time = current_time.isoformat()
        elif format.lower() == "readable":
            formatted_time = current_time.strftime("%Y年%m月%d日 %H:%M:%S")
        elif format.lower() == "timestamp":
            formatted_time = str(int(current_time.timestamp()))
        else:
            formatted_time = current_time.strftime("%Y-%m-%d %H:%M:%S")

        result = {
            "success": True,
            "current_time": formatted_time,
            "timezone": timezone,
            "format": format,
            "timestamp": int(current_time.timestamp()),
            "iso_format": current_time.isoformat(),
        }

        logger.info(f"Current time requested: {formatted_time} ({timezone})")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to get current time: {str(e)}",
            "error_type": "time_error",
        }
        logger.error(f"Error getting current time: {str(e)}")
        return json.dumps(error_result)


async def count_text_characters(text: str, count_type: str = "all") -> str:
    """
    Count characters in the provided text with various counting options.

    Args:
        text: The text to analyze
        count_type: Type of counting (all, no_spaces, alphanumeric, words, lines)

    Returns:
        JSON string containing character count analysis
    """
    try:
        if not text:
            result = {
                "success": True,
                "text": "",
                "all_characters": 0,
                "no_spaces": 0,
                "alphanumeric": 0,
                "words": 0,
                "lines": 0,
                "count_type": count_type,
            }
            return json.dumps(result, ensure_ascii=False)

        # Various counting methods
        all_chars = len(text)
        no_spaces = len(text.replace(" ", "").replace("\t", "").replace("\n", ""))
        alphanumeric = len(re.sub(r"[^a-zA-Z0-9]", "", text))
        words = len(text.split())
        lines = len(text.splitlines())

        result = {
            "success": True,
            "text": (
                text[:100] + "..." if len(text) > 100 else text
            ),  # Truncate for display
            "all_characters": all_chars,
            "no_spaces": no_spaces,
            "alphanumeric": alphanumeric,
            "words": words,
            "lines": lines,
            "count_type": count_type,
            "analysis": {
                "has_japanese": bool(
                    re.search(r"[\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text)
                ),
                "has_numbers": bool(re.search(r"\d", text)),
                "has_special_chars": bool(
                    re.search(
                        r"[^a-zA-Z0-9\s\u3040-\u309F\u30A0-\u30FF\u4E00-\u9FAF]", text
                    )
                ),
            },
        }

        # Return specific count based on count_type
        if count_type == "no_spaces":
            result["primary_count"] = no_spaces
        elif count_type == "alphanumeric":
            result["primary_count"] = alphanumeric
        elif count_type == "words":
            result["primary_count"] = words
        elif count_type == "lines":
            result["primary_count"] = lines
        else:
            result["primary_count"] = all_chars

        logger.info(f"Text analysis completed: {all_chars} characters, {words} words")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to count characters: {str(e)}",
            "error_type": "text_analysis_error",
        }
        logger.error(f"Error counting characters: {str(e)}")
        return json.dumps(error_result)


async def validate_email_format(email: str) -> str:
    """
    Validate if the provided string is a valid email format.

    Args:
        email: Email address to validate

    Returns:
        JSON string containing validation result
    """
    try:
        # Simple email regex pattern
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        is_valid = bool(re.match(email_pattern, email.strip()))

        # Additional checks
        parts = email.strip().split("@")
        has_at_symbol = "@" in email
        has_domain = len(parts) == 2 and "." in parts[1] if has_at_symbol else False

        result = {
            "success": True,
            "email": email.strip(),
            "is_valid": is_valid,
            "has_at_symbol": has_at_symbol,
            "has_domain": has_domain,
            "local_part": parts[0] if has_at_symbol else "",
            "domain_part": parts[1] if has_at_symbol and len(parts) > 1 else "",
            "validation_details": {
                "length_ok": 5 <= len(email.strip()) <= 254,
                "no_spaces": " " not in email.strip(),
                "valid_characters": bool(
                    re.match(r"^[a-zA-Z0-9._%+-@]+$", email.strip())
                ),
            },
        }

        logger.info(f"Email validation: {email} -> {is_valid}")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to validate email: {str(e)}",
            "error_type": "validation_error",
        }
        logger.error(f"Error validating email: {str(e)}")
        return json.dumps(error_result)


async def generate_random_data(data_type: str = "string", length: int = 10) -> str:
    """
    Generate random data for testing purposes.

    Args:
        data_type: Type of data to generate (string, number, uuid, password)
        length: Length of generated data

    Returns:
        JSON string containing generated data
    """
    try:
        import random
        import string
        import uuid

        if data_type.lower() == "string":
            chars = string.ascii_letters + string.digits
            generated = "".join(random.choice(chars) for _ in range(length))
        elif data_type.lower() == "number":
            generated = random.randint(10 ** (length - 1), 10**length - 1)
        elif data_type.lower() == "uuid":
            generated = str(uuid.uuid4())
        elif data_type.lower() == "password":
            chars = string.ascii_letters + string.digits + "!@#$%^&*"
            generated = "".join(random.choice(chars) for _ in range(length))
        else:
            generated = "".join(
                random.choice(string.ascii_letters) for _ in range(length)
            )

        result = {
            "success": True,
            "data_type": data_type,
            "length": length,
            "generated_data": str(generated),
            "actual_length": len(str(generated)),
        }

        logger.info(f"Generated random {data_type}: {length} characters")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to generate random data: {str(e)}",
            "error_type": "generation_error",
        }
        logger.error(f"Error generating random data: {str(e)}")
        return json.dumps(error_result)


async def calculate_simple_math(expression: str) -> str:
    """
    Calculate simple mathematical expressions safely.

    Args:
        expression: Mathematical expression to evaluate (e.g., "2+3*4")

    Returns:
        JSON string containing calculation result
    """
    try:
        # Only allow safe mathematical operations
        allowed_chars = "0123456789+-*/.() "
        if not all(c in allowed_chars for c in expression):
            raise ValueError("Expression contains invalid characters")

        # Prevent potential security issues
        if any(word in expression.lower() for word in ["import", "eval", "exec", "__"]):
            raise ValueError("Expression contains prohibited keywords")

        # Calculate result
        result_value = eval(expression)

        result = {
            "success": True,
            "expression": expression,
            "result": result_value,
            "result_type": type(result_value).__name__,
            "is_integer": isinstance(result_value, int),
            "is_float": isinstance(result_value, float),
        }

        logger.info(f"Math calculation: {expression} = {result_value}")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to calculate expression: {str(e)}",
            "error_type": "calculation_error",
            "expression": expression,
        }
        logger.error(f"Error calculating expression '{expression}': {str(e)}")
        return json.dumps(error_result)


# エイリアスを作成（テストとの互換性のため）
calculate = calculate_simple_math


async def format_text(text: str, style: str = "uppercase") -> str:
    """
    Format text according to the specified style.

    Args:
        text: Text to format
        style: Formatting style (uppercase, lowercase, title, reverse)

    Returns:
        JSON string containing formatted text
    """
    try:
        if style.lower() == "uppercase":
            formatted_text = text.upper()
        elif style.lower() == "lowercase":
            formatted_text = text.lower()
        elif style.lower() == "title":
            formatted_text = text.title()
        elif style.lower() == "reverse":
            formatted_text = text[::-1]
        else:
            formatted_text = text

        result = {
            "success": True,
            "original_text": text,
            "formatted_text": formatted_text,
            "style": style,
        }

        logger.info(f"Text formatted: '{text}' -> '{formatted_text}' (style: {style})")
        return json.dumps(result, ensure_ascii=False)

    except Exception as e:
        error_result = {
            "success": False,
            "error": f"Failed to format text: {str(e)}",
            "error_type": "formatting_error",
            "original_text": text,
            "style": style,
        }
        logger.error(f"Error formatting text '{text}': {str(e)}")
        return json.dumps(error_result)
