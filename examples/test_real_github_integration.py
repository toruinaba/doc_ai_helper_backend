#!/usr/bin/env python3
"""
Real GitHub API integration test for secure tools.

This script demonstrates actual GitHub API integration with proper authentication.
Set GITHUB_TOKEN environment variable before running.
"""

import asyncio
import json
import os
import logging
import sys

sys.path.append(".")

from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.services.mcp.tools.secure_github_tools import (
    create_github_issue_secure,
    create_github_pull_request_secure,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_real_github_integration():
    """Test with real GitHub API (requires GITHUB_TOKEN)."""

    github_token = os.getenv("GITHUB_TOKEN")
    if not github_token:
        print("⚠️  GITHUB_TOKEN environment variable not set")
        print("   Set it with: export GITHUB_TOKEN=your_github_token")
        print("   Then run this script again")
        return

    print("🔐 Real GitHub API Integration Test")
    print("=" * 50)

    # Use a test repository (create a test repo first)
    test_repo_context = {
        "service": "github",
        "owner": "your-username",  # Update this to your GitHub username
        "repo": "test-repo",  # Update this to your test repository
        "ref": "main",
        "current_path": "README.md",
    }

    print(
        f"Target repository: {test_repo_context['owner']}/{test_repo_context['repo']}"
    )
    print("⚠️  Make sure this repository exists and you have write access")
    print()

    # Test creating an issue
    print("🎯 Testing issue creation...")
    try:
        result = await create_github_issue_secure(
            title="[TEST] Secure GitHub Tools Integration Test",
            description="This is a test issue created by the secure GitHub tools.\n\n"
            "Features tested:\n"
            "- Repository context validation\n"
            "- Secure tool parameter handling\n"
            "- GitHub API integration\n\n"
            "This issue can be safely closed.",
            labels=["test", "automation"],
            github_token=github_token,
            repository_context=test_repo_context,
        )

        result_data = json.loads(result)
        if result_data.get("success"):
            issue_url = result_data["issue"]["url"]
            issue_number = result_data["issue"]["number"]
            print(f"   ✅ Issue created successfully!")
            print(f"   📌 Issue #{issue_number}: {issue_url}")
            print(
                f"   🔒 Context validated: {result_data['issue']['context_validated']}"
            )
        else:
            print(f"   ❌ Failed: {result_data.get('error')}")

    except Exception as e:
        print(f"   ❌ Error: {str(e)}")


if __name__ == "__main__":
    asyncio.run(test_real_github_integration())
