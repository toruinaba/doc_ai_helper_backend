#!/usr/bin/env python3
"""
Test script for context-aware LLM query functionality.

This script tests the new repository context and document metadata features.
"""

import asyncio
import os
import sys
from typing import Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    GitService,
    DocumentType,
)
from doc_ai_helper_backend.models.llm import LLMQueryRequest, MessageItem, MessageRole
from doc_ai_helper_backend.services.llm.openai_service import OpenAIService
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService


async def test_context_aware_query_mock():
    """Test context-aware query with MockLLMService."""
    print("=== Testing MockLLMService with Context ===")

    # Create mock service
    mock_service = MockLLMService()

    # Create repository context
    repo_context = RepositoryContext(
        owner="test-user", repo="test-repo", ref="main", service=GitService.GITHUB
    )

    # Create document metadata
    doc_metadata = DocumentMetadata(
        filename="README.md", title="Test README", type=DocumentType.MARKDOWN
    )

    # Sample document content
    doc_content = """# Test Repository

This is a test repository for demonstrating context-aware LLM queries.

## Features
- Repository context integration
- Document metadata support
- System prompt generation
"""

    try:
        # Test basic query with context
        response = await mock_service.query(
            prompt="このREADMEファイルの内容について教えてください。",
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content=doc_content,
            system_prompt_template="contextual_document_assistant_ja",
            include_document_in_system_prompt=True,
        )

        print(f"✅ Mock query succeeded")
        print(f"   Response: {response.content[:100]}...")
        print(f"   Model: {response.model}")
        print(f"   Provider: {response.provider}")

    except Exception as e:
        print(f"❌ Mock query failed: {e}")
        return False

    return True


async def test_context_aware_query_openai():
    """Test context-aware query with OpenAIService (requires API key)."""
    print("\n=== Testing OpenAIService with Context ===")

    # Check if OpenAI API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("⚠️  Skipping OpenAI test - no API key found")
        return True

    # Create OpenAI service
    openai_service = OpenAIService(api_key=api_key, default_model="gpt-3.5-turbo")

    # Create repository context
    repo_context = RepositoryContext(
        owner="microsoft", repo="vscode", ref="main", service=GitService.GITHUB
    )

    # Create document metadata
    doc_metadata = DocumentMetadata(
        filename="README.md", title="Visual Studio Code", type=DocumentType.MARKDOWN
    )

    # Sample document content
    doc_content = """# Visual Studio Code

Visual Studio Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS and Linux.

## Features
- IntelliSense
- Debugging
- Built-in Git
- Extensions
"""

    try:
        # Test basic query with context
        response = await openai_service.query(
            prompt="このリポジトリの主な特徴について日本語で教えてください。",
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content=doc_content,
            system_prompt_template="contextual_document_assistant_ja",
            include_document_in_system_prompt=True,
        )

        print(f"✅ OpenAI query succeeded")
        print(f"   Response: {response.content[:200]}...")
        print(f"   Model: {response.model}")
        print(f"   Provider: {response.provider}")
        print(
            f"   Tokens used: {response.usage.total_tokens if response.usage else 'N/A'}"
        )

    except Exception as e:
        print(f"❌ OpenAI query failed: {e}")
        return False

    return True


async def test_api_request_structure():
    """Test the new LLMQueryRequest structure."""
    print("\n=== Testing LLMQueryRequest Structure ===")

    try:
        # Create repository context
        repo_context = RepositoryContext(
            owner="example", repo="test-repo", ref="main", service=GitService.GITHUB
        )

        # Create document metadata
        doc_metadata = DocumentMetadata(
            filename="docs/api.md",
            title="API Documentation",
            type=DocumentType.MARKDOWN,
        )

        # Create LLM query request
        request = LLMQueryRequest(
            prompt="APIの使い方について説明してください。",
            provider="openai",
            model="gpt-3.5-turbo",
            repository_context=repo_context,
            document_metadata=doc_metadata,
            document_content="# API Documentation\n\nThis is the API documentation...",
            include_document_in_system_prompt=True,
            system_prompt_template="contextual_document_assistant_ja",
        )

        print(f"✅ LLMQueryRequest creation succeeded")
        print(f"   Prompt: {request.prompt}")
        if request.repository_context:
            print(
                f"   Repository: {request.repository_context.owner}/{request.repository_context.repo}"
            )
        if request.document_metadata:
            print(f"   Document: {request.document_metadata.filename}")
        print(f"   Template: {request.system_prompt_template}")

    except Exception as e:
        print(f"❌ LLMQueryRequest creation failed: {e}")
        return False

    return True


async def main():
    """Run all tests."""
    print("🚀 Starting Context-Aware LLM Tests\n")

    tests = [
        test_api_request_structure,
        test_context_aware_query_mock,
        test_context_aware_query_openai,
    ]

    results = []
    for test in tests:
        try:
            result = await test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    # Summary
    print(f"\n📊 Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("🎉 All tests passed!")
        return 0
    else:
        print("💥 Some tests failed")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
