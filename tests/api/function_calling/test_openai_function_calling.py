"""
Test script for OpenAI Function Calling flow.

This script tests the actual OpenAI integration with complete Function Calling flow.
"""

import asyncio
import json
import httpx
import os
from typing import Dict, Any


class OpenAIFunctionCallingTester:
    """OpenAI Function Callingフローのテスト"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    async def test_openai_calculation(self):
        """OpenAIでの計算テスト"""
        print("🤖 OpenAI Function Callingテスト")
        print("-" * 50)

        # Check if OpenAI API key is available
        if not os.getenv("OPENAI_API_KEY"):
            print("⚠️ OPENAI_API_KEY環境変数が設定されていません")
            print("Mockサービスを使用します")
            provider = "mock"
        else:
            provider = "openai"

        data = {
            "prompt": "What is 15 multiplied by 8?",
            "provider": provider,
            "enable_tools": True,
            "complete_tool_flow": True,
            "tool_choice": "auto",
        }

        async with httpx.AsyncClient() as client:
            try:
                print("📤 リクエスト送信中...")
                response = await client.post(
                    f"{self.api_base}/llm/query", json=data, timeout=60.0
                )
                response.raise_for_status()
                result = response.json()

                print(f"プロンプト: {data['prompt']}")
                print(f"プロバイダー: {provider}")
                print(f"完全フロー: {data['complete_tool_flow']}")
                print(f"レスポンス: {result['content']}")

                # デバッグ: レスポンス構造の詳細確認
                print("\n🔍 レスポンス詳細:")
                print(f"  - プロバイダー: {result.get('provider', 'N/A')}")
                print(f"  - モデル: {result.get('model', 'N/A')}")
                print(f"  - 内容の長さ: {len(result.get('content', ''))}")

                # ツール関連の情報
                tool_calls = result.get("tool_calls")
                if tool_calls:
                    print(f"  - 現在のツール呼び出し: {len(tool_calls)}個")
                    for i, call in enumerate(tool_calls):
                        print(
                            f"    {i+1}. {call.get('function', {}).get('name', 'Unknown')}"
                        )

                if result.get("tool_execution_results"):
                    print("\n🔧 ツール実行結果:")
                    for i, tool_result in enumerate(result["tool_execution_results"]):
                        function_name = tool_result.get("function_name", "Unknown")
                        result_data = tool_result.get(
                            "result", tool_result.get("error", "No result")
                        )
                        print(f"  {i+1}. {function_name}: {str(result_data)[:100]}...")

                if result.get("original_tool_calls"):
                    print("\n📋 元のツール呼び出し:")
                    for i, tool_call in enumerate(result["original_tool_calls"]):
                        function_name = tool_call.get("function", {}).get(
                            "name", "Unknown"
                        )
                        arguments = tool_call.get("function", {}).get("arguments", "{}")
                        print(f"  {i+1}. {function_name}: {arguments}")

                # 最終的な回答に計算結果が含まれているかチェック
                content_lower = result["content"].lower()
                has_result = any(
                    keyword in content_lower
                    for keyword in ["120", "15", "8", "result", "answer", "equals"]
                )
                print(f"\n✅ 最終回答に計算結果が含まれている: {has_result}")
                if not has_result:
                    print(
                        "⚠️  最終回答にツール実行結果が反映されていない可能性があります"
                    )

                return result

            except Exception as e:
                print(f"❌ テストエラー: {e}")
                return None

    async def run_test(self):
        """テストを実行"""
        print("🧪 OpenAI Function Calling統合テスト")
        print("=" * 60)

        await self.test_openai_calculation()


async def main():
    """メイン実行関数"""
    tester = OpenAIFunctionCallingTester()
    await tester.run_test()


if __name__ == "__main__":
    asyncio.run(main())
