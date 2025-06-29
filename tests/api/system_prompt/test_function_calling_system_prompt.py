"""
Function Calling有効時のシステムプロンプト生成テスト
"""

import asyncio
import httpx
import json
from typing import Dict, Any, Optional
from unittest.mock import patch
from fastapi.testclient import TestClient

from doc_ai_helper_backend.services.llm.mock_service import MockLLMService
from doc_ai_helper_backend.services.llm.base import LLMServiceBase


def get_mock_llm_service() -> LLMServiceBase:
    """テスト用のMockLLMServiceインスタンスを返す"""
    return MockLLMService(response_delay=0.1)


def test_function_calling_with_system_prompt():
    """Function Calling有効時のシステムプロンプト生成をテスト"""

    # FastAPIアプリケーションをインポートして依存関数をオーバーライド
    from doc_ai_helper_backend.main import app
    from doc_ai_helper_backend.api.dependencies import get_llm_service

    # 依存関数をモックサービスにオーバーライド
    app.dependency_overrides[get_llm_service] = get_mock_llm_service

    try:
        client = TestClient(app)

        # Function Calling有効でコンテキスト付きリクエスト
        request_data = {
            "prompt": "このドキュメントについて要約してください",
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

Visual Studio Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS and Linux.

## Features

- IntelliSense
- Debugging
- Built-in Git support
- Extensions
""",
            "system_prompt_template": "contextual_document_assistant_ja",
            "include_document_in_system_prompt": True,
            "enable_tools": True,  # Function Callingを有効化
            "tool_choice": "auto",
            "complete_tool_flow": True,
            "options": {"model": "mock", "temperature": 0.7},
        }

        print("=== Function Calling有効時のシステムプロンプト生成テスト ===")
        print(f"送信データ:")
        print(f"  - prompt: {request_data['prompt']}")
        print(
            f"  - repository: {request_data['repository_context']['owner']}/{request_data['repository_context']['repo']}"
        )
        print(f"  - document: {request_data['repository_context']['current_path']}")
        print(f"  - system_prompt_template: {request_data['system_prompt_template']}")
        print(f"  - enable_tools: {request_data['enable_tools']}")
        print(f"  - tool_choice: {request_data['tool_choice']}")
        print(f"  - complete_tool_flow: {request_data['complete_tool_flow']}")
        print()

        response = client.post("/api/v1/llm/query", json=request_data)

        print(f"HTTPステータス: {response.status_code}")

        if response.status_code == 200:
            result = response.json()
            print("✅ 成功:")
            print(f"  - content: {result.get('content', '')[:200]}...")
            print(f"  - model: {result.get('model', 'N/A')}")
            print(f"  - provider: {result.get('provider', 'N/A')}")
            print(f"  - tool_calls: {len(result.get('tool_calls', []) or [])}")

            # システムプロンプトが使用されたかをチェック
            content = result.get("content", "")
            if "microsoft/vscode" in content or "Visual Studio Code" in content:
                print(
                    "✅ Function Calling有効時でもシステムプロンプトがレスポンスに反映されています"
                )
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


def main():
    """メイン関数"""
    print("🚀 Function Calling対応のシステムプロンプト生成テストを開始...")

    if test_function_calling_with_system_prompt():
        print("\n🎉 テストが成功しました！")
    else:
        print("\n⚠️  テストが失敗しました。")


if __name__ == "__main__":
    main()
