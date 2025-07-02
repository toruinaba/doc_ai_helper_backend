"""
FastMCP server for Document AI Helper.

This module provides the main MCP server implementation using FastMCP.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional

from fastmcp import FastMCP

from .config import MCPConfig, default_mcp_config

logger = logging.getLogger(__name__)


class DocumentAIHelperMCPServer:
    """Main MCP server for Document AI Helper using FastMCP."""

    def __init__(self, config: Optional[MCPConfig] = None):
        """
        Initialize the MCP server.

        Args:
            config: MCP configuration, uses default if None
        """
        self.config = config or default_mcp_config
        self.app = FastMCP(name=self.config.server_name)
        self._unified_git_tools = None
        self._setup_server()

    def _setup_server(self):
        """Set up the MCP server with tools and resources."""
        logger.info(f"Setting up MCP Server '{self.config.server_name}'")

        # Initialize unified Git tools
        self._setup_unified_git_tools()

        # Register tools based on configuration
        if self.config.enable_document_tools:
            self._register_document_tools()

        if self.config.enable_feedback_tools:
            self._register_feedback_tools()

        if self.config.enable_analysis_tools:
            self._register_analysis_tools()

        if self.config.enable_github_tools:
            self._register_git_tools()

        if self.config.enable_utility_tools:
            self._register_utility_tools()

        logger.info("MCP Server setup completed")

    def _register_document_tools(self):
        """Register document analysis tools using FastMCP decorators."""
        from .tools.document_tools import (
            extract_document_context,
            analyze_document_structure,
            optimize_document_content,
        )

        @self.app.tool("extract_document_context")
        async def extract_context_tool(
            document_content: str, context_type: str = "summary"
        ) -> Dict[str, Any]:
            """Extract structured context from document content."""
            return await extract_document_context(
                document_content=document_content, context_type=context_type
            )

        @self.app.tool("analyze_document_structure")
        async def analyze_structure_tool(
            document_content: str, analysis_depth: str = "basic"
        ) -> Dict[str, Any]:
            """Analyze document structure and organization."""
            return await analyze_document_structure(
                document_content=document_content, analysis_depth=analysis_depth
            )

        @self.app.tool("optimize_document_content")
        async def optimize_content_tool(
            document_content: str, optimization_type: str = "readability"
        ) -> Dict[str, Any]:
            """Optimize document content for better readability and structure."""
            return await optimize_document_content(
                document_content=document_content, optimization_type=optimization_type
            )

        logger.info("Document tools registered with FastMCP")

    def _register_feedback_tools(self):
        """Register feedback generation tools using FastMCP decorators."""
        from .tools.feedback_tools import (
            generate_feedback_from_conversation,
            create_improvement_proposal,
            analyze_conversation_patterns,
        )

        @self.app.tool("generate_feedback_from_conversation")
        async def generate_feedback_tool(
            conversation_history: List[Dict[str, Any]], feedback_type: str = "general"
        ) -> Dict[str, Any]:
            """Generate feedback from conversation history."""
            return await generate_feedback_from_conversation(
                conversation_history=conversation_history, feedback_type=feedback_type
            )

        @self.app.tool("create_improvement_proposal")
        async def create_proposal_tool(
            current_content: str, feedback_data: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Create improvement proposal based on feedback."""
            return await create_improvement_proposal(
                current_content=current_content, feedback_data=feedback_data
            )

        @self.app.tool("analyze_conversation_patterns")
        async def analyze_patterns_tool(
            conversation_history: List[Dict[str, Any]], analysis_depth: str = "basic"
        ) -> Dict[str, Any]:
            """Analyze conversation patterns and themes."""
            return await analyze_conversation_patterns(
                conversation_history=conversation_history, analysis_depth=analysis_depth
            )

        logger.info("Feedback tools registered with FastMCP")

    def _register_analysis_tools(self):
        """Register text analysis tools using FastMCP decorators."""
        from .tools.analysis_tools import (
            analyze_document_quality,
            extract_document_topics,
            check_document_completeness,
        )

        @self.app.tool("analyze_document_quality")
        async def analyze_quality_tool(
            document_content: str, quality_criteria: str = "general"
        ) -> Dict[str, Any]:
            """Analyze document quality against various criteria."""
            return await analyze_document_quality(
                document_content=document_content, quality_criteria=quality_criteria
            )

        @self.app.tool("extract_document_topics")
        async def extract_topics_tool(
            document_content: str, topic_count: int = 5
        ) -> Dict[str, Any]:
            """Extract main topics from document content."""
            return await extract_document_topics(
                document_content=document_content, topic_count=topic_count
            )

        @self.app.tool("check_document_completeness")
        async def check_completeness_tool(
            document_content: str, completeness_criteria: str = "general"
        ) -> Dict[str, Any]:
            """Check document completeness against criteria."""
            return await check_document_completeness(
                document_content=document_content,
                completeness_criteria=completeness_criteria,
            )

        logger.info("Analysis tools registered with FastMCP")

    def _setup_unified_git_tools(self):
        """Set up unified Git tools with configured services."""
        from .tools.git_tools import configure_git_service

        # Configure GitHub if enabled
        if self.config.enable_github_tools and (
            self.config.github_token or self.config.default_git_service == "github"
        ):
            try:
                configure_git_service(
                    "github",
                    config={
                        "access_token": self.config.github_token,
                        "default_labels": self.config.github_default_labels,
                    },
                    set_as_default=(self.config.default_git_service == "github"),
                )
                logger.info("Configured GitHub service for unified Git tools")
            except Exception as e:
                logger.warning(f"Failed to configure GitHub service: {str(e)}")

        # Configure Forgejo if configured
        if self.config.forgejo_base_url and (
            self.config.forgejo_token
            or (self.config.forgejo_username and self.config.forgejo_password)
        ):
            try:
                configure_git_service(
                    "forgejo",
                    config={
                        "base_url": self.config.forgejo_base_url,
                        "access_token": self.config.forgejo_token,
                        "username": self.config.forgejo_username,
                        "password": self.config.forgejo_password,
                        "default_labels": self.config.forgejo_default_labels,
                    },
                    set_as_default=(self.config.default_git_service == "forgejo"),
                )
                logger.info("Configured Forgejo service for unified Git tools")
            except Exception as e:
                logger.warning(f"Failed to configure Forgejo service: {str(e)}")

    def _register_git_tools(self):
        """Register unified Git tools using FastMCP decorators."""
        from .tools.git_tools import (
            create_git_issue,
            create_git_pull_request,
            check_git_repository_permissions,
        )

        @self.app.tool("create_git_issue")
        async def create_issue_tool(
            title: str,
            description: str,
            labels: Optional[List[str]] = None,
            assignees: Optional[List[str]] = None,
            service_type: Optional[str] = None,
            github_token: Optional[str] = None,
            forgejo_token: Optional[str] = None,
            forgejo_username: Optional[str] = None,
            forgejo_password: Optional[str] = None,
        ) -> str:
            """Create a new issue in the specified Git service."""
            # Get repository context from current session
            repository_context = getattr(self, "_current_repository_context", None)

            # Prepare service-specific kwargs
            kwargs = {}
            if github_token:
                kwargs["github_token"] = github_token
            if forgejo_token:
                kwargs["forgejo_token"] = forgejo_token
            if forgejo_username:
                kwargs["forgejo_username"] = forgejo_username
            if forgejo_password:
                kwargs["forgejo_password"] = forgejo_password

            return await create_git_issue(
                title=title,
                description=description,
                labels=labels,
                assignees=assignees,
                repository_context=repository_context,
                service_type=service_type,
                **kwargs,
            )

        @self.app.tool("create_git_pull_request")
        async def create_pr_tool(
            title: str,
            description: str,
            head_branch: str,
            base_branch: str = "main",
            service_type: Optional[str] = None,
            github_token: Optional[str] = None,
            forgejo_token: Optional[str] = None,
            forgejo_username: Optional[str] = None,
            forgejo_password: Optional[str] = None,
        ) -> str:
            """Create a new pull request in the specified Git service."""
            # Get repository context from current session
            repository_context = getattr(self, "_current_repository_context", None)

            # Prepare service-specific kwargs
            kwargs = {}
            if github_token:
                kwargs["github_token"] = github_token
            if forgejo_token:
                kwargs["forgejo_token"] = forgejo_token
            if forgejo_username:
                kwargs["forgejo_username"] = forgejo_username
            if forgejo_password:
                kwargs["forgejo_password"] = forgejo_password

            return await create_git_pull_request(
                title=title,
                description=description,
                head_branch=head_branch,
                base_branch=base_branch,
                repository_context=repository_context,
                service_type=service_type,
                **kwargs,
            )

        @self.app.tool("check_git_repository_permissions")
        async def check_permissions_tool(
            service_type: Optional[str] = None,
            github_token: Optional[str] = None,
            forgejo_token: Optional[str] = None,
            forgejo_username: Optional[str] = None,
            forgejo_password: Optional[str] = None,
        ) -> str:
            """Check permissions for the current repository context."""
            # Get repository context from current session
            repository_context = getattr(self, "_current_repository_context", None)

            # Prepare service-specific kwargs
            kwargs = {}
            if github_token:
                kwargs["github_token"] = github_token
            if forgejo_token:
                kwargs["forgejo_token"] = forgejo_token
            if forgejo_username:
                kwargs["forgejo_username"] = forgejo_username
            if forgejo_password:
                kwargs["forgejo_password"] = forgejo_password

            return await check_git_repository_permissions(
                repository_context=repository_context,
                service_type=service_type,
                **kwargs,
            )

        logger.info("Unified Git tools registered with FastMCP")

    def _register_utility_tools(self):
        """Register utility tools using FastMCP decorators."""
        from .tools.utility_tools import (
            get_current_time,
            count_text_characters,
            validate_email_format,
            generate_random_data,
            calculate_simple_math,
        )

        @self.app.tool("get_current_time")
        async def get_time_tool(timezone: str = "UTC", format: str = "ISO") -> str:
            """Get current time in specified timezone and format."""
            return await get_current_time(timezone=timezone, format=format)

        @self.app.tool("count_text_characters")
        async def count_chars_tool(text: str, count_type: str = "all") -> str:
            """Count characters in the provided text with various counting options."""
            return await count_text_characters(text=text, count_type=count_type)

        @self.app.tool("validate_email_format")
        async def validate_email_tool(email: str) -> str:
            """Validate if the provided string is a valid email format."""
            return await validate_email_format(email=email)

        @self.app.tool("generate_random_data")
        async def generate_random_tool(
            data_type: str = "string", length: int = 10
        ) -> str:
            """Generate random data for testing purposes."""
            return await generate_random_data(data_type=data_type, length=length)

        @self.app.tool("calculate_simple_math")
        async def calculate_math_tool(expression: str) -> str:
            """Calculate simple mathematical expressions safely."""
            return await calculate_simple_math(expression=expression)

        logger.info("Utility tools registered with FastMCP")

    def set_repository_context(self, repository_context: Optional[Dict[str, Any]]):
        """
        Set the current repository context for secure tools.

        Args:
            repository_context: Repository context from LLM request
        """
        self._current_repository_context = repository_context
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
            logger.info(f"Repository context set: {owner}/{repo}")
        else:
            logger.info("Repository context cleared")

    async def list_tools_async(self) -> List[Dict[str, Any]]:
        """List all available tools asynchronously."""
        tools_list = []
        try:
            tools = await self.app.get_tools()
            for tool_name, tool_info in tools.items():
                tools_list.append(
                    {
                        "name": tool_name,
                        "description": (
                            tool_info.description
                            if hasattr(tool_info, "description")
                            else f"Tool: {tool_name}"
                        ),
                        "enabled": True,
                    }
                )
        except Exception as e:
            logger.warning(f"Error listing tools: {e}")
        return tools_list

    def list_tools(self) -> List[Dict[str, Any]]:
        """List all available tools (synchronous wrapper)."""
        try:
            # Use asyncio to run async method in sync context
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If event loop is already running, return empty list as fallback
                    return []
                else:
                    return loop.run_until_complete(self.list_tools_async())
            except RuntimeError:
                return []
        except Exception as e:
            logger.warning(f"Failed to list tools: {e}")
            return []

    async def call_tool(self, tool_name: str, **kwargs) -> Any:
        """
        Call a specific tool by name using FastMCP.

        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool

        Returns:
            Result of the tool execution
        """
        try:
            # Direct tool invocation using function mapping
            if tool_name == "calculate_simple_math":
                from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
                    calculate_simple_math,
                )

                return await calculate_simple_math(**kwargs)
            elif tool_name == "extract_document_context":
                from doc_ai_helper_backend.services.mcp.tools.document_tools import (
                    extract_document_context,
                )

                return await extract_document_context(**kwargs)
            elif tool_name == "analyze_document_structure":
                from doc_ai_helper_backend.services.mcp.tools.document_tools import (
                    analyze_document_structure,
                )

                return await analyze_document_structure(**kwargs)
            elif tool_name == "optimize_document_content":
                from doc_ai_helper_backend.services.mcp.tools.document_tools import (
                    optimize_document_content,
                )

                return await optimize_document_content(**kwargs)
            elif tool_name == "generate_feedback_from_conversation":
                from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
                    generate_feedback_from_conversation,
                )

                return await generate_feedback_from_conversation(**kwargs)
            elif tool_name == "create_improvement_proposal":
                from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
                    create_improvement_proposal,
                )

                return await create_improvement_proposal(**kwargs)
            elif tool_name == "analyze_conversation_patterns":
                from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
                    analyze_conversation_patterns,
                )

                return await analyze_conversation_patterns(**kwargs)
            elif tool_name == "analyze_document_quality":
                from doc_ai_helper_backend.services.mcp.tools.analysis_tools import (
                    analyze_document_quality,
                )

                return await analyze_document_quality(**kwargs)
            elif tool_name == "extract_document_topics":
                from doc_ai_helper_backend.services.mcp.tools.analysis_tools import (
                    extract_document_topics,
                )

                return await extract_document_topics(**kwargs)
            elif tool_name == "check_document_completeness":
                from doc_ai_helper_backend.services.mcp.tools.analysis_tools import (
                    check_document_completeness,
                )

                return await check_document_completeness(**kwargs)
            elif tool_name == "create_git_issue":
                from doc_ai_helper_backend.services.mcp.tools.git_tools import (
                    create_git_issue,
                )

                return await create_git_issue(**kwargs)
            elif tool_name == "create_git_pull_request":
                from doc_ai_helper_backend.services.mcp.tools.git_tools import (
                    create_git_pull_request,
                )

                return await create_git_pull_request(**kwargs)
            elif tool_name == "check_git_repository_permissions":
                from doc_ai_helper_backend.services.mcp.tools.git_tools import (
                    check_git_repository_permissions,
                )

                return await check_git_repository_permissions(**kwargs)
            elif tool_name == "get_current_time":
                from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
                    get_current_time,
                )

                return await get_current_time(**kwargs)
            elif tool_name == "count_text_characters":
                from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
                    count_text_characters,
                )

                return await count_text_characters(**kwargs)
            elif tool_name == "validate_email_format":
                from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
                    validate_email_format,
                )

                return await validate_email_format(**kwargs)
            elif tool_name == "generate_random_data":
                from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
                    generate_random_data,
                )

                return await generate_random_data(**kwargs)
            else:
                raise ValueError(f"Unknown tool: {tool_name}")

        except Exception as e:
            logger.error(f"Error calling tool {tool_name}: {e}")
            return {"error": f"Failed to execute tool {tool_name}: {str(e)}"}

    async def get_available_tools_async(self) -> List[str]:
        """Get list of available tool names asynchronously."""
        try:
            tools = await self.app.get_tools()
            return list(tools.keys())
        except Exception as e:
            logger.warning(f"Error getting available tools: {e}")
            return []

    def get_available_tools(self) -> List[str]:
        """Get list of available tool names (synchronous wrapper)."""
        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    # If event loop is already running, return empty list as fallback
                    return []
                else:
                    return loop.run_until_complete(self.get_available_tools_async())
            except RuntimeError:
                return []
        except Exception as e:
            logger.warning(f"Failed to get available tools: {e}")
            return []

    async def get_tools_info_async(self) -> List[Dict[str, Any]]:
        """Get detailed information about all available tools."""
        try:
            # Get tools from FastMCP
            tools = await self.app.get_tools()

            tools_info = []
            for tool_name, tool_func in tools.items():
                tool_info = {
                    "name": tool_name,
                    "description": self._get_tool_description(tool_name),
                    "parameters": self._get_tool_parameters(tool_name),
                    "category": self._get_tool_category(tool_name),
                    "enabled": True,
                }
                tools_info.append(tool_info)

            return tools_info
        except Exception as e:
            logger.error(f"Error getting tools info: {e}")
            return []

    def _get_tool_description(self, tool_name: str) -> Optional[str]:
        """Get description for a tool."""
        descriptions = {
            # Document tools
            "analyze_document_structure": "Analyze the structure and organization of a document",
            "extract_document_keywords": "Extract keywords and key phrases from document content",
            "check_document_links": "Check and validate links within a document",
            "summarize_document_sections": "Generate summaries for different sections of a document",
            # Feedback tools
            "collect_user_feedback": "Collect and store user feedback about documents or features",
            "generate_feedback_from_conversation": "Generate structured feedback based on conversation history",
            "create_improvement_proposal": "Create improvement proposals based on feedback data",
            "analyze_conversation_patterns": "Analyze patterns and themes in conversation history",
            # Analysis tools
            "analyze_document_quality": "Analyze document quality against various criteria",
            "extract_document_topics": "Extract main topics and themes from document content",
            "check_document_completeness": "Check document completeness against specified criteria",
            # GitHub tools
            "create_github_issue": "現在表示中のドキュメントのリポジトリにGitHub Issueを作成します。問題報告、改善提案、バグ報告などに使用できます。",
            "create_github_pull_request": "現在表示中のドキュメントのリポジトリにGitHubプルリクエストを作成します。コード変更、ドキュメント更新などの提案に使用できます。",
            "check_github_repository_permissions": "現在表示中のドキュメントのGitHubリポジトリの権限を確認します。読み取り、書き込み、Issue作成などの権限状況を確認できます。",
            # Utility tools
            "get_current_time": "Get current date and time in specified format",
            "count_text_characters": "Count characters, words, and lines in text",
            "validate_email_format": "Validate email address format",
            "generate_random_data": "Generate random data for testing purposes",
        }
        return descriptions.get(tool_name)

    def _get_tool_parameters(self, tool_name: str) -> List[Dict[str, Any]]:
        """Get parameters for a tool."""
        parameters_map = {
            # Document tools
            "analyze_document_structure": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Content of the document to analyze",
                },
                {
                    "name": "analysis_type",
                    "type": "str",
                    "required": False,
                    "default": "basic",
                    "description": "Type of analysis to perform",
                },
            ],
            "extract_document_keywords": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Content to extract keywords from",
                },
                {
                    "name": "keyword_count",
                    "type": "int",
                    "required": False,
                    "default": 10,
                    "description": "Maximum number of keywords to extract",
                },
            ],
            "check_document_links": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Document content to check links in",
                },
                {
                    "name": "base_url",
                    "type": "str",
                    "required": False,
                    "description": "Base URL for relative link checking",
                },
            ],
            "summarize_document_sections": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Content to summarize",
                },
                {
                    "name": "section_type",
                    "type": "str",
                    "required": False,
                    "default": "auto",
                    "description": "Type of sections to identify",
                },
            ],
            # Feedback tools
            "collect_user_feedback": [
                {
                    "name": "feedback_text",
                    "type": "str",
                    "required": True,
                    "description": "User feedback text",
                },
                {
                    "name": "feedback_type",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "Type of feedback",
                },
                {
                    "name": "rating",
                    "type": "int",
                    "required": False,
                    "description": "Numerical rating if applicable",
                },
            ],
            "generate_feedback_from_conversation": [
                {
                    "name": "conversation_history",
                    "type": "List[Dict[str, Any]]",
                    "required": True,
                    "description": "Conversation history to analyze",
                },
                {
                    "name": "feedback_type",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "Type of feedback to generate",
                },
            ],
            "create_improvement_proposal": [
                {
                    "name": "current_content",
                    "type": "str",
                    "required": True,
                    "description": "Current content to improve",
                },
                {
                    "name": "feedback_data",
                    "type": "Dict[str, Any]",
                    "required": True,
                    "description": "Feedback data for improvement",
                },
            ],
            "analyze_conversation_patterns": [
                {
                    "name": "conversation_history",
                    "type": "List[Dict[str, Any]]",
                    "required": True,
                    "description": "Conversation history to analyze",
                },
                {
                    "name": "analysis_depth",
                    "type": "str",
                    "required": False,
                    "default": "basic",
                    "description": "Depth of pattern analysis",
                },
            ],
            # Analysis tools
            "analyze_document_quality": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Document content to analyze",
                },
                {
                    "name": "quality_criteria",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "Quality criteria to apply",
                },
            ],
            "extract_document_topics": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Document content to extract topics from",
                },
                {
                    "name": "topic_count",
                    "type": "int",
                    "required": False,
                    "default": 5,
                    "description": "Number of topics to extract",
                },
            ],
            "check_document_completeness": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Document content to check",
                },
                {
                    "name": "completeness_criteria",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "Completeness criteria to apply",
                },
            ],
            # GitHub tools
            "create_github_issue": [
                {
                    "name": "title",
                    "type": "str",
                    "required": True,
                    "description": "Issueのタイトル（簡潔で分かりやすい日本語で記述）",
                },
                {
                    "name": "description",
                    "type": "str",
                    "required": True,
                    "description": "Issueの詳細説明（問題の内容、再現手順、期待される結果などを日本語で記述）",
                },
                {
                    "name": "labels",
                    "type": "List[str]",
                    "required": False,
                    "description": "Issueに適用するラベルのリスト（例：['バグ', '改善提案', 'ドキュメント']）",
                },
                {
                    "name": "assignees",
                    "type": "List[str]",
                    "required": False,
                    "description": "Issueを担当するGitHubユーザー名のリスト",
                },
                {
                    "name": "github_token",
                    "type": "str",
                    "required": False,
                    "description": "GitHub Personal Access Token（オプション、環境変数から自動取得）",
                },
            ],
            "create_github_pull_request": [
                {
                    "name": "repository",
                    "type": "str",
                    "required": True,
                    "description": "Repository in format 'owner/repo'",
                },
                {
                    "name": "title",
                    "type": "str",
                    "required": True,
                    "description": "Pull request title",
                },
                {
                    "name": "description",
                    "type": "str",
                    "required": True,
                    "description": "Pull request description",
                },
                {
                    "name": "file_path",
                    "type": "str",
                    "required": True,
                    "description": "Path to the file to modify",
                },
                {
                    "name": "file_content",
                    "type": "str",
                    "required": True,
                    "description": "New file content",
                },
                {
                    "name": "branch_name",
                    "type": "str",
                    "required": False,
                    "description": "Branch name for the PR",
                },
                {
                    "name": "base_branch",
                    "type": "str",
                    "required": False,
                    "default": "main",
                    "description": "Base branch for the PR",
                },
                {
                    "name": "github_token",
                    "type": "str",
                    "required": False,
                    "description": "GitHub access token",
                },
            ],
            "check_github_repository_permissions": [
                {
                    "name": "repository",
                    "type": "str",
                    "required": True,
                    "description": "Repository in format 'owner/repo'",
                },
                {
                    "name": "github_token",
                    "type": "str",
                    "required": False,
                    "description": "GitHub access token",
                },
            ],
            # Utility tools
            "get_current_time": [
                {
                    "name": "format",
                    "type": "str",
                    "required": False,
                    "default": "iso",
                    "description": "Time format (iso, readable, timestamp)",
                },
                {
                    "name": "timezone",
                    "type": "str",
                    "required": False,
                    "description": "Timezone for the time",
                },
            ],
            "count_text_characters": [
                {
                    "name": "text",
                    "type": "str",
                    "required": True,
                    "description": "Text to count characters in",
                }
            ],
            "validate_email_format": [
                {
                    "name": "email",
                    "type": "str",
                    "required": True,
                    "description": "Email address to validate",
                }
            ],
            "generate_random_data": [
                {
                    "name": "data_type",
                    "type": "str",
                    "required": True,
                    "description": "Type of random data to generate",
                },
                {
                    "name": "count",
                    "type": "int",
                    "required": False,
                    "default": 1,
                    "description": "Number of items to generate",
                },
                {
                    "name": "options",
                    "type": "Dict[str, Any]",
                    "required": False,
                    "description": "Additional options for data generation",
                },
            ],
        }
        return parameters_map.get(tool_name, [])

    def _get_tool_category(self, tool_name: str) -> str:
        """Get category for a tool."""
        if (
            tool_name.startswith("analyze_document")
            or tool_name.startswith("extract_document")
            or tool_name.startswith("check_document")
            or tool_name.startswith("summarize_document")
        ):
            return "document"
        elif (
            "feedback" in tool_name
            or "conversation" in tool_name
            or "improvement" in tool_name
        ):
            return "feedback"
        elif (
            tool_name.startswith("analyze_")
            or tool_name.startswith("extract_")
            or tool_name.startswith("check_")
        ):
            return "analysis"
        elif "github" in tool_name:
            return "github"
        else:
            return "utility"

    async def get_server_info_async(self) -> Dict[str, Any]:
        """Get MCP server information."""
        return {
            "name": self.config.server_name,
            "version": "1.0.0",
            "description": "Document AI Helper MCP Server",
            "enabled_features": {
                "document_tools": self.config.enable_document_tools,
                "feedback_tools": self.config.enable_feedback_tools,
                "analysis_tools": self.config.enable_analysis_tools,
                "github_tools": self.config.enable_github_tools,
                "utility_tools": self.config.enable_utility_tools,
            },
        }


# Global server instance
mcp_server = DocumentAIHelperMCPServer()


def get_mcp_server() -> DocumentAIHelperMCPServer:
    """Get the global MCP server instance."""
    return mcp_server


async def get_available_tools() -> List[str]:
    """Get available tools from the MCP server."""
    return await mcp_server.get_available_tools_async()


async def get_tools_info() -> List[Dict[str, Any]]:
    """Get detailed information about available tools from the MCP server."""
    return await mcp_server.get_tools_info_async()


async def get_server_info() -> Dict[str, Any]:
    """Get MCP server information."""
    return await mcp_server.get_server_info_async()


async def call_mcp_tool(tool_name: str, **kwargs) -> Any:
    """Call an MCP tool by name."""
    return await mcp_server.call_tool(tool_name, **kwargs)
