"""
Adapter to integrate FastMCP server with LLM Function Calling.

This module provides integration between the FastMCP server and the
existing Function Calling mechanism in LLM services.
"""

import json
import logging
from typing import Any, Callable, Dict, List, Optional

from doc_ai_helper_backend.models.llm import (
    FunctionDefinition,
    FunctionCall,
    ToolCall,
)
from doc_ai_helper_backend.services.llm.function_manager import FunctionRegistry
from .server import DocumentAIHelperMCPServer

logger = logging.getLogger(__name__)


class MCPFunctionAdapter:
    """
    Adapter to integrate MCP server tools with LLM Function Calling.
    """

    def __init__(self, mcp_server: DocumentAIHelperMCPServer):
        """
        Initialize the adapter.

        Args:
            mcp_server: The MCP server instance
        """
        self.mcp_server = mcp_server
        self.function_registry = FunctionRegistry()
        self._register_mcp_tools()

    def _register_mcp_tools(self):
        """Register MCP tools as function calling functions."""
        available_tools = self.mcp_server.get_available_tools()

        for tool_name in available_tools:
            # MCPツールをFunction Calling関数として登録
            self._register_mcp_tool_as_function(tool_name)

        logger.info(f"Registered {len(available_tools)} MCP tools as functions")

    def _register_mcp_tool_as_function(self, tool_name: str):
        """
        Register a single MCP tool as a function calling function.

        Args:
            tool_name: Name of the MCP tool
        """

        async def mcp_tool_wrapper(**kwargs) -> Dict[str, Any]:
            """Wrapper function to call MCP tool."""
            try:
                result = await self.mcp_server.call_tool(tool_name, **kwargs)
                return {"success": True, "result": result, "error": None}
            except Exception as e:
                logger.error(f"Error calling MCP tool '{tool_name}': {e}")
                return {"success": False, "result": None, "error": str(e)}

        # ツールのメタデータを取得
        tool_info = self._get_tool_info(tool_name)

        # Function Callingの関数として登録
        self.function_registry.register_function(
            name=tool_name,
            function=mcp_tool_wrapper,
            description=tool_info.get("description", f"MCP tool: {tool_name}"),
            parameters=tool_info.get(
                "parameters", {"type": "object", "properties": {}, "required": []}
            ),
        )

    def _get_tool_info(self, tool_name: str) -> Dict[str, Any]:
        """
        Get information about an MCP tool.

        Args:
            tool_name: Name of the tool

        Returns:
            Dict containing tool information
        """
        # MCPツールの詳細情報を取得
        # FastMCPから実際のツール情報を取得する実装
        if (
            hasattr(self.mcp_server.app, "_tools")
            and tool_name in self.mcp_server.app._tools
        ):
            tool_info = self.mcp_server.app._tools[tool_name]
            return {
                "description": tool_info.get("description", f"MCP tool: {tool_name}"),
                "parameters": self._generate_parameters_schema(tool_name),
            }

        # デフォルトの情報
        return {
            "description": f"MCP tool: {tool_name}",
            "parameters": {"type": "object", "properties": {}, "required": []},
        }

    def _generate_parameters_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        Generate JSON schema for tool parameters.

        Args:
            tool_name: Name of the tool

        Returns:
            JSON schema for the tool parameters
        """
        # ツール名に基づいてパラメータスキーマを生成
        if "document" in tool_name:
            if tool_name == "extract_document_context":
                return {
                    "type": "object",
                    "properties": {
                        "document_content": {
                            "type": "string",
                            "description": "Content of the document to extract context from",
                        },
                        "repository": {
                            "type": "string",
                            "description": "Repository name",
                        },
                        "path": {"type": "string", "description": "Document path"},
                    },
                    "required": ["document_content", "repository", "path"],
                }
            elif tool_name == "analyze_document_structure":
                return {
                    "type": "object",
                    "properties": {
                        "document_content": {
                            "type": "string",
                            "description": "Content of the document to analyze",
                        },
                        "document_type": {
                            "type": "string",
                            "description": "Type of document (e.g., markdown, html)",
                            "default": "markdown",
                        },
                    },
                    "required": ["document_content"],
                }
            elif tool_name == "optimize_document_content":
                return {
                    "type": "object",
                    "properties": {
                        "document_content": {
                            "type": "string",
                            "description": "Content of the document to optimize",
                        },
                        "optimization_type": {
                            "type": "string",
                            "description": "Type of optimization (readability, structure, etc.)",
                            "default": "readability",
                        },
                    },
                    "required": ["document_content"],
                }
            elif tool_name == "analyze_document_quality":
                return {
                    "type": "object",
                    "properties": {
                        "document_content": {
                            "type": "string",
                            "description": "Content of the document to analyze",
                        },
                        "quality_metrics": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of quality metrics to evaluate",
                        },
                    },
                    "required": ["document_content"],
                }
            elif tool_name == "extract_document_topics":
                return {
                    "type": "object",
                    "properties": {
                        "document_content": {
                            "type": "string",
                            "description": "Content of the document to extract topics from",
                        },
                        "topic_count": {
                            "type": "integer",
                            "description": "Number of topics to extract",
                            "default": 5,
                        },
                    },
                    "required": ["document_content"],
                }
            elif tool_name == "check_document_completeness":
                return {
                    "type": "object",
                    "properties": {
                        "document_content": {
                            "type": "string",
                            "description": "Content of the document to check",
                        },
                        "template_type": {
                            "type": "string",
                            "description": "Type of template to check against",
                            "default": "general",
                        },
                    },
                    "required": ["document_content"],
                }

        elif "feedback" in tool_name:
            if tool_name == "generate_feedback_from_conversation":
                return {
                    "type": "object",
                    "properties": {
                        "conversation_history": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "History of conversation messages",
                        },
                        "feedback_type": {
                            "type": "string",
                            "description": "Type of feedback to generate",
                            "default": "general",
                        },
                    },
                    "required": ["conversation_history"],
                }
            elif tool_name == "create_improvement_proposal":
                return {
                    "type": "object",
                    "properties": {
                        "current_content": {
                            "type": "string",
                            "description": "Current content to improve",
                        },
                        "feedback_data": {
                            "type": "object",
                            "description": "Feedback data to base improvements on",
                        },
                    },
                    "required": ["current_content", "feedback_data"],
                }
            elif tool_name == "analyze_conversation_patterns":
                return {
                    "type": "object",
                    "properties": {
                        "conversation_history": {
                            "type": "array",
                            "items": {"type": "object"},
                            "description": "History of conversation messages",
                        },
                        "analysis_depth": {
                            "type": "string",
                            "description": "Depth of analysis (basic, detailed, etc.)",
                            "default": "basic",
                        },
                    },
                    "required": ["conversation_history"],
                }

        # デフォルトスキーマ
        return {"type": "object", "properties": {}, "required": []}

    def get_function_registry(self) -> FunctionRegistry:
        """
        Get the function registry with MCP tools.

        Returns:
            FunctionRegistry instance with registered MCP tools
        """
        return self.function_registry

    async def execute_function_call(
        self, function_call: FunctionCall
    ) -> Dict[str, Any]:
        """
        Execute a function call through the function registry.

        Args:
            function_call: Function call to execute

        Returns:
            Execution result
        """
        function = self.function_registry.get_function(function_call.name)
        if not function:
            return {
                "success": False,
                "error": f"Function '{function_call.name}' not found",
                "result": None,
            }

        try:
            # 引数をパース
            arguments = json.loads(function_call.arguments)

            # 関数を実行
            result = await function(**arguments)
            return result

        except json.JSONDecodeError as e:
            return {
                "success": False,
                "error": f"Invalid JSON in function arguments: {str(e)}",
                "result": None,
            }
        except Exception as e:
            logger.error(f"Error executing function '{function_call.name}': {e}")
            return {"success": False, "error": str(e), "result": None}

    def get_available_functions(self) -> List[FunctionDefinition]:
        """
        Get all available function definitions.

        Returns:
            List of function definitions
        """
        return self.function_registry.get_all_function_definitions()
