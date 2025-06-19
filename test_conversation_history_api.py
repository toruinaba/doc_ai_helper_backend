"""
Test script to verify conversation history support in API endpoints.
"""

import asyncio
from typing import List, Dict, Any
from doc_ai_helper_backend.models.llm import LLMQueryRequest, MessageItem
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.api.endpoints.llm import query_llm, stream_llm_response


async def test_query_endpoint_with_conversation():
    """Test the query endpoint with conversation history."""

    # Create mock service
    mock_service = MockLLMService()

    # Create request with conversation history
    conversation_history = [
        MessageItem(role="user", content="Hello!"),
        MessageItem(role="assistant", content="Hi there! How can I help you?"),
    ]

    request = LLMQueryRequest(
        prompt="What's the weather like?",
        conversation_history=conversation_history,
        model="test-model",
    )

    # Test query endpoint
    print("Testing query endpoint...")
    try:
        response = await query_llm(request, mock_service)
        print(f"✓ Query successful: {response.content[:50]}...")
    except Exception as e:
        print(f"✗ Query failed: {e}")
        return False

    return True


async def test_stream_endpoint_with_conversation():
    """Test the stream endpoint with conversation history."""

    # Create mock service
    mock_service = MockLLMService()

    # Create request with conversation history
    conversation_history = [
        MessageItem(role="user", content="Hello!"),
        MessageItem(role="assistant", content="Hi there! How can I help you?"),
    ]

    request = LLMQueryRequest(
        prompt="Tell me a story",
        conversation_history=conversation_history,
        model="test-model",
    )

    # Test stream endpoint
    print("Testing stream endpoint...")
    try:
        response = await stream_llm_response(request, mock_service)
        print(f"✓ Stream successful: {type(response)}")
    except Exception as e:
        print(f"✗ Stream failed: {e}")
        return False

    return True


async def main():
    """Run all tests."""
    print("Testing conversation history support in API endpoints...\n")

    query_success = await test_query_endpoint_with_conversation()
    stream_success = await test_stream_endpoint_with_conversation()

    print(f"\nResults:")
    print(f"Query endpoint: {'✓ PASS' if query_success else '✗ FAIL'}")
    print(f"Stream endpoint: {'✓ PASS' if stream_success else '✗ FAIL'}")

    if query_success and stream_success:
        print("\n🎉 All tests passed! Conversation history support is working.")
    else:
        print("\n❌ Some tests failed. Please check the implementation.")


if __name__ == "__main__":
    asyncio.run(main())
