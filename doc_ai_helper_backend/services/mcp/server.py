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
            """Extract structured context from documents. Analyzes headings, paragraph structure, metadata to provide detailed document information."""
            return await extract_document_context(
                document_content=document_content, context_type=context_type
            )

        @self.app.tool("analyze_document_structure")
        async def analyze_structure_tool(
            document_content: str, analysis_depth: str = "basic"
        ) -> Dict[str, Any]:
            """Analyze document structure and composition. Detailed analysis of heading hierarchy, section division, logical flow."""
            return await analyze_document_structure(
                document_content=document_content, analysis_depth=analysis_depth
            )

        @self.app.tool("optimize_document_content")
        async def optimize_content_tool(
            document_content: str, optimization_type: str = "readability"
        ) -> Dict[str, Any]:
            """Optimize document content for readability and structural improvement. Paragraph composition, expression improvement, overall quality enhancement."""
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
            """Generate structured feedback from conversation history. Analyze dialogue patterns and improvement points to create detailed feedback reports."""
            return await generate_feedback_from_conversation(
                conversation_history=conversation_history, feedback_type=feedback_type
            )

        @self.app.tool("create_improvement_proposal")
        async def create_proposal_tool(
            current_content: str, feedback_data: Dict[str, Any]
        ) -> Dict[str, Any]:
            """Create improvement proposals based on feedback data. Analyze current content and provide specific, practical improvement suggestions."""
            return await create_improvement_proposal(
                current_content=current_content, feedback_data=feedback_data
            )

        @self.app.tool("analyze_conversation_patterns")
        async def analyze_patterns_tool(
            conversation_history: List[Dict[str, Any]], analysis_depth: str = "basic"
        ) -> Dict[str, Any]:
            """Analyze patterns and themes in conversation history. Detailed analysis of dialogue trends, frequent topics, communication characteristics."""
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
            """Analyze document quality against various criteria. Evaluate readability, structure, content completeness, technical accuracy."""
            return await analyze_document_quality(
                document_content=document_content, quality_criteria=quality_criteria
            )

        @self.app.tool("extract_document_topics")
        async def extract_topics_tool(
            document_content: str, topic_count: int = 5
        ) -> Dict[str, Any]:
            """Extract main topics and themes from document content. Identify important topics through keyword analysis and semantic grouping."""
            return await extract_document_topics(
                document_content=document_content, topic_count=topic_count
            )

        @self.app.tool("check_document_completeness")
        async def check_completeness_tool(
            document_content: str, completeness_criteria: str = "general"
        ) -> Dict[str, Any]:
            """Check document completeness against specified criteria. Evaluate missing necessary information, structural problems, content coverage."""
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
            """Create new pull request in specified Git service. Supports PR creation for code review, feature integration, bug fixes."""
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
            """Check permissions for current repository context. Verify access levels including read, write, admin permissions."""
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
            document_content: str = "",
            summary_length: str = "comprehensive",
            focus_area: str = "general", 
            context: Optional[str] = None,
        ) -> str:
            """Generate high-quality summaries of Japanese documents using internal LLM API.
            
            When called without document_content, automatically uses the current document being viewed in the repository context.
            """
            # If document_content is empty, try to get it from repository context
            if not document_content.strip():
                # Try to get current document content from repository context
                repository_context = getattr(self, "_current_repository_context", None)
                if repository_context and repository_context.get("current_path"):
                    try:
                        # Import document service to get current document content
                        from doc_ai_helper_backend.api.dependencies import get_document_service
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
                            logger.info(f"Auto-retrieved document content from {owner}/{repo}/{path}: {len(document_content)} chars")
                    except Exception as e:
                        logger.warning(f"Failed to auto-retrieve document content: {e}")
                
                # Still no content available
                if not document_content.strip():
                    import json
                    return json.dumps({
                        "success": False,
                        "error": "document_content parameter is required. Please specify the document content to summarize, or ensure the current document is available in the repository context.",
                        "hint": "Example: summarize_document_with_llm(document_content='paste document content here')"
                    }, ensure_ascii=False)
            
            return await summarize_document_with_llm(
                document_content=document_content,
                summary_length=summary_length,
                focus_area=focus_area,
                context=context,
            )

        @self.app.tool("create_improvement_recommendations_with_llm")
        async def improvement_tool(
            document_content: str = "",
            summary_context: str = "",
            improvement_type: str = "comprehensive",
            target_audience: str = "general",
        ) -> str:
            """Create detailed improvement recommendations for Japanese documents through professional LLM analysis.
            
            When called without document_content, automatically uses the current document being viewed in the repository context.
            """
            # If document_content is empty, try to get it from repository context
            if not document_content.strip():
                # Try to get current document content from repository context
                repository_context = getattr(self, "_current_repository_context", None)
                if repository_context and repository_context.get("current_path"):
                    try:
                        # Import document service to get current document content
                        from doc_ai_helper_backend.api.dependencies import get_document_service
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
                            logger.info(f"Auto-retrieved document content from {owner}/{repo}/{path}: {len(document_content)} chars")
                    except Exception as e:
                        logger.warning(f"Failed to auto-retrieve document content: {e}")
                
                # Still no content available
                if not document_content.strip():
                    import json
                    return json.dumps({
                        "success": False,
                        "error": "document_content parameter is required. Please specify the document content for improvement recommendations, or ensure the current document is available in the repository context.",
                        "hint": "Example: create_improvement_recommendations_with_llm(document_content='paste document content here')"
                    }, ensure_ascii=False)
            
            return await create_improvement_recommendations_with_llm(
                document_content=document_content,
                summary_context=summary_context,
                improvement_type=improvement_type,
                target_audience=target_audience,
            )

        logger.info("LLM-enhanced tools registered with FastMCP")

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

                # Validate document_content parameter
                document_content = kwargs.get("document_content", "")
                if not document_content.strip():
                    import json
                    return json.dumps({
                        "success": False,
                        "error": "document_content parameter is required. Please specify the document content to summarize.",
                        "hint": "Example: summarize_document_with_llm(document_content='paste document content here')"
                    }, ensure_ascii=False)

                return await summarize_document_with_llm(**kwargs)
            elif tool_name == "create_improvement_recommendations_with_llm":
                from doc_ai_helper_backend.services.mcp.tools.llm_enhanced_tools import (
                    create_improvement_recommendations_with_llm,
                )

                # Validate document_content parameter
                document_content = kwargs.get("document_content", "")
                if not document_content.strip():
                    import json
                    return json.dumps({
                        "success": False,
                        "error": "document_content parameter is required. Please specify the document content for improvement recommendations.",
                        "hint": "Example: create_improvement_recommendations_with_llm(document_content='paste document content here')"
                    }, ensure_ascii=False)

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
            "analyze_document_structure": "Analyze document structure and composition. Detailed analysis of heading hierarchy, section division, logical flow.",
            "extract_document_keywords": "Extract keywords and important phrases from document content. Identify core topics through text mining.",
            "check_document_links": "Check and validate links in documents. Verify validity and accessibility of internal and external links.",
            "summarize_document_sections": "Generate summaries for different sections of documents. Understand section-wise points and overall structure.",
            # Feedback tools
            "collect_user_feedback": "Collect and store user feedback about documents and features. Systematically manage improvement points and issues.",
            "generate_feedback_from_conversation": "Generate structured feedback based on conversation history. Analyze dialogue patterns and improvement points.",
            "create_improvement_proposal": "Create improvement proposals based on feedback data. Provide specific and practical improvement suggestions.",
            "analyze_conversation_patterns": "Analyze patterns and themes in conversation history. Identify dialogue trends and frequent topics.",
            # Analysis tools
            "analyze_document_quality": "Analyze document quality against various criteria. Evaluate readability, structure, content completeness.",
            "extract_document_topics": "Extract main topics and themes from document content. Identify important topics through keyword analysis.",
            "check_document_completeness": "Check document completeness against specified criteria. Identify missing necessary information and structural problems.",
            # Git tools
            "create_git_issue": "Create issue in unified Git services (GitHub/Forgejo). Can be used for problem reports, improvement proposals, bug reports.",
            "create_github_pull_request": "Create GitHub pull request for currently displayed document repository. Can be used for proposing code changes, document updates.",
            "check_github_repository_permissions": "Check permissions for currently displayed document's GitHub repository. Verify permission status for read, write, issue creation.",
            # Utility tools
            "get_current_time": "Get current date and time in specified format. Supports timestamps and date formatting.",
            "count_text_characters": "Count characters, words, lines in text. Used for analyzing document length and structure.",
            "validate_email_format": "Validate email address format. Check if it's a valid email address format.",
            "generate_random_data": "Generate random data for testing purposes. Used for creating sample data and verification information.",
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
                    "description": "Issue title (concise and clear description)",
                },
                {
                    "name": "description",
                    "type": "str",
                    "required": True,
                    "description": "Issue detailed description (problem content, reproduction steps, expected results)",
                },
                {
                    "name": "labels",
                    "type": "List[str]",
                    "required": False,
                    "description": "List of labels to apply to the issue (e.g., ['bug', 'enhancement', 'documentation'])",
                },
                {
                    "name": "assignees",
                    "type": "List[str]",
                    "required": False,
                    "description": "List of usernames to assign to the issue",
                },
                {
                    "name": "github_token",
                    "type": "str",
                    "required": False,
                    "description": "GitHub Personal Access Token (optional, auto-retrieved from environment variables)",
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
                    "description": "Japanese document content to summarize",
                },
                {
                    "name": "summary_length",
                    "type": "str",
                    "required": False,
                    "default": "comprehensive",
                    "description": "Summary length (brief=concise, detailed=detailed, comprehensive=comprehensive)",
                },
                {
                    "name": "focus_area",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "Focus area (general=general, technical=technical, business=business)",
                },
                {
                    "name": "context",
                    "type": "str",
                    "required": False,
                    "description": "Additional context (optional)",
                },
            ],
            "create_improvement_recommendations_with_llm": [
                {
                    "name": "document_content",
                    "type": "str",
                    "required": True,
                    "description": "Japanese document content to analyze",
                },
                {
                    "name": "summary_context",
                    "type": "str",
                    "required": False,
                    "default": "",
                    "description": "Pre-analysis summary context (optional)",
                },
                {
                    "name": "improvement_type",
                    "type": "str",
                    "required": False,
                    "default": "comprehensive",
                    "description": "Improvement type (structure=structure, content=content, readability=readability, comprehensive=comprehensive)",
                },
                {
                    "name": "target_audience",
                    "type": "str",
                    "required": False,
                    "default": "general",
                    "description": "Target audience (general=general, technical=technical, beginner=beginner, expert=expert)",
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
