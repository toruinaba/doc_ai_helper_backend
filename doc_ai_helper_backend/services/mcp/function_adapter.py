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
        self._tools_registered = False

    async def _ensure_tools_registered(self):
        """Ensure MCP tools are registered (lazy initialization)."""
        if not self._tools_registered:
            await self._register_mcp_tools()
            self._tools_registered = True

    async def _register_mcp_tools(self):
        """Register MCP tools as function calling functions."""
        available_tools = await self.mcp_server.get_available_tools_async()

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
        logger.debug(f"Getting tool info for: {tool_name}")

        # FastMCPアプリの属性を確認
        logger.debug(
            f"MCP server app has _tools: {hasattr(self.mcp_server.app, '_tools')}"
        )
        if hasattr(self.mcp_server.app, "_tools"):
            logger.debug(
                f"Tool {tool_name} in _tools: {tool_name in self.mcp_server.app._tools}"
            )
            logger.debug(
                f"Available tools: {list(self.mcp_server.app._tools.keys()) if hasattr(self.mcp_server.app, '_tools') else 'No _tools'}"
            )

        if (
            hasattr(self.mcp_server.app, "_tools")
            and tool_name in self.mcp_server.app._tools
        ):
            tool_info = self.mcp_server.app._tools[tool_name]
            logger.debug(
                f"Found tool info for {tool_name}, generating parameters schema"
            )
            parameters = self._generate_parameters_schema(tool_name)
            logger.debug(f"Generated parameters for {tool_name}: {parameters}")
            return {
                "description": tool_info.get("description", f"MCP tool: {tool_name}"),
                "parameters": parameters,
            }  # デフォルトの情報（パラメータスキーマも生成）
        logger.debug(
            f"Using default info for {tool_name}, generating parameters schema"
        )
        parameters = self._generate_parameters_schema(tool_name)
        logger.debug(f"Generated default parameters for {tool_name}: {parameters}")
        return {
            "description": f"MCP tool: {tool_name}",
            "parameters": parameters,
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

        elif "github" in tool_name:
            if tool_name == "create_github_issue":
                return {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Issue title",
                        },
                        "description": {
                            "type": "string",
                            "description": "Issue description/body",
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of label names to apply (optional)",
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of GitHub usernames to assign (optional)",
                        },
                        "github_token": {
                            "type": "string",
                            "description": "GitHub Personal Access Token (optional)",
                        },
                    },
                    "required": ["title", "description"],
                }
            elif tool_name == "create_github_pull_request":
                return {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Pull request title",
                        },
                        "description": {
                            "type": "string",
                            "description": "Pull request description",
                        },
                        "head_branch": {
                            "type": "string",
                            "description": "Source branch name",
                        },
                        "base_branch": {
                            "type": "string",
                            "description": "Base branch name",
                            "default": "main",
                        },
                        "github_token": {
                            "type": "string",
                            "description": "GitHub Personal Access Token (optional)",
                        },
                    },
                    "required": ["title", "description", "head_branch"],
                }
            elif tool_name == "check_github_repository_permissions":
                return {
                    "type": "object",
                    "properties": {
                        "repository": {
                            "type": "string",
                            "description": "Repository in 'owner/repo' format",
                        },
                        "github_token": {
                            "type": "string",
                            "description": "GitHub Personal Access Token (optional)",
                        },
                    },
                    "required": ["repository"],
                }
            elif tool_name == "create_github_issue_secure":
                return {
                    "type": "object",
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": "Issue title",
                        },
                        "description": {
                            "type": "string",
                            "description": "Issue description/body",
                        },
                        "labels": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of label names (optional)",
                        },
                        "assignees": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of GitHub usernames to assign (optional)",
                        },
                        "github_token": {
                            "type": "string",
                            "description": "GitHub Personal Access Token (optional)",
                        },
                    },
                    "required": ["title", "description"],
                }

        # ユーティリティツール
        elif tool_name == "calculate_simple_math":
            return {
                "type": "object",
                "properties": {
                    "expression": {
                        "type": "string",
                        "description": "Mathematical expression to evaluate (e.g., '2+3*4')",
                    },
                },
                "required": ["expression"],
            }
        elif tool_name == "get_current_time":
            return {
                "type": "object",
                "properties": {
                    "timezone": {
                        "type": "string",
                        "description": "Timezone (e.g., 'UTC', 'JST')",
                        "default": "UTC",
                    },
                    "format": {
                        "type": "string",
                        "description": "Time format (e.g., 'ISO', 'readable')",
                        "default": "ISO",
                    },
                },
                "required": [],
            }
        elif tool_name == "count_text_characters":
            return {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to count characters in",
                    },
                    "count_type": {
                        "type": "string",
                        "description": "Type of counting (all, letters, words, etc.)",
                        "default": "all",
                    },
                },
                "required": ["text"],
            }
        elif tool_name == "validate_email_format":
            return {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Email address to validate",
                    },
                },
                "required": ["email"],
            }
        elif tool_name == "generate_random_data":
            return {
                "type": "object",
                "properties": {
                    "data_type": {
                        "type": "string",
                        "description": "Type of data to generate (string, number, etc.)",
                        "default": "string",
                    },
                    "length": {
                        "type": "integer",
                        "description": "Length of generated data",
                        "default": 10,
                    },
                },
                "required": [],
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
            logger.info(
                f"Executing function '{function_call.name}' with arguments: {arguments}"
            )
            logger.info(f"Function type: {type(function)}")

            # 関数を実行
            import asyncio

            if asyncio.iscoroutinefunction(function):
                result = await function(**arguments)
            else:
                # 同期関数の場合
                result = function(**arguments)

            logger.info(f"Function execution result: {result}")
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

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """
        Get all available function definitions.

        Returns:
            List of function definitions
        """
        await self._ensure_tools_registered()
        return self.function_registry.get_all_function_definitions()

    def set_repository_context(self, repository_context: Optional[Dict[str, Any]]):
        """
        Set repository context for secure tools.

        Args:
            repository_context: Repository context dictionary
        """
        if hasattr(self.mcp_server, "set_repository_context"):
            self.mcp_server.set_repository_context(repository_context)
            logger.info("Repository context updated in MCP server")
        else:
            logger.warning("MCP server does not support repository context setting")
