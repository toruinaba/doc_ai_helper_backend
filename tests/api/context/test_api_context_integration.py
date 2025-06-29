#!/usr/bin/env python3
"""
API integration test for context-aware LLM query functionality.

This script tests the new repository context features through the actual API endpoints.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import httpx
from fastapi.testclient import TestClient

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    GitService,
    DocumentType,
)


def test_llm_query_with_context():
    """Test LLM query API with repository context."""
    print("=== Testing LLM Query API with Context ===")

    client = TestClient(app)

    # Prepare request payload with context
    request_data = {
        "prompt": "このREADMEファイルについて、リポジトリの概要を日本語で教えてください。",
        "provider": "mock",  # Use mock provider for testing
        "repository_context": {
            "owner": "microsoft",
            "repo": "vscode",
            "ref": "main",
            "service": "github",
            "current_path": "README.md",
        },
        "document_metadata": {
            "filename": "README.md",
            "title": "Visual Studio Code README",
            "type": "markdown",
        },
        "document_content": """# Visual Studio Code

Visual Studio Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS and Linux.

## Features
- IntelliSense
- Debugging  
- Built-in Git
- Extensions
""",
        "include_document_in_system_prompt": True,
        "system_prompt_template": "contextual_document_assistant_ja",
    }

    try:
        # Send POST request to LLM query endpoint
        response = client.post("/api/v1/llm/query", json=request_data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ API query succeeded")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Content: {result.get('content', 'N/A')[:100]}...")
            print(f"   Model: {result.get('model', 'N/A')}")
            print(f"   Provider: {result.get('provider', 'N/A')}")
            return True
        else:
            print(f"❌ API query failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ API query failed with exception: {e}")
        return False


def test_llm_query_without_context():
    """Test LLM query API without repository context (baseline)."""
    print("\n=== Testing LLM Query API without Context ===")

    client = TestClient(app)

    # Prepare request payload without context
    request_data = {
        "prompt": "Hello, how are you?",
        "provider": "mock",  # Use mock provider for testing
    }

    try:
        # Send POST request to LLM query endpoint
        response = client.post("/api/v1/llm/query", json=request_data)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ API query without context succeeded")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response Content: {result.get('content', 'N/A')[:100]}...")
            print(f"   Model: {result.get('model', 'N/A')}")
            print(f"   Provider: {result.get('provider', 'N/A')}")
            return True
        else:
            print(f"❌ API query without context failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ API query without context failed with exception: {e}")
        return False


def test_api_capabilities():
    """Test API capabilities endpoint."""
    print("\n=== Testing API Capabilities ===")

    client = TestClient(app)

    try:
        # Send GET request to capabilities endpoint
        response = client.get("/api/v1/llm/capabilities")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Capabilities endpoint succeeded")
            print(f"   Status Code: {response.status_code}")
            print(f"   Available models: {result.get('available_models', [])}")
            print(f"   Supports streaming: {result.get('supports_streaming', False)}")
            print(
                f"   Supports function calling: {result.get('supports_function_calling', False)}"
            )
            return True
        else:
            print(f"❌ Capabilities endpoint failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Capabilities endpoint failed with exception: {e}")
        return False


def test_health_endpoint():
    """Test health endpoint."""
    print("\n=== Testing Health Endpoint ===")

    client = TestClient(app)

    try:
        # Send GET request to health endpoint
        response = client.get("/health")

        if response.status_code == 200:
            result = response.json()
            print(f"✅ Health endpoint succeeded")
            print(f"   Status Code: {response.status_code}")
            print(f"   Status: {result.get('status', 'N/A')}")
            return True
        else:
            print(f"❌ Health endpoint failed")
            print(f"   Status Code: {response.status_code}")
            print(f"   Response: {response.text}")
            return False

    except Exception as e:
        print(f"❌ Health endpoint failed with exception: {e}")
        return False


def main():
    """Run all API integration tests."""
    print("🚀 Starting API Integration Tests for Context-Aware LLM\n")

    tests = [
        test_health_endpoint,
        test_api_capabilities,
        test_llm_query_without_context,
        test_llm_query_with_context,
    ]

    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            results.append(False)

    # Summary
    print(f"\n📊 API Test Results: {sum(results)}/{len(results)} passed")

    if all(results):
        print("🎉 All API tests passed!")
        return 0
    else:
        print("💥 Some API tests failed")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
