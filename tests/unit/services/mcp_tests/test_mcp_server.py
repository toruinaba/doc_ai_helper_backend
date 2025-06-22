"""
Tests for FastMCP server implementation.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.config import MCPConfig


@pytest.fixture
def mcp_config():
    """Create a test MCP configuration."""
    return MCPConfig(
        server_name="test_server",
        server_version="1.0.0",
        enable_document_tools=True,
        enable_feedback_tools=True,
        enable_analysis_tools=True,
    )


@pytest.fixture
@patch("doc_ai_helper_backend.services.mcp.server.FastMCP")
def mcp_server(mock_fastmcp, mcp_config):
    """Create a test MCP server."""
    mock_app = Mock()
    mock_app._tools = {}
    mock_app.get_tool = Mock(return_value=AsyncMock())
    mock_app.get_tools = AsyncMock(return_value={})
    mock_fastmcp.return_value = mock_app

    server = DocumentAIHelperMCPServer(mcp_config)
    return server


@pytest.mark.asyncio
class TestDocumentAIHelperMCPServer:
    """Test cases for DocumentAIHelperMCPServer."""

    def test_server_initialization(self, mcp_server, mcp_config):
        """Test that the server initializes correctly."""
        assert mcp_server.config == mcp_config
        assert mcp_server.app is not None

    def test_get_available_tools(self, mcp_server):
        """Test getting available tools."""

        # Mock the FastMCP app with tools
        async def mock_get_tools():
            return {
                "extract_document_context": {"description": "Extract context"},
                "analyze_document_structure": {"description": "Analyze structure"},
            }

        mcp_server.app.get_tools = AsyncMock(
            return_value={
                "extract_document_context": {"description": "Extract context"},
                "analyze_document_structure": {"description": "Analyze structure"},
            }
        )

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tools = loop.run_until_complete(mcp_server.get_available_tools_async())
            assert "extract_document_context" in tools
            assert "analyze_document_structure" in tools
        finally:
            loop.close()

    def test_list_tools(self, mcp_server):
        """Test listing tools with metadata."""
        # Mock the FastMCP app with tools
        mock_tools = {
            "extract_document_context": type(
                "MockTool", (), {"description": "Extract context"}
            )(),
            "analyze_document_structure": type(
                "MockTool", (), {"description": "Analyze structure"}
            )(),
        }

        mcp_server.app.get_tools = AsyncMock(return_value=mock_tools)

        import asyncio

        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        try:
            tools_list = loop.run_until_complete(mcp_server.list_tools_async())
            assert len(tools_list) == 2
            assert all("name" in tool for tool in tools_list)
            assert all("description" in tool for tool in tools_list)
        finally:
            loop.close()

    @pytest.mark.asyncio
    async def test_call_tool_success(self, mcp_server):
        """Test successful tool calling."""
        # Mock the tool function itself
        mock_result = {"status": "success", "result": "test result"}
        mock_tool = AsyncMock(return_value=mock_result)

        # Mock get_tool to return our mock tool
        mcp_server.app.get_tool = Mock(return_value=mock_tool)

        result = await mcp_server.call_tool("test_tool", param1="value1")

        assert result == mock_result
        mock_tool.assert_called_once_with(param1="value1")

    @pytest.mark.asyncio
    async def test_call_tool_error(self, mcp_server):
        """Test tool calling with error."""
        # Mock get_tool to return a tool that raises an exception
        mock_tool = AsyncMock(side_effect=Exception("Tool error"))
        mcp_server.app.get_tool = Mock(return_value=mock_tool)

        with pytest.raises(Exception, match="Tool execution failed"):
            await mcp_server.call_tool("test_tool", param1="value1")

    def test_fastmcp_app_property(self, mcp_server):
        """Test accessing the underlying FastMCP app."""
        assert mcp_server.fastmcp_app is mcp_server.app
