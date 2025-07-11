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
from doc_ai_helper_backend.services.llm.utils import FunctionRegistry
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

        # 日本語の説明文を生成
        description = self._get_japanese_description(tool_name)

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
                "description": description,
                "parameters": parameters,
            }

        # デフォルトの情報（パラメータスキーマも生成）
        logger.debug(
            f"Using default info for {tool_name}, generating parameters schema"
        )
        logger.error(f"CLAUDE_DEBUG: About to call _generate_parameters_schema for {tool_name}")
        parameters = self._generate_parameters_schema(tool_name)
        logger.debug(f"CLAUDE_MODIFIED: Generated default parameters for {tool_name}: {parameters}")
        return {
            "description": description,
            "parameters": parameters,
        }

    def _get_japanese_description(self, tool_name: str) -> str:
        """
        Get English description for a tool.

        Args:
            tool_name: Name of the tool

        Returns:
            English description string
        """
        # Unified Git tools descriptions
        if tool_name == "create_git_issue":
            return "Create new issue in Git repository (supports GitHub, Forgejo and other Git services)"
        elif tool_name == "create_git_pull_request":
            return "Create new pull request in Git repository (supports GitHub, Forgejo and other Git services)"
        elif tool_name == "check_git_repository_permissions":
            return "Check Git repository access permissions (supports GitHub, Forgejo and other Git services)"

        # Document tools descriptions
        elif tool_name == "extract_document_context":
            return "Extract context information from documents"
        elif tool_name == "analyze_document_structure":
            return "Analyze document structure"
        elif tool_name == "optimize_document_content":
            return "Optimize document content"
        elif tool_name == "analyze_document_quality":
            return "Analyze document quality"
        elif tool_name == "extract_document_topics":
            return "Extract topics from documents"
        elif tool_name == "check_document_completeness":
            return "Check document completeness"

        # Feedback tools descriptions
        elif tool_name == "generate_feedback_from_conversation":
            return "Generate feedback from conversation history"
        elif tool_name == "create_improvement_proposal":
            return "Create improvement proposals"
        elif tool_name == "analyze_conversation_patterns":
            return "Analyze conversation patterns"
        
        # LLM-enhanced tools descriptions
        elif tool_name == "summarize_document_with_llm":
            return "Generate high-quality summaries of Japanese documents using internal LLM API. IMPORTANT: Always provide the document_content parameter with the actual document text (e.g., README.md content that is currently being viewed). If document_content is not provided, the tool will automatically retrieve it from the current repository context. Provides natural and readable Japanese summaries through specialized prompts."
        elif tool_name == "create_improvement_recommendations_with_llm":
            return "Create detailed improvement recommendations for Japanese documents through professional LLM analysis. IMPORTANT: Always provide the document_content parameter with the actual document text (e.g., README.md content that is currently being viewed). If document_content is not provided, the tool will automatically retrieve it from the current repository context. Provides prioritized improvement suggestions with implementation guidance in Japanese."

        # Legacy GitHub tools descriptions (for backward compatibility)
        elif tool_name == "create_github_issue":
            return "Create new issue in GitHub repository"
        elif tool_name == "create_github_pull_request":
            return "Create new pull request in GitHub repository"
        elif tool_name == "check_github_repository_permissions":
            return "Check GitHub repository access permissions"
        elif tool_name == "create_github_issue_secure":
            return "Create new issue in GitHub repository securely"

        # Utility tools descriptions
        elif tool_name == "calculate_simple_math":
            return "Execute simple mathematical calculations"
        elif tool_name == "get_current_time":
            return "Get current time"
        elif tool_name == "count_text_characters":
            return "Count text characters"
        elif tool_name == "validate_email_format":
            return "Validate email address format"
        elif tool_name == "generate_random_data":
            return "Generate random data"

        # Default (generated from English description)
        return f"MCP tool: {tool_name}"

    def _generate_parameters_schema(self, tool_name: str) -> Dict[str, Any]:
        """
        Generate JSON schema for tool parameters.

        Args:
            tool_name: Name of the tool

        Returns:
            JSON schema for the tool parameters
        """
        # ツール名に基づいてパラメータスキーマを生成
        logger.debug(f"_generate_parameters_schema called for tool: {tool_name}")

        # 統合Gitツール
        if tool_name == "create_git_issue":
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
                        "description": "List of usernames to assign (optional)",
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Git service type (github, forgejo, etc.) - optional",
                    },
                    "github_token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token (optional)",
                    },
                    "forgejo_token": {
                        "type": "string",
                        "description": "Forgejo access token (optional)",
                    },
                    "forgejo_username": {
                        "type": "string",
                        "description": "Forgejo username (optional)",
                    },
                    "forgejo_password": {
                        "type": "string",
                        "description": "Forgejo password (optional)",
                    },
                },
                "required": ["title", "description"],
            }
        elif tool_name == "create_git_pull_request":
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
                        "description": "Target branch name",
                        "default": "main",
                    },
                    "service_type": {
                        "type": "string",
                        "description": "Git service type (github, forgejo, etc.) - optional",
                    },
                    "github_token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token (optional)",
                    },
                    "forgejo_token": {
                        "type": "string",
                        "description": "Forgejo access token (optional)",
                    },
                    "forgejo_username": {
                        "type": "string",
                        "description": "Forgejo username (optional)",
                    },
                    "forgejo_password": {
                        "type": "string",
                        "description": "Forgejo password (optional)",
                    },
                },
                "required": ["title", "description", "head_branch"],
            }
        elif tool_name == "check_git_repository_permissions":
            return {
                "type": "object",
                "properties": {
                    "service_type": {
                        "type": "string",
                        "description": "Git service type (github, forgejo, etc.) - optional",
                    },
                    "github_token": {
                        "type": "string",
                        "description": "GitHub Personal Access Token (optional)",
                    },
                    "forgejo_token": {
                        "type": "string",
                        "description": "Forgejo access token (optional)",
                    },
                    "forgejo_username": {
                        "type": "string",
                        "description": "Forgejo username (optional)",
                    },
                    "forgejo_password": {
                        "type": "string",
                        "description": "Forgejo password (optional)",
                    },
                },
                "required": [],
            }

        # ドキュメントツール
        elif "document" in tool_name:
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
                        "improvement_type": {
                            "type": "string",
                            "description": "Type of improvement (structure, content, readability, etc.)",
                            "default": "general",
                        },
                        "priority": {
                            "type": "string",
                            "description": "Priority level (high, medium, low)",
                            "default": "medium",
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
        
        # LLM Enhanced Tools
        elif tool_name == "summarize_document_with_llm":
            logger.debug(f"Found summarize_document_with_llm in _generate_parameters_schema")
            return {
                "type": "object",
                "properties": {
                    "document_content": {
                        "type": "string",
                        "description": "REQUIRED: The actual Japanese document content to summarize (full text content). For example, if analyzing README.md, provide the entire README.md content text here. Do not leave this empty - always include the document text.",
                    },
                    "summary_length": {
                        "type": "string",
                        "description": "Summary length (brief=concise, detailed=detailed, comprehensive=comprehensive)",
                        "default": "comprehensive",
                    },
                    "focus_area": {
                        "type": "string",
                        "description": "Focus area (general=general, technical=technical, business=business)",
                        "default": "general",
                    },
                    "context": {
                        "type": "string",
                        "description": "Additional context (optional)",
                    },
                },
                "required": ["document_content"],
            }
        elif tool_name == "create_improvement_recommendations_with_llm":
            return {
                "type": "object",
                "properties": {
                    "document_content": {
                        "type": "string",
                        "description": "REQUIRED: The actual Japanese document content to analyze for improvements (full text content). For example, if analyzing README.md, provide the entire README.md content text here. Do not leave this empty - always include the document text.",
                    },
                    "summary_context": {
                        "type": "string",
                        "description": "Pre-analysis summary context (optional)",
                        "default": "",
                    },
                    "improvement_type": {
                        "type": "string",
                        "description": "Improvement type (structure=structure, content=content, readability=readability, comprehensive=comprehensive)",
                        "default": "comprehensive",
                    },
                    "target_audience": {
                        "type": "string",
                        "description": "Target audience (general=general, technical=technical, beginner=beginner, expert=expert)",
                        "default": "general",
                    },
                },
                "required": ["document_content"],
            }

        # Default schema
        return {"type": "object", "properties": {}, "required": []}

    def get_function_registry(self) -> FunctionRegistry:
        """
        Get the function registry with MCP tools.

        Returns:
            FunctionRegistry instance with registered MCP tools
        """
        return self.function_registry

    async def execute_function_call(
        self, function_call: FunctionCall, repository_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Execute a function call through the function registry.

        Args:
            function_call: Function call to execute
            repository_context: Repository context to inject into Git tools

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

            # Git関連ツールとLLM強化ツールの場合、直接渡されたrepository_contextを注入
            if function_call.name.startswith(("create_git_", "check_git_", "summarize_document_with_llm", "create_improvement_recommendations_with_llm")):
                if repository_context:
                    if "repository_context" not in arguments:
                        arguments["repository_context"] = repository_context
                        logger.info(
                            f"Direct-injected repository_context for {function_call.name}: {repository_context.get('owner')}/{repository_context.get('repo')}"
                        )
                    else:
                        logger.info(
                            f"Repository context already in arguments: {arguments['repository_context']}"
                        )
                    
                    # For LLM-enhanced tools, also try to auto-fill document_content if empty
                    if function_call.name in ["summarize_document_with_llm", "create_improvement_recommendations_with_llm"]:
                        if not arguments.get("document_content", "").strip():
                            try:
                                from doc_ai_helper_backend.services.git.factory import GitServiceFactory
                                
                                # Create git service
                                service_type = repository_context.get("service", "github")
                                git_service = GitServiceFactory.create(service_type)
                                
                                # Get document content
                                owner = repository_context.get("owner")
                                repo = repository_context.get("repo")
                                path = repository_context.get("current_path")
                                ref = repository_context.get("ref", "main")
                                
                                if owner and repo and path:
                                    document_content = await git_service.get_file_content(owner, repo, path, ref)
                                    arguments["document_content"] = document_content
                                    logger.info(f"Auto-filled document_content for {function_call.name} from {owner}/{repo}/{path}: {len(document_content)} chars")
                            except Exception as e:
                                logger.warning(f"Failed to auto-fill document_content for {function_call.name}: {e}")
                else:
                    logger.warning(f"No repository context provided for {function_call.name} operation")

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
        
        DEPRECATED: This method no longer sets global state. Repository context
        is now passed directly to execute_function_call to avoid concurrency issues.

        Args:
            repository_context: Repository context dictionary
        """
        # Log deprecation warning but take no action
        if repository_context:
            owner = repository_context.get("owner", "unknown")
            repo = repository_context.get("repo", "unknown")
            logger.warning(f"DEPRECATED: set_repository_context called for {owner}/{repo}. Use execute_function_call(repository_context=...) instead.")
        else:
            logger.warning("DEPRECATED: set_repository_context called with None. Use execute_function_call(repository_context=...) instead.")
