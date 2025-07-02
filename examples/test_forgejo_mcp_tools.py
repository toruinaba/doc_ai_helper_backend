"""
Test script for Forgejo MCP tools integration.

This script tests the Forgejo adapter implementation for MCP tools.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(".")

from doc_ai_helper_backend.services.mcp.tools.git.forgejo_adapter import (
    MCPForgejoAdapter,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext


async def test_forgejo_mcp_tools():
    """Test Forgejo MCP tools functionality."""
    print("🔧 Testing Forgejo MCP Tools Integration")
    print("=" * 50)

    # Get Forgejo configuration from environment
    base_url = os.getenv("FORGEJO_BASE_URL", "http://localhost:3000")
    access_token = os.getenv("FORGEJO_TOKEN")
    username = os.getenv("FORGEJO_USERNAME")
    password = os.getenv("FORGEJO_PASSWORD")

    if not access_token and not (username and password):
        print("⚠️  No Forgejo authentication found")
        print(
            "   Set FORGEJO_TOKEN or FORGEJO_USERNAME/FORGEJO_PASSWORD environment variables"
        )
        print("   Testing with mock authentication...")

        # Use mock credentials for testing
        username = "testuser"
        password = "testpass"

    print(f"🌐 Forgejo Base URL: {base_url}")
    print(f"🔑 Authentication: {'Token' if access_token else 'Basic Auth'}")

    # Initialize Forgejo adapter
    try:
        adapter = MCPForgejoAdapter(
            base_url=base_url,
            access_token=access_token,
            username=username,
            password=password,
        )
        print("✅ Forgejo adapter initialized successfully")
    except Exception as e:
        print(f"❌ Failed to initialize Forgejo adapter: {e}")
        return

    # Test repository context
    test_repo_context = {
        "service": "forgejo",
        "owner": "testuser",
        "repo": "test-repo",
        "repository_full_name": "testuser/test-repo",
        "current_path": "README.md",
        "base_url": base_url,
        "ref": "main",
    }

    print(f"\n📋 Test repository context: {test_repo_context['repository_full_name']}")

    # Test 1: Check repository permissions (safe operation)
    print("\n🔐 Testing repository permissions check...")
    try:
        result = await adapter.check_repository_permissions(
            repository_context=test_repo_context
        )
        print(f"✅ Permissions check result: {result[:200]}...")
    except Exception as e:
        print(f"❌ Error checking permissions: {e}")

    # Test 2: Create issue (will fail without proper setup, but should handle gracefully)
    print("\n📝 Testing issue creation...")
    try:
        result = await adapter.create_issue(
            title="Test Issue from Forgejo MCP",
            description="This is a test issue created via Forgejo MCP tools",
            labels=["test", "mcp"],
            repository_context=test_repo_context,
        )
        print(f"📝 Issue creation result: {result[:200]}...")
    except Exception as e:
        print(f"❌ Error creating issue: {e}")

    # Test 3: Create pull request (will fail without proper setup, but should handle gracefully)
    print("\n🔀 Testing pull request creation...")
    try:
        result = await adapter.create_pull_request(
            title="Test PR from Forgejo MCP",
            description="This is a test PR created via Forgejo MCP tools",
            head_branch="feature/test",
            base_branch="main",
            repository_context=test_repo_context,
        )
        print(f"🔀 PR creation result: {result[:200]}...")
    except Exception as e:
        print(f"❌ Error creating PR: {e}")

    print("\n🎉 Forgejo MCP Tools test completed!")


if __name__ == "__main__":
    asyncio.run(test_forgejo_mcp_tools())
