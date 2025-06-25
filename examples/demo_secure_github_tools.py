#!/usr/bin/env python3
"""
Demonstration script for secure GitHub tools with repository context.

This script demonstrates how the repository context validation works
to prevent unauthorized repository access through MCP tools.
"""

import asyncio
import json
import logging
from typing import Dict, Any
import sys

sys.path.append(".")

from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.services.mcp.tools.github_tools import (
    create_github_issue,
    create_github_pull_request,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def demo_github_tools():
    """Demonstrate secure GitHub tools with repository context validation."""

    print("🔐 Secure GitHub Tools Demo")
    print("=" * 50)

    # Scenario 1: User is viewing a document in test-owner/test-repo
    print("\n📍 Scenario 1: User viewing document in test-owner/test-repo")

    repository_context = {
        "service": "github",
        "owner": "test-owner",
        "repo": "test-repo",
        "ref": "main",
        "current_path": "docs/README.md",
    }

    print(
        f"Current repository context: {repository_context['owner']}/{repository_context['repo']}"
    )

    # Try to create an issue in the current repository context (should succeed)
    print("\n✅ Creating issue in current repository context...")
    try:
        result = await create_github_issue(
            title="Improve README structure",
            description="The current README.md structure could be improved for better readability.",
            labels=["documentation", "enhancement"],
            repository_context=repository_context,
        )

        result_data = json.loads(result)
        if result_data.get("success"):
            print(f"   ✅ Issue created successfully!")
            print(f"   📌 Repository: {result_data['issue']['repository']}")
            print(
                f"   🔒 Context validated: {result_data['issue']['context_validated']}"
            )
        else:
            print(f"   ❌ Failed: {result_data.get('error')}")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

    # Scenario 2: No repository context provided
    print("\n📍 Scenario 2: No repository context provided")
    print("Current repository context: None")

    print("\n❌ Attempting to create issue without context...")
    try:
        result = await create_github_issue(
            title="Test issue",
            description="This should fail due to missing context.",
            repository_context=None,
        )

        result_data = json.loads(result)
        print(f"   🚫 Expected failure: {result_data.get('error')}")
        print(f"   📝 Error type: {result_data.get('error_type')}")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

    # Scenario 3: Demonstrate repository context auto-injection
    print("\n📍 Scenario 3: Repository context auto-injection")

    # Show how the LLM would interact with secure tools
    print(
        "User message: 'この README.md の改善提案を GitHub Issue として投稿してください'"
    )
    print("System: Extracting repository context from current document view...")

    repo_ctx = RepositoryContext(
        service="github",
        owner="microsoft",
        repo="vscode",
        ref="main",
        current_path="README.md",
    )

    print(f"System: Auto-detected repository: {repo_ctx.repository_full_name}")
    print("System: Creating issue with auto-injected repository context...")

    try:
        result = await create_github_issue(
            title="README improvement suggestions",
            description="Based on the current README.md analysis, here are some improvement suggestions:\n\n"
            "1. Add more code examples\n"
            "2. Improve section organization\n"
            "3. Add troubleshooting section",
            labels=["documentation", "enhancement"],
            repository_context={
                "service": repo_ctx.service,
                "owner": repo_ctx.owner,
                "repo": repo_ctx.repo,
                "ref": repo_ctx.ref,
                "current_path": repo_ctx.current_path,
            },
        )

        result_data = json.loads(result)
        if result_data.get("success"):
            print(
                f"   ✅ Issue would be created in: {result_data['issue']['repository']}"
            )
            print(f"   🔒 Security: Context validated automatically")
        else:
            print(f"   ❌ Would fail: {result_data.get('error')}")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")

    # Scenario 4: Benefits summary
    print("\n📋 Security Benefits Summary")
    print("=" * 50)
    print("✅ Repository access is restricted to current context")
    print("✅ No need for users to specify repository manually")
    print("✅ Prevents accidental operations on wrong repositories")
    print("✅ Maintains backward compatibility with explicit repository parameters")
    print("✅ Provides clear error messages for unauthorized access attempts")

    print("\n🔧 Implementation Details")
    print("=" * 50)
    print("• Repository context is automatically extracted from document view")
    print("• Secure tools validate context before executing operations")
    print("• LLM Function Calling integrates seamlessly with context validation")
    print("• Error handling provides informative feedback to users")


def demo_parameter_comparison():
    """Demonstrate the difference in parameters between regular and secure tools."""

    print("\n🔄 Tool Parameter Comparison")
    print("=" * 50)

    print("\n📊 Regular GitHub Tools:")
    print("  create_github_issue:")
    print("    - repository: str (required) ⚠️  User must specify")
    print("    - title: str (required)")
    print("    - description: str (required)")
    print("    - labels: List[str] (optional)")
    print("    - assignees: List[str] (optional)")

    print("\n🔒 Secure GitHub Tools:")
    print("  create_github_issue:")
    print("    - title: str (required)")
    print("    - description: str (required)")
    print("    - labels: List[str] (optional)")
    print("    - assignees: List[str] (optional)")
    print("    - repository_context: auto-injected 🔐")

    print("\n💡 Key Differences:")
    print("• Secure tools don't expose 'repository' parameter to LLM")
    print("• Repository is automatically determined from context")
    print("• Simpler LLM interaction (fewer parameters to manage)")
    print("• Enhanced security through context validation")


async def main():
    """Main demonstration function."""

    print("🚀 Starting Secure GitHub Tools Demonstration")
    print()

    # Demo the secure tools functionality
    await demo_github_tools()

    # Demo parameter comparison
    demo_parameter_comparison()

    print("\n✨ Demo completed successfully!")
    print("\nNext steps:")
    print("1. Test with real GitHub API tokens in development environment")
    print("2. Integrate with frontend for full E2E testing")
    print("3. Monitor usage patterns and security effectiveness")


if __name__ == "__main__":
    asyncio.run(main())
