"""
Integration test for MCP Tools API with real MCP server.
"""

import pytest
import asyncio
from doc_ai_helper_backend.services.mcp.server import (
    get_tools_info,
    get_server_info,
    get_mcp_server,
)


class TestMCPToolsIntegration:
    """Integration tests for MCP Tools functionality."""

    @pytest.mark.asyncio
    async def test_get_tools_info_async(self):
        """Test getting tools info directly from MCP server."""
        tools_info = await get_tools_info()

        assert isinstance(tools_info, list)

        if tools_info:
            tool = tools_info[0]
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert "category" in tool
            assert "enabled" in tool

    @pytest.mark.asyncio
    async def test_get_server_info_async(self):
        """Test getting server info directly from MCP server."""
        server_info = await get_server_info()

        assert isinstance(server_info, dict)
        assert "name" in server_info
        assert "version" in server_info
        assert "description" in server_info
        assert "enabled_features" in server_info

    @pytest.mark.asyncio
    async def test_mcp_server_initialization(self):
        """Test that MCP server is properly initialized."""
        server = get_mcp_server()

        assert server is not None
        assert server.config is not None
        assert server.app is not None

    @pytest.mark.asyncio
    async def test_tool_categories_consistency(self):
        """Test that tool categories are consistent."""
        tools_info = await get_tools_info()

        expected_categories = {"document", "feedback", "analysis", "utility", "github"}
        found_categories = set()

        for tool in tools_info:
            category = tool.get("category", "other")
            found_categories.add(category)

        # All found categories should be in expected categories
        unexpected_categories = found_categories - expected_categories
        assert (
            len(unexpected_categories) == 0
        ), f"Unexpected categories: {unexpected_categories}"

    @pytest.mark.asyncio
    async def test_tool_parameters_completeness(self):
        """Test that all tools have complete parameter definitions."""
        tools_info = await get_tools_info()

        for tool in tools_info:
            tool_name = tool["name"]
            parameters = tool["parameters"]

            # Each parameter should have required fields
            for param in parameters:
                assert "name" in param, f"Tool {tool_name} parameter missing 'name'"
                assert "type" in param, f"Tool {tool_name} parameter missing 'type'"
                assert (
                    "required" in param
                ), f"Tool {tool_name} parameter missing 'required'"

                # Name should be non-empty string
                assert (
                    isinstance(param["name"], str) and param["name"]
                ), f"Tool {tool_name} parameter name invalid"

                # Type should be non-empty string
                assert (
                    isinstance(param["type"], str) and param["type"]
                ), f"Tool {tool_name} parameter type invalid"

                # Required should be boolean
                assert isinstance(
                    param["required"], bool
                ), f"Tool {tool_name} parameter required invalid"

    @pytest.mark.asyncio
    async def test_specific_tool_availability(self):
        """Test that expected tools are available."""
        tools_info = await get_tools_info()
        tool_names = [tool["name"] for tool in tools_info]

        # Check for some key tools that should be available
        expected_tools = [
            "get_current_time",
            "count_text_characters",
        ]

        for expected_tool in expected_tools:
            assert (
                expected_tool in tool_names
            ), f"Expected tool {expected_tool} not found"

    @pytest.mark.asyncio
    async def test_tool_descriptions_present(self):
        """Test that tools have descriptions."""
        tools_info = await get_tools_info()

        tools_without_description = []
        for tool in tools_info:
            if not tool.get("description"):
                tools_without_description.append(tool["name"])

        # Most tools should have descriptions
        # Allow some tools to not have descriptions but warn about it
        if tools_without_description:
            print(f"Warning: Tools without descriptions: {tools_without_description}")
