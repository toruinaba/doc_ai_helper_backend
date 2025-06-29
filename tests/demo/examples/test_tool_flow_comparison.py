#!/usr/bin/env python3
"""
Function Callingの完全フローとレガシーフローを比較するテスト
"""

import asyncio
import aiohttp
import json


async def test_both_flows():
    """完全フローとレガシーフローを比較"""

    # ツールが確実に呼ばれる質問に変更
    test_prompt = "Please calculate 127 times 943 using the calculation tool and provide me the result."

    # テスト1: 完全フロー（complete_tool_flow=True）
    print("🔄 完全Function Callingフロー（complete_tool_flow=True）")
    print("=" * 60)

    payload_complete = {
        "prompt": test_prompt,
        "provider": "openai",
        "complete_tool_flow": True,  # 完全フロー
        "enable_tools": True,  # 修正: enable_function_calling -> enable_tools
        "tool_choice": "auto",
        "options": {"model": "azure-tk-gpt-4o", "temperature": 0.1, "max_tokens": 1000},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/llm/query",
            json=payload_complete,
            headers={"Content-Type": "application/json"},
        ) as response:

            if response.status == 200:
                data = await response.json()
                print(f"📝 最終応答: {data.get('content', 'なし')}")
                print(
                    f"🔧 ツール実行結果: {data.get('tool_execution_results', 'なし')}"
                )
                print(f"🎯 モデル: {data.get('model', 'なし')}")

                # ツール実行の有無をツール関連フィールドで確認
                tool_calls = data.get("tool_calls", [])
                print(f"🛠️ ツールコール: {len(tool_calls) if tool_calls else 0}件")

                # original_tool_callsの確認（デバッグ用フィールド）
                orig_calls = data.get("original_tool_calls", [])
                print(f"🔍 元ツールコール: {len(orig_calls) if orig_calls else 0}件")

            else:
                print(f"❌ エラー: {response.status}")

    print("\n" + "=" * 60)

    # テスト2: レガシーフロー（complete_tool_flow=False）
    print("🔄 レガシーFunction Callingフロー（complete_tool_flow=False）")
    print("=" * 60)

    payload_legacy = {
        "prompt": test_prompt,
        "provider": "openai",
        "complete_tool_flow": False,  # レガシーフロー
        "enable_tools": True,  # 修正: enable_function_calling -> enable_tools
        "tool_choice": "auto",
        "options": {"model": "azure-tk-gpt-4o", "temperature": 0.1, "max_tokens": 1000},
    }

    async with aiohttp.ClientSession() as session:
        async with session.post(
            "http://localhost:8000/api/v1/llm/query",
            json=payload_legacy,
            headers={"Content-Type": "application/json"},
        ) as response:

            if response.status == 200:
                data = await response.json()
                print(f"📝 最終応答: {data.get('content', 'なし')}")

                # レガシーフローではツール実行結果が明示的に返される
                tool_execution = data.get("tool_execution_results", [])
                if tool_execution:
                    print(f"🔧 ツール実行結果: {len(tool_execution)}件")
                    for i, result in enumerate(tool_execution):
                        print(
                            f"  {i+1}. {result.get('function_name')}: {result.get('result')}"
                        )
                else:
                    print("🔧 ツール実行結果: なし")

                print(f"🎯 モデル: {data.get('model', 'なし')}")

            else:
                print(f"❌ エラー: {response.status}")


if __name__ == "__main__":
    asyncio.run(test_both_flows())
