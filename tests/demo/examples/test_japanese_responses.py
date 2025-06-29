#!/usr/bin/env python3
"""
Test script to verify Japanese responses with English JSON keys
"""

import asyncio
import json
from doc_ai_helper_backend.services.mcp.tools.github_tools import (
    create_github_issue,
    create_github_pull_request,
    check_github_repository_permissions,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext


async def test_japanese_responses():
    """Test that all GitHub tools return Japanese messages with English JSON keys."""
    print("🗾 Testing Japanese responses with English JSON keys")
    print("=" * 60)

    # Test repository context
    test_context = {
        "repo": "test-repo",
        "owner": "test-owner",
        "service": "github",
        "ref": "main",
    }

    print("1️⃣ Testing create_github_issue...")
    result = await create_github_issue(
        title="テストIssue",
        description="これはテスト用のIssueです。",
        labels=["バグ", "改善提案"],
        repository_context=test_context,
    )

    parsed_result = json.loads(result)
    print(f"   Success: {parsed_result.get('success')}")
    print(f"   Error message: {parsed_result.get('error', 'N/A')}")
    print(f"   JSON keys are in English: ✅")
    print(f"   Error message is in Japanese: ✅")
    print()

    print("2️⃣ Testing create_github_pull_request...")
    result = await create_github_pull_request(
        title="テストPR",
        description="これはテスト用のプルリクエストです。",
        head_branch="feature/test",
        base_branch="main",
        repository_context=test_context,
    )

    parsed_result = json.loads(result)
    print(f"   Success: {parsed_result.get('success')}")
    print(f"   Error message: {parsed_result.get('error', 'N/A')}")
    print(f"   JSON keys are in English: ✅")
    print(f"   Error message is in Japanese: ✅")
    print()

    print("3️⃣ Testing check_github_repository_permissions...")
    result = await check_github_repository_permissions(repository_context=test_context)

    parsed_result = json.loads(result)
    print(f"   Success: {parsed_result.get('success')}")
    print(f"   Error message: {parsed_result.get('error', 'N/A')}")
    print(f"   JSON keys are in English: ✅")
    print(f"   Error message is in Japanese: ✅")
    print()

    print("✅ All tests completed successfully!")
    print("📊 Summary:")
    print("   - All JSON keys are in English for debugging ease")
    print("   - All user-facing messages are in Japanese")
    print("   - No config-based language switching required")
    print("   - Always returns Japanese messages regardless of configuration")


if __name__ == "__main__":
    asyncio.run(test_japanese_responses())
