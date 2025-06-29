#!/usr/bin/env python3
"""
Function Callingテスト - ツール呼び出しを明示的にテスト
"""

import asyncio
import aiohttp
import json


async def test_explicit_tool_call():
    """明示的にツール呼び出しをテスト"""

    # ドキュメント分析ツールを呼び出すプロンプト
    test_prompt = """
    Please use the analyze_document_structure tool to analyze the following markdown content:
    
    # Sample Document
    ## Introduction
    This is a sample document.
    
    ## Main Content
    - Item 1
    - Item 2
    
    ## Conclusion
    Thank you for reading.
    """

    print("🔄 明示的ツール呼び出しテスト")
    print("=" * 60)

    payload = {
        "prompt": test_prompt,
        "provider": "openai",
        "complete_tool_flow": True,
        "enable_tools": True,  # 修正: enable_function_calling -> enable_tools
        "tool_choice": "auto",
        "options": {"model": "azure-tk-gpt-4o", "temperature": 0.1, "max_tokens": 2000},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/llm/query",
            json=payload,
            headers={"Content-Type": "application/json"},
        ) as response:

            print(f"📡 HTTPステータス: {response.status}")

            if response.status == 200:
                data = await response.json()
                print(f"📝 最終応答: {data.get('content', 'なし')[:200]}...")
                print(
                    f"🔧 ツール実行結果: {data.get('tool_execution_results', 'なし')}"
                )
                print(f"🎯 モデル: {data.get('model', 'なし')}")

                # ツール実行の有無をツール関連フィールドで確認
                tool_calls = data.get("tool_calls", [])
                print(f"🛠️ ツールコール: {len(tool_calls) if tool_calls else 0}件")

                if tool_calls:
                    for i, call in enumerate(tool_calls):
                        print(
                            f"  {i+1}. {call.get('function', {}).get('name', '不明')}"
                        )

                # original_tool_callsの確認（デバッグ用フィールド）
                orig_calls = data.get("original_tool_calls", [])
                print(f"🔍 元ツールコール: {len(orig_calls) if orig_calls else 0}件")

                if orig_calls:
                    for i, call in enumerate(orig_calls):
                        print(
                            f"  {i+1}. {call.get('function', {}).get('name', '不明')}"
                        )

                # 完全レスポンスをJSONで表示
                print("\n📋 完全レスポンス:")
                print(json.dumps(data, indent=2, ensure_ascii=False))

            else:
                error_text = await response.text()
                print(f"❌ エラー: {response.status}")
                print(f"エラー詳細: {error_text}")


if __name__ == "__main__":
    asyncio.run(test_explicit_tool_call())
