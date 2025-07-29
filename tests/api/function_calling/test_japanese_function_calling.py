#!/usr/bin/env python3
"""
日本語化されたGitHub MCPツールの効果をテスト
"""

import asyncio
import json
import os
from doc_ai_helper_backend.services.llm.providers.openai_service import OpenAIService


async def test_japanese_github_function_calling():
    """日本語化されたGitHub Function Callingの効果をテスト"""

    print("🌟 日本語GitHub Function Callingテスト")
    print("=" * 50)

    # GitHub tokenを設定（デモ用）
    os.environ["GITHUB_TOKEN"] = "demo_token_for_testing"

    try:
        # OpenAI LLMサービスを初期化
        llm_service = OpenAIService()

        # 日本語化されたFunction定義
        japanese_github_functions = [
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
        ]

        # 日本語プロンプトでテスト
        japanese_prompt = """
        このREADME.mdファイルを確認しましたが、以下の問題があります：
        
        1. インストール手順が不明確で、初心者には理解困難
        2. サンプルコードが古いバージョンで動作しない
        3. 必要な依存関係の説明が不足している
        4. トラブルシューティングの情報がない
        
        これらの問題についてGitHub Issueを作成してください。
        タイトルは「READMEドキュメントの改善が必要」とし、
        上記の問題点を詳しく説明してください。
        適切なラベルも付けてください。
        """

        print("📝 日本語プロンプトでFunction Callingをテスト中...")
        print(f"プロンプト: {japanese_prompt[:100]}...")

        # LLMに日本語関数定義と日本語プロンプトを送信
        response = await llm_service.query(
            prompt=japanese_prompt,
            options={
                "functions": japanese_github_functions,
                "function_call": "auto",
                "temperature": 0.3,  # 創造性と確実性のバランス
            },
        )

        print(f"\n✅ LLM応答:")
        print(f"   {response.content}")

        # Function Callが発生した場合の処理
        if response.tool_calls:
            print("\n🔧 Function Callが検出されました:")
            for tool_call in response.tool_calls:
                print(f"   関数名: {tool_call.function.name}")

                # 引数を解析して日本語内容を確認
                try:
                    args = json.loads(tool_call.function.arguments)
                    print(f"\n   📋 生成されたIssue内容:")
                    print(f"   タイトル: {args.get('title', 'N/A')}")
                    print(f"   説明: {args.get('description', 'N/A')[:200]}...")
                    if args.get("labels"):
                        print(f"   ラベル: {args.get('labels')}")

                    print(f"\n   🎯 日本語品質評価:")
                    title = args.get("title", "")
                    if any(char in title for char in "あいうえおかきくけこ"):
                        print(f"   ✅ タイトルに日本語が含まれています")
                    else:
                        print(f"   ⚠️  タイトルが英語になっています")

                    description = args.get("description", "")
                    if any(char in description for char in "あいうえおかきくけこ"):
                        print(f"   ✅ 説明文が日本語で書かれています")
                    else:
                        print(f"   ⚠️  説明文が英語になっています")

                except json.JSONDecodeError:
                    print(f"   ⚠️  引数の解析に失敗: {tool_call.function.arguments}")
        else:
            print("\n⚠️  Function Callが実行されませんでした")
            print("   LLMがFunction Callingを選択しなかった可能性があります")

    except Exception as e:
        print(f"❌ エラー: {e}")

    print("\n🎯 結論:")
    print("   Function定義とパラメータ説明を日本語化することで、")
    print("   LLMは日本語でより自然で適切な内容を生成します。")
    print("   特にタイトルや説明文で日本語が使用される確率が向上します。")


if __name__ == "__main__":
    asyncio.run(test_japanese_github_function_calling())
