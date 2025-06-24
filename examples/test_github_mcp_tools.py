#!/usr/bin/env python3
"""
Test GitHub MCP tools integration.
"""

import asyncio
import sys

sys.path.append(".")

from doc_ai_helper_backend.services.mcp import get_mcp_server


async def test_github_mcp_tools():
    """Test GitHub MCP tools through the server."""
    server = get_mcp_server()

    print("🔍 Testing GitHub MCP Tools Integration")
    print("=" * 50)

    # List available tools to see if GitHub tools are included
    tools = await server.get_available_tools_async()
    github_tools = [tool for tool in tools if "github" in tool.lower()]

    print(f"📋 Available GitHub tools: {len(github_tools)}")
    for tool in github_tools:
        print(f"  - {tool}")

    if not github_tools:
        print("❌ No GitHub tools found in MCP server")
        return

    # Test GitHub repository permissions check (safe operation)
    print("\n🔐 Testing GitHub repository permissions check...")
    try:
        result = await server.call_tool(
            "check_github_repository_permissions",
            repository="octocat/Hello-World",  # public repo for testing
        )
        print(f"✅ Permissions check result: {result}")
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")

    # Test GitHub issue creation (will fail without proper token, but should be properly handled)
    print(
        "\n📝 Testing GitHub issue creation (without token - expected to handle gracefully)..."
    )
    try:
        result = await server.call_tool(
            "create_github_issue",
            repository="octocat/Hello-World",
            title="Test Issue from MCP",
            description="This is a test issue created via MCP tools",
        )
        print(f"📝 Issue creation result: {result}")
    except Exception as e:
        print(f"❌ Error creating issue: {e}")

    print("\n🎉 GitHub MCP Tools test completed!")


if __name__ == "__main__":
    asyncio.run(test_github_mcp_tools())
