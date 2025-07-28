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

        # Git tools use GitServiceFactory directly, no setup needed

        # Register tools based on configuration
        # Register comprehensive document analysis tool (replaces document, feedback, and analysis tools)
        self._register_comprehensive_tools()

        # Always register git tools (GitHub/Forgejo integration is enabled by default)
        self._register_git_tools()

        # Register LLM-enhanced tools for Japanese document processing
        self._register_llm_enhanced_tools()

        logger.info("MCP Server setup completed")

    def _register_comprehensive_tools(self):
        """Register comprehensive document analysis tool using FastMCP decorators."""
        from .tools.comprehensive_tools import analyze_document_comprehensive

        @self.app.tool("analyze_document_comprehensive")
        async def analyze_comprehensive_tool(
            document_content: str, 
            analysis_type: str = "full", 
            focus_area: str = "general"
        ) -> Dict[str, Any]:
            """
            Comprehensive document analysis combining structure, quality, topics, and completeness analysis.
            
            This consolidated tool provides complete document insights including structure analysis, 
            quality metrics, topic extraction, completeness checks, and contextual information.
            Replaces multiple separate analysis tools for better efficiency and selection accuracy.
            
            Args:
            - document_content: The document content to analyze
            - analysis_type: Type of analysis - "full", "structure", "quality", "topics", "completeness"
            - focus_area: Focus area - "general", "technical", "readability", "completeness"
            
            Returns: Comprehensive analysis results with structure, quality, topics, and recommendations
            """
            return await analyze_document_comprehensive(
                document_content=document_content,
                analysis_type=analysis_type,
                focus_area=focus_area
            )

        logger.info("Comprehensive tools registered with FastMCP")


    def _register_git_tools(self):
        """Register Git tools using FastMCP decorators."""
        from .tools.git_tools import (
            create_git_issue,
            check_git_repository_permissions,
        )

        @self.app.tool("create_git_issue")
        async def create_issue_tool(
            title: str,
            problem_description: str,
            improvement_proposals: str,
            labels: Optional[List[str]] = None,
            assignees: Optional[List[str]] = None,
            repository_context: Optional[Dict[str, Any]] = None,
        ) -> str:
            """Create a new issue with clear separation of problem and improvement proposals. Repository context is automatically injected by the LLM service."""
            logger.info(f"Creating Git issue with repository_context: {repository_context}")
            
            return await create_git_issue(
                title=title,
                problem_description=problem_description,
                improvement_proposals=improvement_proposals,
                labels=labels,
                assignees=assignees,
                repository_context=repository_context,
            )


        @self.app.tool("check_git_repository_permissions")
        async def check_permissions_tool(
            repository_context: Optional[Dict[str, Any]] = None,
        ) -> Dict[str, Any]:
            """Check permissions for current repository context. Repository context is automatically injected by the LLM service."""
            logger.info(f"Checking Git permissions with repository_context: {repository_context}")

            return await check_git_repository_permissions(
                repository_context=repository_context,
            )

        logger.info("Git tools registered with FastMCP")

    def _register_llm_enhanced_tools(self):
        """Register LLM-enhanced tools for Japanese document processing using FastMCP decorators."""
        from .tools.llm_enhanced_tools import (
            create_improvement_recommendations_with_llm,
        )


        @self.app.tool("create_improvement_recommendations_with_llm")
        async def improvement_tool(
            document_content: str = "",
            summary_context: str = "",
            improvement_type: str = "comprehensive",
            target_audience: str = "general",
            feedback_data: str = "",
        ) -> str:
            """
            Create detailed improvement recommendations for Japanese documents through professional LLM analysis.
            
            Consolidates document analysis and feedback data to provide comprehensive improvement suggestions.
            Replaces the previous create_improvement_proposal tool with enhanced LLM-powered analysis.
            When called without document_content, automatically uses the current document being viewed in the repository context.
            
            Args:
            - document_content: Document content to analyze (auto-retrieved if empty)
            - summary_context: Summary context for additional insights
            - improvement_type: Type of improvement focus (comprehensive, structure, content, readability)
            - target_audience: Target audience (general, technical, business)
            - feedback_data: Additional feedback data as JSON string
            
            Returns: Comprehensive improvement recommendations with implementation guidance
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
                feedback_data=feedback_data,
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
        Call a specific tool by name using FastMCP (unified execution path).

        Args:
            tool_name: Name of the tool to call
            **kwargs: Arguments to pass to the tool

        Returns:
            Result of the tool execution
        """
        try:
            logger.info(f"Executing tool via FastMCP: {tool_name}")
            logger.debug(f"Tool arguments: {kwargs}")
            
            # Get tool from FastMCP
            tool = await self.app.get_tool(tool_name)
            if not tool:
                raise ValueError(f"Tool {tool_name} not found in FastMCP registry")
            
            # Execute tool function directly
            result = await tool.fn(**kwargs)
            logger.debug(f"FastMCP tool execution result: {result}")
            return result

        except Exception as e:
            logger.error(f"Error calling FastMCP tool {tool_name}: {e}")
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
        """Get detailed information about all available tools using FastMCP."""
        try:
            # Get tools directly from FastMCP
            tools = await self.app.get_tools()

            tools_info = []
            for tool_name, tool in tools.items():
                tool_info = {
                    "name": tool_name,
                    "description": tool.description or f"FastMCP tool: {tool_name}",
                    "parameters": tool.parameters or {"type": "object", "properties": {}, "required": []},
                    "category": self._categorize_tool(tool_name),
                    "enabled": tool.enabled,
                }
                tools_info.append(tool_info)

            return tools_info
        except Exception as e:
            logger.error(f"Error getting tools info: {e}")
            return []

    def _categorize_tool(self, tool_name: str) -> str:
        """Simple tool categorization based on name."""
        if "git" in tool_name:
            return "git"
        elif "document" in tool_name:
            return "document"
        elif "feedback" in tool_name or "conversation" in tool_name or "improvement" in tool_name:
            return "feedback"
        elif "llm" in tool_name:
            return "llm_enhanced"
        else:
            return "utility"


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
