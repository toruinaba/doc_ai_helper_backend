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
        # Test with an actual document tool
        result = await mcp_server.call_tool(
            "extract_document_context",
            document_content="# Test\nThis is test content.",
            title="Test Doc",
        )

        # Document tools return JSON strings, not dict objects
        assert isinstance(result, str)
        import json

        # Should be valid JSON
        result_dict = json.loads(result)
        assert "title" in result_dict

    @pytest.mark.asyncio
    async def test_call_tool_error(self, mcp_server):
        """Test tool calling with error."""
        # Test with non-existent tool
        result = await mcp_server.call_tool("non_existent_tool", param1="value1")

        # Should return error result instead of raising exception
        assert isinstance(result, dict)
        assert "error" in result

    def test_fastmcp_app_property(self, mcp_server):
        """Test accessing the underlying FastMCP app."""
        assert hasattr(mcp_server, "app")
        assert mcp_server.app is not None
