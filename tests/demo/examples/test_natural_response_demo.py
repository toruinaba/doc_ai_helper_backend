#!/usr/bin/env python3
"""
自然な応答のデモ - Function Callingの完全フロー確認
"""

import asyncio
import aiohttp
import json


async def test_natural_response():
    """自然な応答の確認テスト"""

    test_cases = [
        {
            "name": "計算問題",
            "prompt": "Please calculate 456 times 789 and explain what this calculation might be useful for.",
            "tool_expected": "calculate_simple_math",
        },
        {
            "name": "ドキュメント分析",
            "prompt": """
            Please analyze the structure of this markdown document and provide recommendations:
            
            # Product Documentation
            ## Features
            - Fast performance
            - Easy to use
            
            ### Advanced Features
            - API integration
            - Custom plugins
            
            ## Installation
            1. Download the package
            2. Run installer
            
            What improvements would you suggest for this document?
            """,
            "tool_expected": "analyze_document_structure",
        },
    ]

    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{'='*80}")
        print(f"🧪 テストケース {i}: {test_case['name']}")
        print(f"{'='*80}")
        print(f"📝 質問: {test_case['prompt'][:100]}...")
        print(f"🔧 期待ツール: {test_case['tool_expected']}")
        print()

        payload = {
            "prompt": test_case["prompt"],
            "provider": "openai",
            "complete_tool_flow": True,
            "enable_tools": True,
            "tool_choice": "auto",
            "options": {
                "model": "azure-tk-gpt-4o",
                "temperature": 0.3,
                "max_tokens": 1500,
            },
        }

        async with aiohttp.ClientSession() as session:
            async with session.post(
                "http://localhost:8000/api/v1/llm/query",
                json=payload,
                headers={"Content-Type": "application/json"},
            ) as response:

                if response.status == 200:
                    data = await response.json()

                    # 自然な応答の表示
                    natural_response = data.get("content", "")
                    print("🎯 【自然な応答】:")
                    print("-" * 50)
                    print(natural_response)
                    print("-" * 50)

                    # ツール実行の確認
                    original_tools = data.get("original_tool_calls", [])
                    if original_tools:
                        print(f"\n✅ ツール実行: {len(original_tools)}件")
                        for j, tool in enumerate(original_tools, 1):
                            tool_name = tool.get("function", {}).get("name", "不明")
                            print(f"  {j}. {tool_name}")
                    else:
                        print("\n❌ ツール実行なし")

                    # ツール実行結果の詳細
                    tool_results = data.get("tool_execution_results", [])
                    if tool_results:
                        print(f"\n🔧 ツール実行結果詳細:")
                        for j, result in enumerate(tool_results, 1):
                            function_name = result.get("function_name", "不明")
                            result_data = result.get("result", {})
                            print(f"  {j}. {function_name}:")
                            if (
                                isinstance(result_data, dict)
                                and "result" in result_data
                            ):
                                print(f"     結果: {result_data['result']}")
                            else:
                                print(f"     結果: {result_data}")

                    # 応答の特徴分析
                    print(f"\n📊 応答分析:")
                    print(f"  - 文字数: {len(natural_response)}")
                    print(f"  - 単語数: {len(natural_response.split())}")
                    print(
                        f"  - ツール結果を含む: {'Yes' if any(tool.get('tool_expected', '') in natural_response.lower() for tool in [test_case]) else 'Yes' if any(str(r.get('result', '')).replace('\"', '') in natural_response for r in tool_results) else 'No'}"
                    )

                else:
                    print(f"❌ HTTPエラー: {response.status}")
                    error_text = await response.text()
                    print(f"エラー詳細: {error_text}")


if __name__ == "__main__":
    print("🚀 自然な応答デモテスト開始")
    print("このテストでは、Function Callingの完全フローで")
    print("ツール実行結果が自然な形で応答に統合されることを確認します。")

    asyncio.run(test_natural_response())
