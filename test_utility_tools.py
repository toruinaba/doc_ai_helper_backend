#!/usr/bin/env python3
"""
Test script for utility tools and Function Calling integration.
"""

import asyncio
import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.models.llm import LLMQueryRequest


async def test_utility_function_calling():
    """Test utility function calling with MockLLMService."""
    print("🧪 Testing Utility Function Calling with MockLLMService...")

    # Create mock LLM service
    mock_service = LLMServiceFactory.create("mock", response_delay=0.1)

    # Test 1: Current time function
    print("\n1️⃣ Testing current time function...")
    time_request = LLMQueryRequest(
        prompt="What is the current time?", enable_tools=True
    )

    time_functions = await mock_service.get_available_functions()
    utility_functions = [f for f in time_functions if "time" in f.name.lower()]

    if utility_functions:
        print(f"   ✅ Found utility functions: {[f.name for f in utility_functions]}")

        # Test with tools
        response = await mock_service.query_with_tools(
            prompt=time_request.prompt,
            tools=utility_functions,
            options={"enable_tools": True},
        )

        print(f"   📤 Response: {response.content}")
        if response.tool_calls:
            print(f"   🔧 Tool calls: {len(response.tool_calls)}")
            for call in response.tool_calls:
                print(f"      - {call.function.name}: {call.function.arguments}")

                # Execute the function call
                # Get available functions dict for execution
                all_funcs = await mock_service.get_available_functions()
                funcs_dict = {f.name: f for f in all_funcs}

                result = await mock_service.execute_function_call(
                    call.function, funcs_dict
                )
                print(f"      - Result: {result}")
        else:
            print("   ⚠️ No tool calls generated")
    else:
        print("   ❌ No utility functions found")

    # Test 2: Character count function
    print("\n2️⃣ Testing character count function...")
    count_request = LLMQueryRequest(
        prompt="Count the characters in this text: Hello World!", enable_tools=True
    )

    all_functions = await mock_service.get_available_functions()
    count_functions = [f for f in all_functions if "count" in f.name.lower()]

    if count_functions:
        print(f"   ✅ Found count functions: {[f.name for f in count_functions]}")

        response = await mock_service.query_with_tools(
            prompt=count_request.prompt,
            tools=count_functions,
            options={"enable_tools": True},
        )

        print(f"   📤 Response: {response.content}")
        if response.tool_calls:
            print(f"   🔧 Tool calls: {len(response.tool_calls)}")
            for call in response.tool_calls:
                print(f"      - {call.function.name}: {call.function.arguments}")

                result = await mock_service.execute_function_call(call.function)
                print(f"      - Result: {result}")
        else:
            print("   ⚠️ No tool calls generated")
    else:
        print("   ❌ No count functions found")

    # Test 3: Email validation function
    print("\n3️⃣ Testing email validation function...")
    email_request = LLMQueryRequest(
        prompt="Validate this email address: test@example.com", enable_tools=True
    )

    email_functions = [
        f
        for f in all_functions
        if "email" in f.name.lower() or "validate" in f.name.lower()
    ]

    if email_functions:
        print(f"   ✅ Found email functions: {[f.name for f in email_functions]}")

        response = await mock_service.query_with_tools(
            prompt=email_request.prompt,
            tools=email_functions,
            options={"enable_tools": True},
        )

        print(f"   📤 Response: {response.content}")
        if response.tool_calls:
            print(f"   🔧 Tool calls: {len(response.tool_calls)}")
            for call in response.tool_calls:
                print(f"      - {call.function.name}: {call.function.arguments}")

                result = await mock_service.execute_function_call(call.function)
                print(f"      - Result: {result}")
        else:
            print("   ⚠️ No tool calls generated")
    else:
        print("   ❌ No email functions found")

    print("\n✨ Utility function calling test completed!")


async def test_api_endpoint_integration():
    """Test API endpoint integration with utility tools."""
    print("\n🌐 Testing API Endpoint Integration...")

    try:
        import httpx

        # Test with a real HTTP request to the API
        async with httpx.AsyncClient() as client:
            # Test current time request
            time_request_data = {
                "prompt": "What is the current time?",
                "enable_tools": True,
                "tool_choice": "auto",
            }

            print("   📡 Sending request to API endpoint...")
            response = await client.post(
                "http://localhost:8000/api/v1/llm/query",
                json=time_request_data,
                timeout=30.0,
            )

            if response.status_code == 200:
                result = response.json()
                print(f"   ✅ API Response: {result.get('content', 'No content')}")

                if result.get("tool_execution_results"):
                    print(
                        f"   🔧 Tool execution results: {result['tool_execution_results']}"
                    )
                else:
                    print("   ⚠️ No tool execution results")
            else:
                print(
                    f"   ❌ API request failed: {response.status_code} - {response.text}"
                )

    except ImportError:
        print("   ⚠️ httpx not available, skipping API endpoint test")
    except Exception as e:
        print(f"   ❌ API endpoint test failed: {e}")


async def main():
    """Main test function."""
    print("🚀 Starting Utility Tools Function Calling Tests...")

    try:
        await test_utility_function_calling()
        await test_api_endpoint_integration()

        print("\n🎉 All tests completed!")

    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
