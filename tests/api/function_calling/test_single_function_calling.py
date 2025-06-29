#!/usr/bin/env python3
"""
単発のFunction Callingテスト - ログ詳細確認用
"""

import asyncio
import aiohttp
import json


async def single_test():
    """単発テスト"""

    payload = {
        "prompt": "What is 5 times 6?",
        "provider": "openai",
        "complete_tool_flow": True,
        "enable_function_calling": True,
        "tool_choice": "auto",
        "options": {
            "model": "bedrock-claude-3-7-sonnet",
            "temperature": 0.1,
            "max_tokens": 1000,
        },
    }

    print("🔧 単発Function Callingテスト")
    print(f"プロンプト: {payload['prompt']}")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/v1/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    print(f"📝 最終応答: {data.get('content', 'なし')}")
                    print(
                        f"🔧 ツール実行結果: {len(data.get('tool_execution_results', []))}件"
                    )

                    for i, result in enumerate(data.get("tool_execution_results", [])):
                        print(
                            f"  {i+1}. {result.get('function_name')}: {result.get('result', {}).get('result') if isinstance(result.get('result'), dict) else result.get('result')}"
                        )

                else:
                    error = await response.text()
                    print(f"❌ エラー: {response.status} - {error}")

    except Exception as e:
        print(f"❌ 例外: {e}")


if __name__ == "__main__":
    asyncio.run(single_test())
