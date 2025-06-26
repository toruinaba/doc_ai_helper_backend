#!/usr/bin/env python3
"""
Test GitHub MCP tools integration.
"""

import asyncio
import os
import sys

sys.path.append(".")

from doc_ai_helper_backend.services.mcp import get_mcp_server


async def test_github_mcp_tools():
    """Test GitHub MCP tools through the server."""
    server = get_mcp_server()

    print("🔍 Testing GitHub MCP Tools Integration")
    print("=" * 50)

    # Check if GitHub token is available
    github_token = os.getenv("GITHUB_TOKEN") or os.getenv("GITHUB_ACCESS_TOKEN")
    if github_token:
        print(f"✅ GitHub token found: {github_token[:8]}***")
    else:
        print("⚠️  No GitHub token found in environment variables")
        print("   Set GITHUB_TOKEN environment variable for full functionality")

    # List available tools to see if GitHub tools are included
    tools = await server.get_available_tools_async()
    github_tools = [tool for tool in tools if "github" in tool.lower()]

    print(f"\n📋 Available GitHub tools: {len(github_tools)}")
    for tool in github_tools:
        print(f"  - {tool}")

    if not github_tools:
        print("❌ No GitHub tools found in MCP server")
        return

    # Create a mock repository context for testing
    repository_context = {
        "service": "github",
        "owner": "octocat",
        "repo": "Hello-World",
        "repository_full_name": "octocat/Hello-World",
        "current_path": "README.md",
        "base_url": "https://github.com/octocat/Hello-World",
    }

    # Test GitHub repository permissions check (safe operation)
    print("\n🔐 Testing GitHub repository permissions check...")
    try:
        result = await server.call_tool(
            "check_github_repository_permissions",
            github_token=github_token,
            repository_context=repository_context,
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
            title="Test Issue from MCP",
            description="This is a test issue created via MCP tools",
            github_token=github_token,
            repository_context=repository_context,
        )
        print(f"📝 Issue creation result: {result}")
    except Exception as e:
        print(f"❌ Error creating issue: {e}")

    print("\n🎉 GitHub MCP Tools test completed!")


if __name__ == "__main__":
    asyncio.run(test_github_mcp_tools())
