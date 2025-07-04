"""
Demonstration of multi-Git service MCP integration.

This script demonstrates how the unified Git tools can work with multiple
Git services (GitHub, Forgejo) simultaneously.
"""

import asyncio
import os
import sys

# Add project root to path
sys.path.append(".")

from doc_ai_helper_backend.services.mcp import get_mcp_server
from doc_ai_helper_backend.services.mcp.tools.git_tools import (
    configure_git_service,
    get_unified_git_tools,
)


async def demo_multi_git_mcp():
    """Demonstrate multi-Git service MCP operations."""
    print("🌐 Multi-Git Service MCP Integration Demo")
    print("=" * 50)

    # Initialize MCP server
    print("\n🔧 Initializing MCP server...")
    try:
        mcp_server = get_mcp_server()
        print("✅ MCP server initialized")
    except Exception as e:
        print(f"❌ Failed to initialize MCP server: {e}")
        return

    # Configure multiple Git services
    print("\n⚙️  Configuring multiple Git services...")

    # Configure GitHub
    github_token = os.getenv("GITHUB_TOKEN")
    if github_token:
        try:
            configure_git_service(
                "github", config={"access_token": github_token}, set_as_default=True
            )
            print("✅ GitHub service configured with token")
        except Exception as e:
            print(f"❌ Failed to configure GitHub: {e}")
    else:
        print("⚠️  No GitHub token found, skipping GitHub configuration")

    # Configure Forgejo
    forgejo_base_url = os.getenv("FORGEJO_BASE_URL")
    forgejo_token = os.getenv("FORGEJO_TOKEN")
    forgejo_username = os.getenv("FORGEJO_USERNAME")
    forgejo_password = os.getenv("FORGEJO_PASSWORD")

    if forgejo_base_url and (forgejo_token or (forgejo_username and forgejo_password)):
        try:
            configure_git_service(
                "forgejo",
                config={
                    "base_url": forgejo_base_url,
                    "access_token": forgejo_token,
                    "username": forgejo_username,
                    "password": forgejo_password,
                },
            )
            print("✅ Forgejo service configured")
        except Exception as e:
            print(f"❌ Failed to configure Forgejo: {e}")
    else:
        print("⚠️  No Forgejo configuration found, skipping Forgejo configuration")

    # Show configured services
    unified_tools = get_unified_git_tools()
    configured_services = unified_tools.get_configured_services()
    default_service = unified_tools.get_default_service()

    print(f"\n📋 Configured services: {configured_services}")
    print(f"🎯 Default service: {default_service}")

    # Demo repository contexts
    demo_repositories = []

    if "github" in configured_services:
        demo_repositories.append(
            {
                "name": "GitHub Demo Repository",
                "context": {
                    "service": "github",
                    "owner": "octocat",
                    "repo": "Hello-World",
                    "repository_full_name": "octocat/Hello-World",
                    "current_path": "README.md",
                    "base_url": "https://github.com/octocat/Hello-World",
                    "ref": "main",
                },
            }
        )

    if "forgejo" in configured_services:
        demo_repositories.append(
            {
                "name": "Forgejo Demo Repository",
                "context": {
                    "service": "forgejo",
                    "owner": "testuser",
                    "repo": "test-repo",
                    "repository_full_name": "testuser/test-repo",
                    "current_path": "README.md",
                    "base_url": forgejo_base_url,
                    "ref": "main",
                },
            }
        )

    # Test operations on each configured service
    print(f"\n🧪 Testing operations on {len(demo_repositories)} repositories...")

    for repo_info in demo_repositories:
        repo_name = repo_info["name"]
        repo_context = repo_info["context"]
        service_type = repo_context["service"]

        print(f"\n📂 Testing {repo_name} ({service_type})...")

        # Set repository context in MCP server
        setattr(mcp_server, "_current_repository_context", repo_context)

        # Test 1: Check repository permissions
        print(f"   🔐 Checking repository permissions...")
        try:
            result = await mcp_server.call_tool(
                "check_git_repository_permissions", service_type=service_type
            )
            print(f"   ✅ Permissions check result: {'success' in result.lower()}")
        except Exception as e:
            print(f"   ❌ Error checking permissions: {str(e)[:100]}...")

        # Test 2: Create test issue (will be handled gracefully)
        print(f"   📝 Testing issue creation...")
        try:
            result = await mcp_server.call_tool(
                "create_git_issue",
                title=f"Test Issue from {repo_name}",
                description=f"This is a test issue created via {service_type} MCP tools",
                labels=["test", "mcp", service_type],
                service_type=service_type,
            )
            print(f"   ✅ Issue creation handled: {'success' in result.lower()}")
        except Exception as e:
            print(f"   ❌ Error creating issue: {str(e)[:100]}...")

    # Demonstrate service switching
    print(f"\n🔄 Demonstrating service switching...")

    if len(configured_services) > 1:
        print("   📋 Available services for switching:")
        for i, service in enumerate(configured_services):
            print(f"      {i+1}. {service}")

        # Switch default service
        original_default = unified_tools.get_default_service()
        new_default = [s for s in configured_services if s != original_default][0]

        try:
            unified_tools.set_default_service(new_default)
            print(
                f"   ✅ Switched default service from {original_default} to {new_default}"
            )

            # Switch back
            if original_default:
                unified_tools.set_default_service(original_default)
                print(f"   ✅ Switched back to {original_default}")
        except Exception as e:
            print(f"   ❌ Error switching services: {e}")
    else:
        print("   ⚠️  Only one service configured, cannot demonstrate switching")

    # Test MCP server tool listing
    print(f"\n📋 Available MCP tools...")
    try:
        available_tools = await mcp_server.get_available_tools_async()
        git_tools = [tool for tool in available_tools if "git" in tool.lower()]

        print(f"   📋 Total tools: {len(available_tools)}")
        print(f"   🔧 Git-related tools: {len(git_tools)}")
        for tool in git_tools:
            print(f"      - {tool}")
    except Exception as e:
        print(f"   ❌ Error listing tools: {e}")

    print("\n🎉 Multi-Git Service MCP Integration Demo completed!")
    print("=" * 50)
    print("🔍 Summary:")
    print(f"   - Configured services: {len(configured_services)}")
    print(f"   - Tested repositories: {len(demo_repositories)}")
    print(f"   - Default service: {unified_tools.get_default_service()}")
    print("\n💡 Next steps:")
    print("   - Configure your Git services in .env file")
    print("   - Set up real repositories for testing")
    print("   - Integrate with frontend applications")


if __name__ == "__main__":
    asyncio.run(demo_multi_git_mcp())
