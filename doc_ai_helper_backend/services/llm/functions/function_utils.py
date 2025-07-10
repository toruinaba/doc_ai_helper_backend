"""
Function Utils (Function Utils)

LLMサービス向けのFunction Callingユーティリティを提供します。

主要機能:
- OpenAI tools形式への変換
- Tool callsのパース処理
- ユーティリティ関数定義の提供
"""

import logging
from typing import Dict, Any, List, Optional

from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
    ToolCall,
)

logger = logging.getLogger(__name__)


def convert_function_definition_to_openai_tool(
    function_def: FunctionDefinition,
) -> Dict[str, Any]:
    """
    FunctionDefinitionをOpenAI tools形式に変換する。

    Args:
        function_def: 変換する関数定義

    Returns:
        Dict[str, Any]: OpenAI tools形式の辞書
    """
    return {
        "type": "function",
        "function": {
            "name": function_def.name,
            "description": function_def.description or "",
            "parameters": function_def.parameters
            or {"type": "object", "properties": {}},
        },
    }


def parse_openai_tool_calls(tool_calls: List[Any]) -> List[ToolCall]:
    """
    OpenAI APIからのtool callsをToolCallモデルに変換する。

    Args:
        tool_calls: OpenAI APIからのtool calls

    Returns:
        List[ToolCall]: 変換されたToolCallのリスト
    """
    result = []
    for tool_call in tool_calls:
        if hasattr(tool_call, "function"):
            function_call = FunctionCall(
                name=tool_call.function.name, arguments=tool_call.function.arguments
            )
            result.append(
                ToolCall(id=tool_call.id, type="function", function=function_call)
            )

    return result


def get_utility_functions() -> List[FunctionDefinition]:
    """
    Get the list of utility function definitions for LLM function calling.

    Returns:
        List[FunctionDefinition]: List of utility function definitions
    """
    return [
        FunctionDefinition(
            name="get_current_time",
            description="Get the current date and time in the specified timezone and format. Use this when users ask about the current time, date, or want to know what time it is.",
            parameters={
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone to use (UTC, JST, EST, etc.)",
                        "default": "UTC",
                    },
                    "format": {
                        "type": "string",
                        "description": "Output format (ISO, readable, timestamp)",
                        "enum": ["ISO", "readable", "timestamp"],
                        "default": "ISO",
                    },
                },
                "required": [],
            },
        ),
        FunctionDefinition(
            name="count_text_characters",
            description="Count characters in the provided text with various counting options. Use this when users want to analyze text length, word count, or character statistics.",
            parameters={
                "type": "object",
                "properties": {
                    "text": {"type": "string", "description": "The text to analyze"},
                    "count_type": {
                        "type": "string",
                        "description": "Type of counting",
                        "enum": ["all", "no_spaces", "alphanumeric", "words", "lines"],
                        "default": "all",
                    },
                },
                "required": ["text"],
            },
        ),
        FunctionDefinition(
            name="validate_email_format",
            description="Validate if the provided string is a valid email format. Use this when users want to check if an email address is properly formatted.",
            parameters={
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to validate",
                    }
                },
                "required": ["email"],
            },
        ),
        FunctionDefinition(
            name="generate_random_data",
            description="Generate random data for testing purposes. Use this when users need sample data, random strings, numbers, or test data.",
            parameters={
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to generate",
                        "enum": ["string", "number", "uuid", "password"],
                        "default": "string",
                    },
                    "length": {
                        "type": "integer",
                        "description": "Length of generated data",
                        "minimum": 1,
                        "maximum": 100,
                        "default": 10,
                    },
                },
                "required": [],
            },
        ),
        FunctionDefinition(
            name="calculate_simple_math",
            description="Calculate simple mathematical expressions safely. Use this when users want to perform calculations or evaluate mathematical expressions.",
            parameters={
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2+3*4', '(10-5)*2')",
                    }
                },
                "required": ["expression"],
            },
        ),
    ]
