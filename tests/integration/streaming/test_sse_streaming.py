#!/usr/bin/env python3
"""
SSEストリーミングテスト - ツール使用対応版
"""

import asyncio
import aiohttp
import json


async def test_sse_streaming():
    """SSEストリーミングのテスト"""

    test_cases = [
        {
            "name": "通常のストリーミング（ツールなし）",
            "payload": {
                "prompt": "Write a short story about a robot discovering emotions.",
                "provider": "openai",
                "enable_tools": False,
                "options": {
                    "model": "azure-tk-gpt-4o",
                    "temperature": 0.7,
                    "max_tokens": 500,
                },
            },
        },
        {
            "name": "ツール使用ストリーミング（完全フロー）",
            "payload": {
                "prompt": "Please calculate 234 times 567 and explain the result in detail.",
                "provider": "openai",
                "enable_tools": True,
                "complete_tool_flow": True,
                "tool_choice": "auto",
                "options": {
                    "model": "azure-tk-gpt-4o",
                    "temperature": 0.3,
                    "max_tokens": 800,
                },
            },
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"🧪 テストケース {i}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"📝 質問: {test_case['payload']['prompt'][:60]}...")
        print()

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    "http://localhost:8000/api/v1/llm/stream",
                    json=test_case["payload"],
                    headers={
                        "Content-Type": "application/json",
                        "Accept": "text/event-stream",
                    },
                ) as response:

                    print(f"📡 HTTPステータス: {response.status}")

                    if response.status == 200:
                        print("🎯 【ストリーミング開始】:")
                        print("-" * 50)

                        chunk_count = 0
                        full_content = ""

                        async for line in response.content:
                            line_str = line.decode("utf-8").strip()

                            if line_str.startswith("data: "):
                                data_str = line_str[6:]  # Remove 'data: ' prefix

                                if data_str:
                                    try:
                                        data = json.loads(data_str)

                                        if "text" in data:
                                            text_chunk = data["text"]
                                            full_content += text_chunk
                                            print(text_chunk, end="", flush=True)
                                            chunk_count += 1

                                        elif "status" in data:
                                            print(
                                                f"\n[{data['status']}] {data.get('message', '')}"
                                            )

                                        elif "tool_info" in data:
                                            tool_info = data["tool_info"]
                                            print(
                                                f"\n[ツール実行完了] {tool_info['tools_executed']}件: {', '.join(tool_info['tool_names'])}"
                                            )

                                        elif "tool_execution_results" in data:
                                            results = data["tool_execution_results"]
                                            print(
                                                f"\n[ツール結果] {len(results)}件の実行結果を受信"
                                            )

                                        elif "done" in data and data["done"]:
                                            print("\n[ストリーミング完了]")
                                            break

                                        elif "error" in data:
                                            print(f"\n❌ エラー: {data['error']}")
                                            break

                                    except json.JSONDecodeError as e:
                                        print(
                                            f"\n⚠️ JSON解析エラー: {e} - データ: {data_str}"
                                        )

                        print(f"\n{'-' * 50}")
                        print(f"📊 統計:")
                        print(f"  - チャンク数: {chunk_count}")
                        print(f"  - 総文字数: {len(full_content)}")
                        print(f"  - 総単語数: {len(full_content.split())}")

                    else:
                        error_text = await response.text()
                        print(f"❌ HTTPエラー: {response.status}")
                        print(f"エラー詳細: {error_text}")

        except Exception as e:
            print(f"❌ 接続エラー: {str(e)}")


if __name__ == "__main__":
    print("🚀 SSEストリーミングテスト開始")
    print("ツール使用対応版のストリーミング機能をテストします。")

    asyncio.run(test_sse_streaming())
