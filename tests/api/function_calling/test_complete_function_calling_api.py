"""
Test script for the new complete Function Calling flow API endpoints.

This script tests the API endpoints with the new complete_tool_flow parameter.
"""

import asyncio
import json
import httpx
from typing import Dict, Any, List, Optional


class CompleteFunctionCallingAPITester:
    """API経由で完全なFunction Callingフローをテストするクラス"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    async def query_llm(
        self,
        prompt: str,
        enable_tools: bool = True,
        complete_tool_flow: bool = True,
        tool_choice: str = "auto",
        provider: str = "mock",  # Use mock for testing
    ) -> Dict[str, Any]:
        """LLMにクエリを送信（新しい完全なフロー）"""

        data = {
            "prompt": prompt,
            "provider": provider,
            "enable_tools": enable_tools,
            "complete_tool_flow": complete_tool_flow,
            "tool_choice": tool_choice,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/llm/query", json=data, timeout=60.0
            )
            response.raise_for_status()
            return response.json()

    async def test_complete_flow_calculation(self):
        """完全フローでの計算テスト"""
        print("🧮 完全フローでの計算テスト")
        print("-" * 50)

        result = await self.query_llm(
            "Calculate 25 * 4 + 10",
            complete_tool_flow=True,
        )

        print(f"プロンプト: Calculate 25 * 4 + 10")
        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(
                    f"  - {tool_result['function_name']}: {tool_result.get('result', tool_result.get('error'))}"
                )

        if result.get("original_tool_calls"):
            print("元のツール呼び出し:")
            for tool_call in result["original_tool_calls"]:
                print(f"  - {tool_call['function']['name']}")

        print()
        return result

    async def test_legacy_flow_calculation(self):
        """レガシーフローでの計算テスト（比較用）"""
        print("🔧 レガシーフローでの計算テスト")
        print("-" * 50)

        result = await self.query_llm(
            "Calculate 25 * 4 + 10",
            complete_tool_flow=False,  # レガシーフローを使用
        )

        print(f"プロンプト: Calculate 25 * 4 + 10")
        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(
                    f"  - {tool_result['function_name']}: {tool_result.get('result', tool_result.get('error'))}"
                )

        print()
        return result

    async def test_complete_flow_analysis(self):
        """完全フローでの分析テスト"""
        print("📄 完全フローでの分析テスト")
        print("-" * 50)

        result = await self.query_llm(
            "Analyze this document structure: '# Title\\n## Section 1\\n- Item A\\n- Item B'",
            complete_tool_flow=True,
        )

        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(f"  - {tool_result['function_name']}")

        print()
        return result

    async def test_no_tools_complete_flow(self):
        """ツール無効での完全フローテスト"""
        print("🚫 ツール無効での完全フローテスト")
        print("-" * 50)

        result = await self.query_llm(
            "Hello, how are you today?",
            enable_tools=False,
            complete_tool_flow=True,
        )

        print(f"レスポンス: {result['content']}")
        print(f"ツール実行結果: {result.get('tool_execution_results')}")
        print()
        return result

    async def test_health_check(self):
        """ヘルスチェック"""
        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/health/")
            response.raise_for_status()
            result = response.json()
            print(f"✅ サーバー状態: {result['status']}")
            return result

    async def run_all_tests(self):
        """全テストを実行"""
        print("🚀 完全Function Callingフロー APIテスト開始")
        print("=" * 60)

        try:
            # ヘルスチェック
            await self.test_health_check()

            # 完全フローテスト
            complete_calc = await self.test_complete_flow_calculation()

            # レガシーフロー比較
            legacy_calc = await self.test_legacy_flow_calculation()

            # 分析テスト
            await self.test_complete_flow_analysis()

            # ツール無効テスト
            await self.test_no_tools_complete_flow()

            # 結果比較
            print("📊 完全フロー vs レガシーフロー比較")
            print("-" * 50)
            print(f"完全フロー応答: {complete_calc['content'][:100]}...")
            print(f"レガシー応答: {legacy_calc['content'][:100]}...")

            # 完全フローでは最終的なLLM応答が含まれることを確認
            if (
                "result" in complete_calc["content"].lower()
                or "calculation" in complete_calc["content"].lower()
            ):
                print("✅ 完全フローで適切な最終応答が生成されました")
            else:
                print("⚠️ 完全フローの最終応答が期待と異なります")

            print("✅ すべてのテストが完了しました！")

        except httpx.HTTPStatusError as e:
            print(f"❌ HTTPエラー: {e.response.status_code}")
            print(f"レスポンス: {e.response.text}")
        except httpx.ConnectError:
            print("❌ 接続エラー: サーバーが起動していない可能性があります")
            print(
                "   python -m doc_ai_helper_backend.main を実行してサーバーを起動してください"
            )
        except Exception as e:
            print(f"❌ 予期しないエラー: {e}")


async def main():
    """メイン実行関数"""
    tester = CompleteFunctionCallingAPITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
