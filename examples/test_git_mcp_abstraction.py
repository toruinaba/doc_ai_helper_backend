"""
Test script for Git MCP tools abstraction.

This script tests the abstraction layer that unifies GitHub and Forgejo operations.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(".")

from doc_ai_helper_backend.services.mcp.tools.git.factory import MCPGitToolsFactory
from doc_ai_helper_backend.services.mcp.tools.git_tools import (
    configure_git_service,
    get_unified_git_tools,
    create_git_issue,
    create_git_pull_request,
    check_git_repository_permissions,
)


async def test_git_abstraction():
    """Test Git MCP tools abstraction."""
    print("🏗️  Testing Git MCP Tools Abstraction")
    print("=" * 50)

    # Test 1: Factory pattern
    print("\n🏭 Testing factory pattern...")

    # Test GitHub adapter creation
    try:
        github_adapter = MCPGitToolsFactory.create(
            "github", config={"access_token": "test_token"}
        )
        print(f"✅ GitHub adapter created: {github_adapter.service_name}")
    except Exception as e:
        print(f"❌ Error creating GitHub adapter: {e}")

    # Test Forgejo adapter creation
    try:
        forgejo_adapter = MCPGitToolsFactory.create(
            "forgejo",
            config={"base_url": "http://localhost:3000", "access_token": "test_token"},
        )
        print(f"✅ Forgejo adapter created: {forgejo_adapter.service_name}")
    except Exception as e:
        print(f"❌ Error creating Forgejo adapter: {e}")

    # Test 2: Unified Git tools configuration
    print("\n🔧 Testing unified Git tools configuration...")

    # Configure GitHub service
    try:
        configure_git_service(
            "github",
            config={"access_token": os.getenv("GITHUB_TOKEN", "test_token")},
            set_as_default=True,
        )
        print("✅ GitHub service configured")
    except Exception as e:
        print(f"❌ Error configuring GitHub service: {e}")

    # Configure Forgejo service
    try:
        configure_git_service(
            "forgejo",
            config={
                "base_url": os.getenv("FORGEJO_BASE_URL", "http://localhost:3000"),
                "access_token": os.getenv("FORGEJO_TOKEN", "test_token"),
            },
        )
        print("✅ Forgejo service configured")
    except Exception as e:
        print(f"❌ Error configuring Forgejo service: {e}")

    # Test 3: Unified interface operations
    print("\n🚀 Testing unified interface operations...")

    # Test repository contexts
    github_context = {
        "service": "github",
        "owner": "octocat",
        "repo": "Hello-World",
        "repository_full_name": "octocat/Hello-World",
        "current_path": "README.md",
        "base_url": "https://github.com/octocat/Hello-World",
        "ref": "main",
    }

    forgejo_context = {
        "service": "forgejo",
        "owner": "testuser",
        "repo": "test-repo",
        "repository_full_name": "testuser/test-repo",
        "current_path": "README.md",
        "base_url": os.getenv("FORGEJO_BASE_URL", "http://localhost:3000"),
        "ref": "main",
    }

    # Test GitHub operations via unified interface
    print("\n📋 Testing GitHub operations via unified interface...")
    try:
        result = await check_git_repository_permissions(
            repository_context=github_context, service_type="github"
        )
        print(f"✅ GitHub permissions check: {result[:100]}...")
    except Exception as e:
        print(f"❌ Error in GitHub operations: {e}")

    # Test Forgejo operations via unified interface
    print("\n📋 Testing Forgejo operations via unified interface...")
    try:
        result = await check_git_repository_permissions(
            repository_context=forgejo_context, service_type="forgejo"
        )
        print(f"✅ Forgejo permissions check: {result[:100]}...")
    except Exception as e:
        print(f"❌ Error in Forgejo operations: {e}")

    # Test automatic service detection from context
    print("\n🎯 Testing automatic service detection...")
    try:
        result = await create_git_issue(
            title="Test Issue via Unified Interface",
            description="This issue was created using the unified Git tools interface",
            labels=["test", "unified"],
            repository_context=github_context,  # Service auto-detected from context
        )
        print(f"✅ Auto-detected GitHub issue creation: {result[:100]}...")
    except Exception as e:
        print(f"❌ Error in auto-detected operations: {e}")

    # Test 4: Unified tools management
    print("\n🎛️  Testing unified tools management...")

    unified_tools = get_unified_git_tools()

    try:
        configured_services = unified_tools.get_configured_services()
        default_service = unified_tools.get_default_service()

        print(f"✅ Configured services: {configured_services}")
        print(f"✅ Default service: {default_service}")
    except Exception as e:
        print(f"❌ Error in unified tools management: {e}")

    print("\n🎉 Git MCP Tools Abstraction test completed!")


if __name__ == "__main__":
    asyncio.run(test_git_abstraction())
