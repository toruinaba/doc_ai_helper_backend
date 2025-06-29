#!/usr/bin/env python3
"""
OpenAI Function Calling詳細デバッグテスト
ツール実行後の最終応答に計算結果が含まれているかを詳細に検証
"""

import asyncio
import aiohttp
import json


async def test_openai_function_calling_detailed():
    """OpenAI Function Callingの詳細テスト"""

    # テストケース
    test_cases = [
        {
            "name": "基本的な計算",
            "prompt": "What is 15 multiplied by 8?",
            "expected_result": "120",
        },
        {
            "name": "複合計算",
            "prompt": "Calculate 25 * 4 + 10 and explain the result",
            "expected_result": "110",
        },
        {
            "name": "複雑な計算",
            "prompt": "Please compute (12 + 8) * 3 and tell me the answer",
            "expected_result": "60",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*60}")
        print(f"🧪 テストケース {i}: {test_case['name']}")
        print(f"{'='*60}")

        # リクエストペイロード
        payload = {
            "prompt": test_case["prompt"],
            "provider": "openai",
            "complete_tool_flow": True,
            "enable_function_calling": True,  # 正しいパラメータ名
            "tool_choice": "auto",  # ツールの自動選択
            "options": {
                "model": "azure-tk-gpt-4o",
                "temperature": 0.1,
                "max_tokens": 2000,
            },
        }

        print(f"📤 プロンプト: {test_case['prompt']}")
        print(f"🔍 期待される結果: {test_case['expected_result']}")

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/v1/llm/query",
                    json=payload,
                    headers={"Content-Type": "application/json"},
                ) as response:

                    print(f"📊 HTTP ステータス: {response.status}")

                    if response.status == 200:
                        data = await response.json()

                        # レスポンス詳細
                        print(f"🤖 最終応答: {data.get('content', 'N/A')[:200]}...")
                        print(f"⚙️ プロバイダー: {data.get('provider', 'N/A')}")
                        print(f"🎯 モデル: {data.get('model', 'N/A')}")

                        # ツール実行結果
                        tool_execution = data.get("tool_execution_results", [])
                        if tool_execution:
                            print(f"🔧 ツール実行数: {len(tool_execution)}")
                            for j, tool_result in enumerate(tool_execution):
                                function_name = tool_result.get(
                                    "function_name", "Unknown"
                                )
                                result = tool_result.get("result", {})
                                print(
                                    f"  {j+1}. {function_name}: {str(result)[:100]}..."
                                )
                        else:
                            print("⚠️ ツール実行結果なし")

                        # 最終応答の分析
                        response_text = data.get("content", "")
                        contains_result = test_case["expected_result"] in response_text

                        print(f"✅ 期待される結果が含まれている: {contains_result}")

                        if not contains_result:
                            print(
                                f"❌ 期待される値 '{test_case['expected_result']}' が応答に含まれていません"
                            )
                            print(f"📝 完全な応答: {response_text}")

                        # 使用トークン数
                        usage = data.get("usage", {})
                        if usage:
                            print(
                                f"💰 使用トークン: {usage.get('total_tokens', 'N/A')}"
                            )

                    else:
                        error_text = await response.text()
                        print(f"❌ エラー応答: {error_text}")

        except Exception as e:
            print(f"❌ テスト実行エラー: {str(e)}")

        # 少し待機
        await asyncio.sleep(2)

    print(f"\n{'='*60}")
    print("🏁 全テストケース完了")
    print(f"{'='*60}")


if __name__ == "__main__":
    asyncio.run(test_openai_function_calling_detailed())
