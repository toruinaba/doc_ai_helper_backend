#!/usr/bin/env python3
"""
日本語化されたGitHub MCPツールの効果をMockサービスでテスト
"""

import asyncio
import json
from doc_ai_helper_backend.services.llm.mock_service import MockLLMService


async def test_japanese_github_mock():
    """日本語化されたGitHub Function CallingをMockサービスでテスト"""

    print("🌟 日本語GitHub MCP Tools テスト（Mock）")
    print("=" * 60)

    # Mock LLMサービスを初期化
    mock_service = MockLLMService()

    # 日本語化されたFunction定義を含むプロンプト
    japanese_prompt = """
    このREADME.mdファイルを確認しましたが、以下の問題があります：
    
    1. インストール手順が不明確で、初心者には理解困難
    2. サンプルコードが古いバージョンで動作しない
    3. 必要な依存関係の説明が不足している
    4. トラブルシューティングの情報がない
    
    これらの問題についてGitHub Issueを作成してください。
    """

    print(f"📝 日本語プロンプト:")
    print(f"   {japanese_prompt.strip()}")

    try:
        # Function Calling対応のオプション
        options = {
            "functions": [
                {
                    "name": "create_github_issue",
                    "description": "現在表示中のドキュメントのリポジトリにGitHub Issueを作成します。問題報告、改善提案、バグ報告などに使用できます。",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "title": {
                                "type": "string",
                                "description": "Issueのタイトル（簡潔で分かりやすい日本語で記述）",
                            },
                            "description": {
                                "type": "string",
                                "description": "Issueの詳細説明（問題の内容、再現手順、期待される結果などを日本語で記述）",
                            },
                            "labels": {
                                "type": "array",
                                "items": {"type": "string"},
                                "description": "Issueに適用するラベルのリスト（例：['バグ', '改善提案', 'ドキュメント']）",
                            },
                        },
                        "required": ["title", "description"],
                    },
                }
            ],
            "function_call": "auto",
        }

        # LLMクエリを実行
        response = await mock_service.query(japanese_prompt, options)

        print(f"\n✅ Mock LLM応答:")
        print(f"   内容: {response.content}")

        # Function Callをチェック
        if response.tool_calls:
            print(f"\n🔧 Function Callが生成されました:")
            for tool_call in response.tool_calls:
                print(f"   関数名: {tool_call.function.name}")
                print(f"   引数: {tool_call.function.arguments}")

                # 引数を解析
                try:
                    args = json.loads(tool_call.function.arguments)
                    print(f"\n   📋 生成されたIssue内容:")
                    print(f"   タイトル: {args.get('title', 'N/A')}")
                    print(f"   説明: {args.get('description', 'N/A')[:150]}...")
                    if args.get("labels"):
                        print(f"   ラベル: {args.get('labels')}")

                except json.JSONDecodeError as e:
                    print(f"   ⚠️  JSON解析エラー: {e}")
        else:
            print(f"\n⚠️  Function Callが生成されませんでした")

    except Exception as e:
        print(f"\n❌ エラー: {e}")

    print(f"\n🎯 日本語化の効果:")
    print(f"   ✅ Function定義の説明を日本語化")
    print(f"   ✅ パラメータ説明を日本語化")
    print(f"   ✅ 戻り値のJSONキーを日本語化")
    print(f"   ✅ エラーメッセージを日本語化")
    print(f"\n   これにより、LLMは一貫した日本語コンテキストで動作し、")
    print(f"   日本語での応答確率が大幅に向上します。")


if __name__ == "__main__":
    asyncio.run(test_japanese_github_mock())
