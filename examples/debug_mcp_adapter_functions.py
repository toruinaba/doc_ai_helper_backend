#!/usr/bin/env python3
"""
MCPアダプターが提供する関数定義をデバッグするスクリプト
"""

import asyncio
import sys

sys.path.append(".")

from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter
from doc_ai_helper_backend.services.mcp import get_mcp_server


async def debug_mcp_adapter_functions():
    """MCPアダプターが提供する関数定義をデバッグ"""
    print("🔍 MCP Adapter Functions Debug")
    print("=" * 50)

    # MCPサーバーとアダプターを作成
    mcp_server = get_mcp_server()
    mcp_adapter = MCPFunctionAdapter(mcp_server)

    # MCPサーバーから直接利用可能なツールを取得
    server_tools = await mcp_server.get_available_tools_async()
    print(f"📋 MCP Server tools: {len(server_tools)}")
    for tool in server_tools:
        print(f"  - {tool}")

    # MCPアダプターから利用可能な関数を取得
    adapter_functions = await mcp_adapter.get_available_functions()
    print(f"\n📋 MCP Adapter functions: {len(adapter_functions)}")

    # 特定の関数を詳しく調査
    target_functions = [
        "calculate_simple_math",
        "extract_document_context",
        "optimize_document_content",
    ]

    for target in target_functions:
        print(f"\n🔍 Function: {target}")
        print("-" * 30)

        # サーバーに存在するか
        if target in server_tools:
            print(f"✅ Exists in MCP Server")

            # アダプターの関数リストに存在するか
            matching_functions = [
                f for f in adapter_functions if hasattr(f, "name") and f.name == target
            ]
            if matching_functions:
                func = matching_functions[0]
                print(f"✅ Exists in MCP Adapter")
                print(f"   Name: {func.name}")
                print(f"   Description: {func.description}")
                print(f"   Parameters: {func.parameters}")
            else:
                print(f"❌ Missing from MCP Adapter!")
        else:
            print(f"❌ Missing from MCP Server!")


if __name__ == "__main__":
    asyncio.run(debug_mcp_adapter_functions())
