#!/usr/bin/env python3
"""
個別のMCPツール直接呼び出しテスト
"""

import asyncio
import sys
import os

# パスを追加
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


async def test_individual_tools():
    """個別のMCPツールを直接テスト"""
    print("🔧 個別MCPツール直接呼び出しテスト")
    print("=" * 50)

    try:
        # calculateツールのテスト
        print("1. calculate_simple_mathツール...")
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
            calculate_simple_math,
        )

        result = await calculate_simple_math(expression="100 * 25 + 75")
        print(f"   結果: {result}")

        # format_textツールのテスト（存在しない場合）
        print("2. format_textツール...")
        try:
            from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
                format_text,
            )

            result = await format_text(text="hello world", style="title")
            print(f"   結果: {result}")
        except ImportError:
            print("   format_textツールは存在しません")

        # ドキュメント分析ツール
        print("3. analyze_document_structureツール...")
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            analyze_document_structure,
        )

        result = await analyze_document_structure(
            document_content="# タイトル\n\n内容です\n\n## サブタイトル\n\nさらに内容",
            document_type="markdown",
        )
        print(f"   結果: {result}")

        # フィードバック生成ツール
        print("4. generate_feedback_from_conversationツール...")
        from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
            generate_feedback_from_conversation,
        )

        conversation = [
            {
                "role": "user",
                "content": "ドキュメントが分かりにくい",
                "timestamp": "2024-01-01T00:00:00Z",
            },
            {
                "role": "assistant",
                "content": "どの部分ですか？",
                "timestamp": "2024-01-01T00:01:00Z",
            },
        ]
        result = await generate_feedback_from_conversation(
            conversation_history=conversation,
            document_context="# サンプル文書\n内容",
            feedback_type="improvement",
        )
        print(f"   結果: {result}")

    except Exception as e:
        print(f"❌ エラー: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_individual_tools())
