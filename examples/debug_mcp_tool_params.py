#!/usr/bin/env python3
"""
Debug script to test MCP tool parameter passing.
"""

import asyncio
import sys

sys.path.append(".")

from doc_ai_helper_backend.services.mcp import get_mcp_server


async def test_direct_tool_call():
    """Test direct MCP tool invocation."""
    server = get_mcp_server()

    print("📋 Available tools:")
    tools = await server.get_available_tools_async()
    for tool in tools:
        print(f"  - {tool}")

    print("\n🧮 Testing calculate_simple_math directly...")
    try:
        result = await server.call_tool("calculate_simple_math", expression="2+3")
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")

    print("\n🧮 Testing calculate_simple_math with different kwargs...")
    try:
        result = await server.call_tool(
            "calculate_simple_math", **{"expression": "10*5"}
        )
        print(f"Result: {result}")
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(test_direct_tool_call())
