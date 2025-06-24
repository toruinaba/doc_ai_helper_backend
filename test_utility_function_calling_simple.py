"""
ユーティリティ関数のFunction Calling機能をテストするためのスクリプト

このスクリプトは、MockLLMServiceがユーティリティ関数（現在時刻取得、文字数カウント等）を
正しく検出・実行できるかを確認します。
"""

import asyncio
import sys
import os

# プロジェクトルートをパスに追加
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.utility_functions import get_utility_functions


async def test_utility_function_calling():
    """ユーティリティ関数のFunction Calling機能をテストする"""
    print("🔧 ユーティリティ関数 Function Calling テスト開始")

    # MockLLMServiceを初期化
    mock_service = MockLLMService(response_delay=0.1)

    # ユーティリティ関数定義を取得
    utility_functions = get_utility_functions()
    print(f"📋 利用可能なユーティリティ関数: {len(utility_functions)}個")
    for func in utility_functions:
        print(f"  - {func.name}: {func.description}")

    # テストケース1: 現在時刻取得
    print("\n⏰ テスト1: 現在時刻取得")
    prompt1 = "What is the current time?"
    response1 = await mock_service.query(
        prompt1, options={"functions": utility_functions}
    )

    print(f"プロンプト: {prompt1}")
    print(f"レスポンス: {response1.content}")
    if response1.tool_calls:
        print(f"✅ ツール呼び出し: {len(response1.tool_calls)}個")
        for tool_call in response1.tool_calls:
            print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")
    else:
        print("❌ ツール呼び出しが発生しませんでした")

    # テストケース2: 文字数カウント
    print("\n📊 テスト2: 文字数カウント")
    prompt2 = "Please count the characters in this text: Hello World"
    response2 = await mock_service.query(
        prompt2, options={"functions": utility_functions}
    )

    print(f"プロンプト: {prompt2}")
    print(f"レスポンス: {response2.content}")
    if response2.tool_calls:
        print(f"✅ ツール呼び出し: {len(response2.tool_calls)}個")
        for tool_call in response2.tool_calls:
            print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")
    else:
        print("❌ ツール呼び出しが発生しませんでした")

    # テストケース3: メール検証
    print("\n📧 テスト3: メール検証")
    prompt3 = "Please validate this email address: test@example.com"
    response3 = await mock_service.query(
        prompt3, options={"functions": utility_functions}
    )

    print(f"プロンプト: {prompt3}")
    print(f"レスポンス: {response3.content}")
    if response3.tool_calls:
        print(f"✅ ツール呼び出し: {len(response3.tool_calls)}個")
        for tool_call in response3.tool_calls:
            print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")
    else:
        print("❌ ツール呼び出しが発生しませんでした")

    # テストケース4: 計算
    print("\n🧮 テスト4: 計算")
    prompt4 = "Calculate 15 + 27"
    response4 = await mock_service.query(
        prompt4, options={"functions": utility_functions}
    )

    print(f"プロンプト: {prompt4}")
    print(f"レスポンス: {response4.content}")
    if response4.tool_calls:
        print(f"✅ ツール呼び出し: {len(response4.tool_calls)}個")
        for tool_call in response4.tool_calls:
            print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")
    else:
        print("❌ ツール呼び出しが発生しませんでした")

    # テストケース5: ランダムデータ生成
    print("\n🎲 テスト5: ランダムデータ生成")
    prompt5 = "Generate a random UUID for me"
    response5 = await mock_service.query(
        prompt5, options={"functions": utility_functions}
    )

    print(f"プロンプト: {prompt5}")
    print(f"レスポンス: {response5.content}")
    if response5.tool_calls:
        print(f"✅ ツール呼び出し: {len(response5.tool_calls)}個")
        for tool_call in response5.tool_calls:
            print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")
    else:
        print("❌ ツール呼び出しが発生しませんでした")

    # テストケース6: 通常のプロンプト（ツール呼び出しなし）
    print("\n💬 テスト6: 通常のプロンプト（ツール呼び出しなし）")
    prompt6 = "Hello, how are you doing today?"
    response6 = await mock_service.query(
        prompt6, options={"functions": utility_functions}
    )

    print(f"プロンプト: {prompt6}")
    print(f"レスポンス: {response6.content}")
    if response6.tool_calls:
        print(f"❓ 予期しないツール呼び出し: {len(response6.tool_calls)}個")
        for tool_call in response6.tool_calls:
            print(f"  - {tool_call.function.name}: {tool_call.function.arguments}")
    else:
        print("✅ ツール呼び出しなし（正常）")

    print("\n✅ ユーティリティ関数 Function Calling テスト完了")


if __name__ == "__main__":
    asyncio.run(test_utility_function_calling())
