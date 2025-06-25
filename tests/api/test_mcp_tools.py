"""
Test for MCP Tools API endpoints.
"""

import pytest
from fastapi.testclient import TestClient
from doc_ai_helper_backend.main import app


@pytest.fixture
def client():
    """Test client fixture."""
    return TestClient(app)


class TestMCPToolsAPI:
    """Test class for MCP Tools API endpoints."""

    def test_get_mcp_tools(self, client):
        """Test getting all MCP tools."""
        response = client.get("/api/v1/llm/tools")

        assert response.status_code == 200
        data = response.json()

        # Check response structure
        assert "tools" in data
        assert "total_count" in data
        assert "categories" in data
        assert "server_info" in data

        # Check that we have tools
        assert isinstance(data["tools"], list)
        assert data["total_count"] >= 0
        assert isinstance(data["categories"], list)
        assert isinstance(data["server_info"], dict)

        # If tools exist, check their structure
        if data["tools"]:
            tool = data["tools"][0]
            assert "name" in tool
            assert "description" in tool
            assert "parameters" in tool
            assert "category" in tool
            assert "enabled" in tool

            # Check parameters structure if they exist
            if tool["parameters"]:
                param = tool["parameters"][0]
                assert "name" in param
                assert "type" in param
                assert "required" in param

    def test_get_mcp_tool_specific(self, client):
        """Test getting a specific MCP tool."""
        # First get all tools to find a valid tool name
        response = client.get("/api/v1/llm/tools")
        assert response.status_code == 200

        data = response.json()
        if not data["tools"]:
            pytest.skip("No tools available to test")

        # Test getting the first tool
        tool_name = data["tools"][0]["name"]
        response = client.get(f"/api/v1/llm/tools/{tool_name}")

        assert response.status_code == 200
        tool_data = response.json()

        # Check tool structure
        assert tool_data["name"] == tool_name
        assert "description" in tool_data
        assert "parameters" in tool_data
        assert "category" in tool_data
        assert "enabled" in tool_data

    def test_get_mcp_tool_not_found(self, client):
        """Test getting a non-existent MCP tool."""
        response = client.get("/api/v1/llm/tools/nonexistent_tool")

        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()

    def test_mcp_tools_categories(self, client):
        """Test that MCP tools are properly categorized."""
        response = client.get("/api/v1/llm/tools")
        assert response.status_code == 200

        data = response.json()
        categories = data["categories"]

        # Check that we have expected categories
        expected_categories = ["document", "feedback", "analysis", "utility"]
        for category in expected_categories:
            # Note: categories might not all be present if tools are disabled
            if category in categories:
                # Find tools in this category
                category_tools = [
                    tool for tool in data["tools"] if tool["category"] == category
                ]
                assert len(category_tools) > 0

    def test_mcp_server_info(self, client):
        """Test that server info is included in response."""
        response = client.get("/api/v1/llm/tools")
        assert response.status_code == 200

        data = response.json()
        server_info = data["server_info"]

        # Check server info structure
        assert "name" in server_info
        assert "version" in server_info
        assert "description" in server_info
        assert "enabled_features" in server_info

        # Check enabled features
        features = server_info["enabled_features"]
        expected_features = [
            "document_tools",
            "feedback_tools",
            "analysis_tools",
            "github_tools",
            "utility_tools",
        ]
        for feature in expected_features:
            assert feature in features
            assert isinstance(features[feature], bool)

    def test_tool_parameters_validation(self, client):
        """Test that tool parameters are properly structured."""
        response = client.get("/api/v1/llm/tools")
        assert response.status_code == 200

        data = response.json()

        for tool in data["tools"]:
            for param in tool["parameters"]:
                # Check required fields
                assert "name" in param
                assert "type" in param
                assert "required" in param

                # Check data types
                assert isinstance(param["name"], str)
                assert isinstance(param["type"], str)
                assert isinstance(param["required"], bool)

                # Optional fields should be properly typed if present
                if "description" in param:
                    assert isinstance(param["description"], str)
                if "default" in param:
                    # Default can be any type
                    pass
