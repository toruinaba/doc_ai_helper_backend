"""
Tests for MCP Function Adapter.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter
from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.config import MCPConfig
from doc_ai_helper_backend.models.llm import FunctionCall


@pytest.fixture
@patch("doc_ai_helper_backend.services.mcp.server.FastMCP")
def mcp_server(mock_fastmcp):
    """Create a test MCP server."""
    mock_app = Mock()
    mock_app._tools = {
        "extract_document_context": {"description": "Extract context"},
        "analyze_document_structure": {"description": "Analyze structure"},
    }
    mock_fastmcp.return_value = mock_app

    config = MCPConfig(
        server_name="test_server",
        enable_document_tools=True,
        enable_feedback_tools=False,
        enable_analysis_tools=False,
    )

    server = DocumentAIHelperMCPServer(config)
    return server


@pytest.fixture
def mcp_adapter(mcp_server):
    """Create a test MCP function adapter."""
    return MCPFunctionAdapter(mcp_server)


@pytest.mark.asyncio
class TestMCPFunctionAdapter:
    """Test cases for MCPFunctionAdapter."""

    def test_adapter_initialization(self, mcp_adapter, mcp_server):
        """Test that the adapter initializes correctly."""
        assert mcp_adapter.mcp_server == mcp_server
        assert mcp_adapter.function_registry is not None

    def test_get_function_registry(self, mcp_adapter):
        """Test getting the function registry."""
        registry = mcp_adapter.get_function_registry()
        assert registry is not None
        assert hasattr(registry, "get_all_function_definitions")

    def test_get_available_functions(self, mcp_adapter):
        """Test getting available function definitions."""
        functions = mcp_adapter.get_available_functions()
        assert isinstance(functions, list)
        # Should have at least one function registered from MCP tools
        assert len(functions) > 0

    @pytest.mark.asyncio
    async def test_execute_function_call_success(self, mcp_adapter):
        """Test successful function call execution."""
        # Mock the MCP server call_tool method
        mock_result = {"status": "success", "data": "test data"}
        mcp_adapter.mcp_server.call_tool = AsyncMock(return_value=mock_result)

        function_call = FunctionCall(
            name="extract_document_context",
            arguments='{"document_content": "test content", "repository": "test", "path": "test.md"}',
        )

        result = await mcp_adapter.execute_function_call(function_call)

        assert result["success"] is True
        assert result["result"] == mock_result

    @pytest.mark.asyncio
    async def test_execute_function_call_invalid_json(self, mcp_adapter):
        """Test function call execution with invalid JSON."""
        function_call = FunctionCall(
            name="extract_document_context",
            arguments='{"invalid": json}',  # Invalid JSON
        )

        result = await mcp_adapter.execute_function_call(function_call)

        assert result["success"] is False
        assert "Invalid JSON" in result["error"]

    @pytest.mark.asyncio
    async def test_execute_function_call_not_found(self, mcp_adapter):
        """Test function call execution for non-existent function."""
        function_call = FunctionCall(
            name="nonexistent_function", arguments='{"param": "value"}'
        )

        result = await mcp_adapter.execute_function_call(function_call)

        assert result["success"] is False
        assert "not found" in result["error"]

    def test_generate_parameters_schema_document_tools(self, mcp_adapter):
        """Test parameter schema generation for document tools."""
        schema = mcp_adapter._generate_parameters_schema("extract_document_context")

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "document_content" in schema["properties"]
        assert "repository" in schema["properties"]
        assert "path" in schema["properties"]
        assert "required" in schema
        assert "document_content" in schema["required"]

    def test_generate_parameters_schema_feedback_tools(self, mcp_adapter):
        """Test parameter schema generation for feedback tools."""
        schema = mcp_adapter._generate_parameters_schema(
            "generate_feedback_from_conversation"
        )

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "conversation_history" in schema["properties"]
        assert "feedback_type" in schema["properties"]

    def test_generate_parameters_schema_analysis_tools(self, mcp_adapter):
        """Test parameter schema generation for analysis tools."""
        schema = mcp_adapter._generate_parameters_schema("analyze_document_quality")

        assert schema["type"] == "object"
        assert "properties" in schema
        assert "document_content" in schema["properties"]
        assert "quality_metrics" in schema["properties"]

    def test_generate_parameters_schema_default(self, mcp_adapter):
        """Test parameter schema generation for unknown tools."""
        schema = mcp_adapter._generate_parameters_schema("unknown_tool")

        assert schema["type"] == "object"
        assert schema["properties"] == {}
        assert schema["required"] == []
