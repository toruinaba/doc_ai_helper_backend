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

        # Always register git tools (GitHub/Forgejo integration is enabled by default)
        self._register_git_tools()

        # Register LLM-enhanced tools for Japanese document processing
        self._register_llm_enhanced_tools()

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
            """文書から構造化されたコンテキストを抽出します。見出し、段落構造、メタデータなどを分析して詳細な文書情報を提供します。"""
            return await extract_document_context(
                document_content=document_content, context_type=context_type
            )

        @self.app.tool("analyze_document_structure")
        async def analyze_structure_tool(
            document_content: str, analysis_depth: str = "basic"
        ) -> Dict[str, Any]:
            """文書の構造と構成を分析します。見出し階層、セクション分割、論理的な流れなどを詳細に解析します。"""
            return await analyze_document_structure(
                document_content=document_content, analysis_depth=analysis_depth
            )

        @self.app.tool("optimize_document_content")
        async def optimize_content_tool(
            document_content: str, optimization_type: str = "readability"
        ) -> Dict[str, Any]:
            """文書コンテンツを読みやすさと構造の改善のために最適化します。段落構成、表現の改善、全体的な品質向上を行います。"""
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
            """会話履歴から構造化されたフィードバックを生成します。対話パターンや改善点を分析し、詳細なフィードバックレポートを作成します。"""
            return await generate_feedback_from_conversation(
                conversation_history=conversation_history, feedback_type=feedback_type
            )

        @self.app.tool("create_improvement_proposal")
        async def create_proposal_tool(
            current_content: str, feedback_data: Dict[str, Any]
        ) -> Dict[str, Any]:
            """フィードバックデータに基づいて改善提案を作成します。現在のコンテンツを分析し、具体的で実践的な改善案を提供します。"""
            return await create_improvement_proposal(
                current_content=current_content, feedback_data=feedback_data
            )

        @self.app.tool("analyze_conversation_patterns")
        async def analyze_patterns_tool(
            conversation_history: List[Dict[str, Any]], analysis_depth: str = "basic"
        ) -> Dict[str, Any]:
            """会話履歴のパターンとテーマを分析します。対話の傾向、頻出トピック、コミュニケーションの特徴を詳細に解析します。"""
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
            """様々な基準に対して文書品質を分析します。読みやすさ、構造、内容の完全性、技術的正確性などを評価します。"""
            return await analyze_document_quality(
                document_content=document_content, quality_criteria=quality_criteria
            )

        @self.app.tool("extract_document_topics")
        async def extract_topics_tool(
            document_content: str, topic_count: int = 5
        ) -> Dict[str, Any]:
            """文書内容から主要なトピックとテーマを抽出します。キーワード分析、意味的グループ化により重要な議題を特定します。"""
            return await extract_document_topics(
                document_content=document_content, topic_count=topic_count
            )

        @self.app.tool("check_document_completeness")
        async def check_completeness_tool(
            document_content: str, completeness_criteria: str = "general"
        ) -> Dict[str, Any]:
            """指定された基準に対して文書の完全性をチェックします。必要な情報の欠落、構造的な問題、内容の網羅性を評価します。"""
            return await check_document_completeness(
                document_content=document_content,
                completeness_criteria=completeness_criteria,
            )

        logger.info("Analysis tools registered with FastMCP")

    def _setup_unified_git_tools(self):
        """Set up unified Git tools with configured services."""
        from .tools.git_tools import configure_git_service
        from doc_ai_helper_backend.core.config import settings

        # Get tokens from settings (which loads from .env)
        github_token = settings.github_token
        forgejo_token = settings.forgejo_token
        forgejo_base_url = settings.forgejo_base_url
        forgejo_username = settings.forgejo_username
        forgejo_password = settings.forgejo_password
        default_git_service = settings.default_git_service or "github"

        # Configure GitHub if token is available
        if github_token:
            try:
                configure_git_service(
                    "github",
                    config={
                        "access_token": github_token,
                        "default_labels": ["documentation", "improvement"],
                    },
                    set_as_default=(default_git_service == "github"),
                )
                logger.info("Configured GitHub service for unified Git tools")
            except Exception as e:
                logger.warning(f"Failed to configure GitHub service: {str(e)}")

        # Configure Forgejo if configured
        if forgejo_base_url and (
            forgejo_token or (forgejo_username and forgejo_password)
        ):
            try:
                configure_git_service(
                    "forgejo",
                    config={
                        "base_url": forgejo_base_url,
                        "access_token": forgejo_token,
                        "username": forgejo_username,
                        "password": forgejo_password,
                        "default_labels": ["documentation", "improvement"],
                    },
                    set_as_default=(default_git_service == "forgejo"),
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
            """Create a new issue in the Git repository (supports GitHub, Forgejo, and other Git services)."""
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
            """指定されたGitサービスで新しいプルリクエストを作成します。コードレビュー、機能統合、バグ修正などのためのPR作成に対応します。"""
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
            """現在のリポジトリコンテキストの権限をチェックします。読み取り、書き込み、管理者権限などのアクセスレベルを確認します。"""
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

    def _register_llm_enhanced_tools(self):
        """Register LLM-enhanced tools for Japanese document processing using FastMCP decorators."""
        from .tools.llm_enhanced_tools import (
            summarize_document_with_llm,
            create_improvement_recommendations_with_llm,
        )

        @self.app.tool("summarize_document_with_llm")
        async def summarize_tool(
            document_content: str,
            summary_length: str = "comprehensive",
            focus_area: str = "general", 
            context: Optional[str] = None,
        ) -> str:
            """内部LLM APIを使用して日本語文書の高品質な要約を生成します。"""
            return await summarize_document_with_llm(
                document_content=document_content,
                summary_length=summary_length,
                focus_area=focus_area,
                context=context,
            )

        @self.app.tool("create_improvement_recommendations_with_llm")
        async def improvement_tool(
            document_content: str,
            summary_context: str = "",
            improvement_type: str = "comprehensive",
            target_audience: str = "general",
        ) -> str:
            """専門レベルのLLM分析による日本語文書の詳細な改善提案を作成します。"""
            return await create_improvement_recommendations_with_llm(
                document_content=document_content,
                summary_context=summary_context,
                improvement_type=improvement_type,
                target_audience=target_audience,
            )

        logger.info("LLM-enhanced tools for Japanese documents registered with FastMCP")

    def set_repository_context(self, repository_context: Optional[Dict[str, Any]]):
        """
        Set the current repository context for secure tools.
        
        DEPRECATED: This method no longer sets global state. Repository context
        is now passed directly to tool execution to avoid concurrency issues.

        Args:
            repository_context: Repository context from LLM request
        """
        # Log deprecation warning but take no action
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
            logger.warning(f"DEPRECATED: set_repository_context called for {owner}/{repo}. Context is now passed directly to tools.")
        else:
            logger.warning("DEPRECATED: set_repository_context called with None. Context is now passed directly to tools.")

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
            elif tool_name == "summarize_document_with_llm":
                from doc_ai_helper_backend.services.mcp.tools.llm_enhanced_tools import (
                    summarize_document_with_llm,
                )

                return await summarize_document_with_llm(**kwargs)
            elif tool_name == "create_improvement_recommendations_with_llm":
                from doc_ai_helper_backend.services.mcp.tools.llm_enhanced_tools import (
                    create_improvement_recommendations_with_llm,
                )

                return await create_improvement_recommendations_with_llm(**kwargs)
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
            "analyze_document_structure": "文書の構造と構成を分析します。見出し階層、セクション分割、論理的な流れなどを詳細に解析します。",
            "extract_document_keywords": "文書内容からキーワードと重要なフレーズを抽出します。テキストマイニングにより核心的なトピックを特定します。",
            "check_document_links": "文書内のリンクをチェックし、検証します。内部リンク、外部リンクの有効性やアクセシビリティを確認します。",
            "summarize_document_sections": "文書の異なるセクションに対して要約を生成します。章ごとのポイントや全体構造を把握できます。",
            # Feedback tools
            "collect_user_feedback": "文書や機能に関するユーザーフィードバックを収集し、保存します。改善点や問題点を体系的に管理します。",
            "generate_feedback_from_conversation": "会話履歴に基づいて構造化されたフィードバックを生成します。対話パターンや改善点を分析します。",
            "create_improvement_proposal": "フィードバックデータに基づいて改善提案を作成します。具体的で実践的な改善案を提供します。",
            "analyze_conversation_patterns": "会話履歴のパターンとテーマを分析します。対話の傾向や頻出トピックを特定します。",
            # Analysis tools
            "analyze_document_quality": "様々な基準に対して文書品質を分析します。読みやすさ、構造、内容の完全性を評価します。",
            "extract_document_topics": "文書内容から主要なトピックとテーマを抽出します。キーワード分析により重要な議題を特定します。",
            "check_document_completeness": "指定された基準に対して文書の完全性をチェックします。必要情報の欠落や構造的問題を特定します。",
            # Git tools
            "create_git_issue": "統一Gitサービス（GitHub/Forgejo）でIssueを作成します。問題報告、改善提案、バグ報告などに使用できます。",
            "create_github_pull_request": "現在表示中のドキュメントのリポジトリにGitHubプルリクエストを作成します。コード変更、ドキュメント更新などの提案に使用できます。",
            "check_github_repository_permissions": "現在表示中のドキュメントのGitHubリポジトリの権限を確認します。読み取り、書き込み、Issue作成などの権限状況を確認できます。",
            # Utility tools
            "get_current_time": "指定された形式で現在の日付と時刻を取得します。タイムスタンプや日付フォーマットに対応します。",
            "count_text_characters": "テキスト内の文字数、単語数、行数をカウントします。文書の長さや構造を分析する際に使用します。",
            "validate_email_format": "メールアドレスの形式を検証します。有効なメールアドレス形式かどうかをチェックします。",
            "generate_random_data": "テスト目的でランダムデータを生成します。サンプルデータや動作確認用の情報作成に使用します。",
            # LLM-enhanced tools (English for better OpenAI tool selection)
            "summarize_document_with_llm": "Generate high-quality summaries of Japanese documents using internal LLM API. Provides natural and readable Japanese summaries through specialized prompts.",
            "create_improvement_recommendations_with_llm": "Create detailed improvement recommendations for Japanese documents through professional LLM analysis. Provides prioritized improvement suggestions with implementation guidance.",
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
            # Git tools
            "create_git_issue": [
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
                    "description": "Issueを担当するユーザー名のリスト",
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
            # LLM-enhanced tools
            "summarize_document_with_llm": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "要約対象の日本語文書内容",
                },
                {
                    "name": "summary_length",
                    "type": "str",
                    "required": False,
                    "default": "comprehensive",
                    "description": "要約の長さ（brief=簡潔, detailed=詳細, comprehensive=包括的）",
                },
                {
                    "name": "focus_area",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "焦点領域（general=一般向け, technical=技術的, business=ビジネス向け）",
                },
                {
                    "name": "context",
                    "type": "str",
                    "required": False,
                    "description": "追加コンテキスト（オプション）",
                },
            ],
            "create_improvement_recommendations_with_llm": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "分析対象の日本語文書内容",
                },
                {
                    "name": "summary_context",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "事前分析の要約コンテキスト（オプション）",
                },
                {
                    "name": "improvement_type",
                    "type": "str",
                    "required": False,
                    "default": "comprehensive",
                    "description": "改善タイプ（structure=構造, content=内容, readability=読みやすさ, comprehensive=包括的）",
                },
                {
                    "name": "target_audience",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "対象読者（general=一般, technical=技術者, beginner=初心者, expert=専門家）",
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
        elif "github" in tool_name or "git" in tool_name:
            return "github"
        elif "llm" in tool_name:
            return "llm_enhanced"
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
                "git_tools": True,  # Git tools are always enabled
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
