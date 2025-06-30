#!/usr/bin/env python3
"""
利用可能なMCP関数のデバッグスクリプト
"""

import asyncio
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from doc_ai_helper_backend.services.llm.openai_service import OpenAIService
from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.function_adapter import MCPFunctionAdapter


async def debug_available_functions():
    """利用可能な関数一覧をデバッグ"""
    print("🔍 MCP関数デバッグ開始")
    print("=" * 50)

    try:
        # MCPサーバーを直接初期化
        print("1. MCPサーバー初期化...")
        mcp_server = DocumentAIHelperMCPServer()
        print(f"   サーバー作成完了: {type(mcp_server)}")

        # MCPアダプター初期化
        print("2. MCPアダプター初期化...")
        mcp_adapter = MCPFunctionAdapter(mcp_server)
        print(f"   アダプター作成完了: {type(mcp_adapter)}")

        # 利用可能な関数を取得
        print("3. 利用可能な関数一覧...")
        print("   MCPアダプターから...")
        functions = await mcp_adapter.get_available_functions()
        print(f"   関数数: {len(functions)}")

        print("   MCPサーバーから直接...")
        tools = mcp_server.get_available_tools()
        print(f"   ツール数: {len(tools)}")
        print(f"   ツール一覧: {tools}")

        print("   MCPサーバーの非同期メソッドから...")
        try:
            tools_async = await mcp_server.get_available_tools_async()
            print(f"   非同期ツール数: {len(tools_async)}")
            print(f"   非同期ツール一覧: {tools_async}")
        except Exception as e:
            print(f"   非同期ツール取得エラー: {e}")

        print("   FastMCPアプリから直接...")
        try:
            fastmcp_tools = await mcp_server.app.get_tools()
            print(f"   FastMCPツール数: {len(fastmcp_tools)}")
            print(f"   FastMCPツール一覧: {list(fastmcp_tools.keys())}")
        except Exception as e:
            print(f"   FastMCPツール取得エラー: {e}")

        for i, func in enumerate(functions):
            if hasattr(func, "name"):
                print(f"   {i+1}. {func.name}: {func.description}")
            else:
                print(f"   {i+1}. {func}")

        # OpenAIサービスの関数一覧
        print("4. OpenAIサービス経由での関数一覧...")
        openai_service = OpenAIService(
            api_key="test-key", default_model="gpt-3.5-turbo"
        )

        all_functions = await openai_service.get_available_functions()
        print(f"   総関数数: {len(all_functions)}")

        for i, func in enumerate(all_functions):
            if hasattr(func, "name"):
                print(f"   {i+1}. {func.name}: {func.description}")
            else:
                print(f"   {i+1}. {func}")

        # 個別ツールの動作確認
        print("5. 個別ツール動作確認...")

        # calculateツールのテスト
        try:
            from doc_ai_helper_backend.services.mcp.tools.utility_tools import calculate

            result = await calculate("10 + 20")
            print(f"   calculate('10 + 20'): {result}")
        except Exception as e:
            print(f"   calculate エラー: {e}")

        # format_textツールのテスト
        try:
            from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
                format_text,
            )

            result = await format_text("hello world", "title")
            print(f"   format_text('hello world', 'title'): {result}")
        except Exception as e:
            print(f"   format_text エラー: {e}")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(debug_available_functions())
