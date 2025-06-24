#!/usr/bin/env python3
"""
API経由でのMCPツール使用テストスクリプト

このスクリプトは、フロントエンドからAPI経由でMCPツールを使用する方法をデモンストレーションします。
"""

import asyncio
import json
import httpx
from typing import Dict, Any, List, Optional


class MCPAPITester:
    """API経由でMCPツールをテストするクラス"""

    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url
        self.api_base = f"{base_url}/api/v1"

    async def query_llm(
        self,
        prompt: str,
        enable_tools: bool = True,
        tool_choice: str = "auto",
        provider: str = "openai",
        conversation_history: Optional[List[Dict[str, Any]]] = None,
    ) -> Dict[str, Any]:
        """LLMにクエリを送信してMCPツールを使用"""

        data = {
            "prompt": prompt,
            "provider": provider,
            "enable_tools": enable_tools,
            "tool_choice": tool_choice,
        }

        if conversation_history:
            data["conversation_history"] = conversation_history

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base}/llm/query", json=data, timeout=60.0
            )
            response.raise_for_status()
            return response.json()

    async def test_calculation_tool(self):
        """計算ツールのテスト"""
        print("🧮 計算ツールのテスト")
        print("-" * 50)

        result = await self.query_llm(
            "100 × 25 + 75を計算してください", enable_tools=True, tool_choice="auto"
        )

        print(f"プロンプト: 100 × 25 + 75を計算してください")
        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(
                    f"  - {tool_result['function_name']}: {tool_result.get('result', tool_result.get('error'))}"
                )

        print()
        return result

    async def test_document_analysis_tool(self):
        """ドキュメント分析ツールのテスト"""
        print("📄 ドキュメント分析ツールのテスト")
        print("-" * 50)

        sample_document = """# プロジェクト概要

これはサンプルプロジェクトです。

## 機能

- 機能A: ユーザー管理
- 機能B: データ処理
- 機能C: レポート生成

## 使用方法

1. インストール
2. 設定ファイルの編集
3. アプリケーションの実行

### 詳細手順

#### インストール
```bash
npm install
```

#### 設定
config.jsonを編集してください。
"""

        result = await self.query_llm(
            f"この文書の構造を分析してください:\n\n{sample_document}",
            enable_tools=True,
            tool_choice="auto",
        )

        print(f"プロンプト: ドキュメント構造分析")
        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(f"  - {tool_result['function_name']}: 実行完了")

        print()
        return result

    async def test_text_formatting_tool(self):
        """テキストフォーマットツールのテスト"""
        print("✨ テキストフォーマットツールのテスト")
        print("-" * 50)

        result = await self.query_llm(
            "この文字列をタイトルケースにフォーマットしてください: hello world from api",
            enable_tools=True,
            tool_choice="auto",
        )

        print(f"プロンプト: hello world from api をタイトルケースに")
        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(
                    f"  - {tool_result['function_name']}: {tool_result.get('result', tool_result.get('error'))}"
                )

        print()
        return result

    async def test_feedback_generation_tool(self):
        """フィードバック生成ツールのテスト"""
        print("💬 フィードバック生成ツールのテスト")
        print("-" * 50)

        conversation_history = [
            {
                "role": "user",
                "content": "ドキュメントが分かりにくいです",
                "timestamp": "2024-01-01T00:00:00Z",
            },
            {
                "role": "assistant",
                "content": "どの部分が分かりにくいですか？具体的に教えてください。",
                "timestamp": "2024-01-01T00:01:00Z",
            },
            {
                "role": "user",
                "content": "構造が複雑すぎて、どこから読めばいいかわからない",
                "timestamp": "2024-01-01T00:02:00Z",
            },
            {
                "role": "assistant",
                "content": "構造を改善する提案をさせていただきます。",
                "timestamp": "2024-01-01T00:03:00Z",
            },
        ]

        result = await self.query_llm(
            "この会話からドキュメント改善のフィードバックを生成してください",
            enable_tools=True,
            tool_choice="auto",
            conversation_history=conversation_history,
        )

        print(f"プロンプト: 会話からフィードバック生成")
        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(f"  - {tool_result['function_name']}: 実行完了")

        print()
        return result

    async def test_specific_tool_forcing(self):
        """特定ツールの強制実行テスト"""
        print("🎯 特定ツール強制実行のテスト")
        print("-" * 50)

        # 計算ツールを強制実行
        result = await self.query_llm(
            "今日はいい天気ですね",  # 計算と関係ないプロンプトでも計算ツールを強制実行
            enable_tools=True,
            tool_choice="calculate",  # 特定のツール名を指定
        )

        print(f"プロンプト: 今日はいい天気ですね（calculate ツール強制実行）")
        print(f"レスポンス: {result['content']}")

        if result.get("tool_execution_results"):
            print("ツール実行結果:")
            for tool_result in result["tool_execution_results"]:
                print(
                    f"  - {tool_result['function_name']}: {tool_result.get('result', tool_result.get('error'))}"
                )

        print()
        return result

    async def test_no_tools(self):
        """ツール無効化のテスト"""
        print("🚫 ツール無効化のテスト")
        print("-" * 50)

        result = await self.query_llm(
            "100 + 200を計算してください", enable_tools=False  # ツールを無効化
        )

        print(f"プロンプト: 100 + 200を計算してください（ツール無効）")
        print(f"レスポンス: {result['content']}")
        print(f"ツール呼び出し: {result.get('tool_calls', 'なし')}")

        print()
        return result

    async def test_health_check(self):
        """APIの動作確認"""
        print("🔍 API動作確認")
        print("-" * 50)

        async with httpx.AsyncClient() as client:
            response = await client.get(f"{self.api_base}/health/")
            response.raise_for_status()
            health_data = response.json()

            print(f"ヘルスチェック: {health_data['status']}")
            print()

            return health_data

    async def run_all_tests(self):
        """すべてのテストを実行"""
        print("🚀 API経由MCPツール使用テスト開始")
        print("=" * 60)
        print()

        try:
            # ヘルスチェック
            await self.test_health_check()

            # 各ツールのテスト
            await self.test_calculation_tool()
            await self.test_document_analysis_tool()
            await self.test_text_formatting_tool()
            await self.test_feedback_generation_tool()
            await self.test_specific_tool_forcing()
            await self.test_no_tools()

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
    tester = MCPAPITester()
    await tester.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
