"""
テスト用のAPIクライアント - コンテキスト対応システムプロンプト生成のテスト
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from unittest.mock import patch
from fastapi.testclient import TestClient

from doc_ai_helper_backend.services.llm.providers.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.base import LLMServiceBase


def get_mock_llm_service() -> LLMServiceBase:
    """テスト用のMockLLMServiceインスタンスを返す"""
    return MockLLMService(response_delay=0.1)


def test_context_aware_api():
    """API経由でコンテキスト対応クエリをテスト（TestClientを使用）"""

    # FastAPIアプリケーションをインポートして依存関数をオーバーライド
    from doc_ai_helper_backend.main import app
    from doc_ai_helper_backend.api.dependencies import get_llm_service

    # 依存関数をモックサービスにオーバーライド
    app.dependency_overrides[get_llm_service] = get_mock_llm_service

    try:
        client = TestClient(app)

        # テスト用のリクエストデータ
        request_data = {
            "prompt": "このドキュメントについて簡単に説明してください",
            "repository_context": {
                "service": "github",
                "owner": "microsoft",
                "repo": "vscode",
                "ref": "main",
                "current_path": "README.md",
                "base_url": "https://github.com/microsoft/vscode",
            },
            "document_metadata": {
                "title": "Visual Studio Code",
                "type": "markdown",
                "filename": "README.md",
                "file_size": 5120,
                "language": "en",
            },
            "document_content": """# Visual Studio Code

Visual Studio Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS and Linux. It comes with built-in support for JavaScript, TypeScript and Node.js and has a rich ecosystem of extensions for other languages and runtimes (such as C++, C#, Java, Python, PHP, Go, .NET).

## Features

- IntelliSense
- Debugging
- Built-in Git support
- Extensions

Get started with the [introductory videos](https://code.visualstudio.com/docs/getstarted/introvideos).
""",
            "system_prompt_template": "contextual_document_assistant_ja",
            "include_document_in_system_prompt": True,
            "options": {"model": "mock", "temperature": 0.7},  # モックサービスを使用
        }

        print("=== API経由でのコンテキスト対応クエリテスト ===")
        print(f"送信データ:")
        print(f"  - prompt: {request_data['prompt']}")
        print(
            f"  - repository: {request_data['repository_context']['owner']}/{request_data['repository_context']['repo']}"
        )
        print(f"  - document: {request_data['repository_context']['current_path']}")
        print(f"  - system_prompt_template: {request_data['system_prompt_template']}")
        print(
            f"  - include_document_in_system_prompt: {request_data['include_document_in_system_prompt']}"
        )
        print(f"  - options.model: {request_data['options']['model']}")
        print()

        response = client.post("/api/v1/llm/query", json=request_data)

        print(f"HTTPステータス: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 成功:")
            print(f"  - content: {result.get('content', '')[:200]}...")
            print(f"  - model: {result.get('model', 'N/A')}")
            print(f"  - provider: {result.get('provider', 'N/A')}")
            print(f"  - usage: {result.get('usage', {})}")

            # システムプロンプトが使用されたかをチェック
            content = result.get("content", "")
            if "microsoft/vscode" in content or "Visual Studio Code" in content:
                print("✅ システムプロンプトがレスポンスに反映されています")
                return True
            else:
                print(
                    "⚠️  システムプロンプトがレスポンスに反映されていない可能性があります"
                )
                print(f"     レスポンス内容: {content}")
                return False

        else:
            print(f"❌ エラー: {response.status_code}")
            print(f"エラー内容: {response.text}")
            return False

    finally:
        # オーバーライドをクリア
        app.dependency_overrides.clear()


def test_minimal_context_api():
    """最小限のコンテキストでテスト（TestClientを使用）"""

    # FastAPIアプリケーションをインポートして依存関数をオーバーライド
    from doc_ai_helper_backend.main import app
    from doc_ai_helper_backend.api.dependencies import get_llm_service

    # 依存関数をモックサービスにオーバーライド
    app.dependency_overrides[get_llm_service] = get_mock_llm_service

    try:
        client = TestClient(app)

        request_data = {
            "prompt": "こんにちは",
            "repository_context": {
                "service": "github",
                "owner": "test",
                "repo": "minimal",
                "ref": "main",
            },
            "system_prompt_template": "minimal_context_ja",
            "include_document_in_system_prompt": True,
            "options": {"model": "mock"},
        }

        print("\n=== 最小限のコンテキストでのテスト ===")
        print(f"送信データ:")
        print(f"  - prompt: {request_data['prompt']}")
        print(
            f"  - repository: {request_data['repository_context']['owner']}/{request_data['repository_context']['repo']}"
        )
        print(f"  - system_prompt_template: {request_data['system_prompt_template']}")
        print(f"  - options.model: {request_data['options']['model']}")
        print()

        response = client.post("/api/v1/llm/query", json=request_data)

        print(f"HTTPステータス: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 成功:")
            print(f"  - content: {result.get('content', '')}")
            print(f"  - model: {result.get('model', 'N/A')}")

            # システムプロンプトが使用されたかをチェック
            content = result.get("content", "")
            if "test/minimal" in content:
                print("✅ 最小限のシステムプロンプトがレスポンスに反映されています")
                return True
            else:
                print(
                    "⚠️  システムプロンプトがレスポンスに反映されていない可能性があります"
                )
                print(f"     レスポンス内容: {content}")
                return False

        else:
            print(f"❌ エラー: {response.status_code}")
            print(f"エラー内容: {response.text}")
            return False

    finally:
        # オーバーライドをクリア
        app.dependency_overrides.clear()


def test_without_context():
    """コンテキストなしでのテスト（従来のクエリ、TestClientを使用）"""

    # FastAPIアプリケーションをインポートして依存関数をオーバーライド
    from doc_ai_helper_backend.main import app
    from doc_ai_helper_backend.api.dependencies import get_llm_service

    # 依存関数をモックサービスにオーバーライド
    app.dependency_overrides[get_llm_service] = get_mock_llm_service

    try:
        client = TestClient(app)

        request_data = {
            "prompt": "こんにちは、元気ですか？",
            "include_document_in_system_prompt": False,
            "options": {"model": "mock"},
        }

        print("\n=== コンテキストなしでのテスト ===")
        print(f"送信データ:")
        print(f"  - prompt: {request_data['prompt']}")
        print(
            f"  - include_document_in_system_prompt: {request_data['include_document_in_system_prompt']}"
        )
        print(f"  - options.model: {request_data['options']['model']}")
        print()

        response = client.post("/api/v1/llm/query", json=request_data)

        print(f"HTTPステータス: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 成功:")
            print(f"  - content: {result.get('content', '')}")
            print(f"  - model: {result.get('model', 'N/A')}")
            return True

        else:
            print(f"❌ エラー: {response.status_code}")
            print(f"エラー内容: {response.text}")
            return False

    finally:
        # オーバーライドをクリア
        app.dependency_overrides.clear()


def main():
    """メイン関数"""
    print("🚀 API経由でのシステムプロンプト生成テストを開始...")

    success_count = 0
    total_tests = 3

    if test_context_aware_api():
        success_count += 1

    if test_minimal_context_api():
        success_count += 1

    if test_without_context():
        success_count += 1

    print(f"\n✅ テスト完了: {success_count}/{total_tests} 成功")

    if success_count == total_tests:
        print("🎉 すべてのテストが成功しました！")
    else:
        print("⚠️  一部のテストが失敗しました。")


if __name__ == "__main__":
    main()
