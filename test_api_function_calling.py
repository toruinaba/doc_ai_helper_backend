"""
API経由でのFunction Calling機能をテストするためのスクリプト

このスクリプトは、LLM APIエンドポイント（/api/v1/llm/query）経由で
Function Callingが正常に動作するかを確認します。
"""

import asyncio
import json
import sys
import os
import httpx

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_api_function_calling():
    """API経由でのFunction Calling機能をテストする"""
    print("🌐 API経由 Function Calling テスト開始")

    # FastAPIサーバーのURL
    base_url = "http://localhost:8000"
    api_url = f"{base_url}/api/v1/llm/query"

    # HTTPクライアントを作成
    async with httpx.AsyncClient(timeout=30.0) as client:
        # テストケース1: 現在時刻取得（Function Calling有効）
        print("\n⏰ テスト1: 現在時刻取得（Function Calling有効）")
        request_data = {
            "prompt": "What is the current time?",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": True,
            "tool_choice": "auto",
        }

        try:
            response = await client.post(api_url, json=request_data)
            print(f"ステータス: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"レスポンス: {result['content']}")

                if result.get("tool_execution_results"):
                    print(
                        f"✅ ツール実行結果: {len(result['tool_execution_results'])}個"
                    )
                    for i, tool_result in enumerate(result["tool_execution_results"]):
                        print(
                            f"  {i+1}. {tool_result['function_name']}: {tool_result['result']}"
                        )
                else:
                    print("❌ ツール実行結果がありません")
            else:
                print(f"❌ APIエラー: {response.text}")

        except Exception as e:
            print(f"❌ リクエストエラー: {e}")

        # テストケース2: 文字数カウント（Function Calling有効）
        print("\n📊 テスト2: 文字数カウント（Function Calling有効）")
        request_data = {
            "prompt": "Please count the characters in this text: Hello World",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": True,
            "tool_choice": "auto",
        }

        try:
            response = await client.post(api_url, json=request_data)
            print(f"ステータス: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"レスポンス: {result['content']}")

                if result.get("tool_execution_results"):
                    print(
                        f"✅ ツール実行結果: {len(result['tool_execution_results'])}個"
                    )
                    for i, tool_result in enumerate(result["tool_execution_results"]):
                        print(
                            f"  {i+1}. {tool_result['function_name']}: {tool_result['result']}"
                        )
                else:
                    print("❌ ツール実行結果がありません")
            else:
                print(f"❌ APIエラー: {response.text}")

        except Exception as e:
            print(f"❌ リクエストエラー: {e}")

        # テストケース3: 計算（Function Calling有効）
        print("\n🧮 テスト3: 計算（Function Calling有効）")
        request_data = {
            "prompt": "Calculate 15 + 27",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": True,
            "tool_choice": "auto",
        }

        try:
            response = await client.post(api_url, json=request_data)
            print(f"ステータス: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"レスポンス: {result['content']}")

                if result.get("tool_execution_results"):
                    print(
                        f"✅ ツール実行結果: {len(result['tool_execution_results'])}個"
                    )
                    for i, tool_result in enumerate(result["tool_execution_results"]):
                        print(
                            f"  {i+1}. {tool_result['function_name']}: {tool_result['result']}"
                        )
                else:
                    print("❌ ツール実行結果がありません")
            else:
                print(f"❌ APIエラー: {response.text}")

        except Exception as e:
            print(f"❌ リクエストエラー: {e}")

        # テストケース4: 通常のプロンプト（Function Calling無効）
        print("\n💬 テスト4: 通常のプロンプト（Function Calling無効）")
        request_data = {
            "prompt": "Hello, how are you doing today?",
            "provider": "mock",
            "model": "mock-model",
            "enable_tools": False,
        }

        try:
            response = await client.post(api_url, json=request_data)
            print(f"ステータス: {response.status_code}")

            if response.status_code == 200:
                result = response.json()
                print(f"レスポンス: {result['content']}")

                if result.get("tool_execution_results"):
                    print(
                        f"❓ 予期しないツール実行: {len(result['tool_execution_results'])}個"
                    )
                else:
                    print("✅ ツール実行なし（正常）")
            else:
                print(f"❌ APIエラー: {response.text}")

        except Exception as e:
            print(f"❌ リクエストエラー: {e}")

    print("\n✅ API経由 Function Calling テスト完了")


if __name__ == "__main__":
    print(
        "📝 注意: このテストを実行する前に、別のターミナルでFastAPIサーバーを起動してください:"
    )
    print("   uvicorn doc_ai_helper_backend.main:app --reload")
    print()

    asyncio.run(test_api_function_calling())
