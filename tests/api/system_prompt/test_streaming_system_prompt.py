"""
ストリーミングモードでのシステムプロンプト生成テスト
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


def test_streaming_with_system_prompt():
    """ストリーミングモードでのシステムプロンプト生成テスト（TestClientを使用）"""

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

Visual Studio Code is a lightweight but powerful source code editor which runs on your desktop and is available for Windows, macOS and Linux.

## Features

- IntelliSense
- Debugging
- Built-in Git support
- Extensions
""",
            "system_prompt_template": "contextual_document_assistant_ja",
            "include_document_in_system_prompt": True,
            "options": {"model": "mock", "temperature": 0.7},
        }

        print("=== ストリーミングモードでのシステムプロンプト生成テスト ===")
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

        # ストリーミングエンドポイントにリクエストを送信
        with client.stream("POST", "/api/v1/llm/stream", json=request_data) as response:
            print(f"HTTPステータス: {response.status_code}")

            if response.status_code == 200:
                print("✅ ストリーミング開始:")
                content_chunks = []

                for chunk in response.iter_text():
                    if chunk.strip():
                        try:
                            data = json.loads(chunk.strip())
                            if "text" in data:
                                content_chunks.append(data["text"])
                                print(f"  📥 chunk: {data['text'][:50]}...")
                            elif "done" in data and data["done"]:
                                print("  ✅ ストリーミング完了")
                            elif "error" in data:
                                print(f"  ❌ エラー: {data['error']}")
                                return False
                        except json.JSONDecodeError:
                            # SSEのdata:プレフィックスなどを処理
                            if chunk.startswith("data: "):
                                try:
                                    data = json.loads(chunk[6:].strip())
                                    if "text" in data:
                                        content_chunks.append(data["text"])
                                        print(f"  📥 chunk: {data['text'][:50]}...")
                                    elif "done" in data and data["done"]:
                                        print("  ✅ ストリーミング完了")
                                except json.JSONDecodeError:
                                    continue

                # 全体のコンテンツを結合
                full_content = "".join(content_chunks)
                print(f"\n📋 結合されたコンテンツ: {full_content[:200]}...")

                # システムプロンプトが使用されたかをチェック
                if (
                    "microsoft/vscode" in full_content
                    or "Visual Studio Code" in full_content
                ):
                    print(
                        "✅ ストリーミングモードでもシステムプロンプトがレスポンスに反映されています"
                    )
                    return True
                else:
                    print(
                        "⚠️  ストリーミングモードでシステムプロンプトがレスポンスに反映されていない可能性があります"
                    )
                    print(f"     レスポンス内容: {full_content}")
                    return False

            else:
                print(f"❌ エラー: {response.status_code}")
                print(f"エラー内容: {response.text}")
                return False

    finally:
        # オーバーライドをクリア
        app.dependency_overrides.clear()


def test_streaming_simple():
    """シンプルなストリーミングテスト"""

    # FastAPIアプリケーションをインポートして依存関数をオーバーライド
    from doc_ai_helper_backend.main import app
    from doc_ai_helper_backend.api.dependencies import get_llm_service

    # 依存関数をモックサービスにオーバーライド
    app.dependency_overrides[get_llm_service] = get_mock_llm_service

    try:
        client = TestClient(app)

        request_data = {
            "prompt": "このドキュメントについて説明してください",
            "repository_context": {
                "service": "github",
                "owner": "microsoft",
                "repo": "vscode",
                "ref": "main",
                "current_path": "README.md",
            },
            "system_prompt_template": "contextual_document_assistant_ja",
            "include_document_in_system_prompt": True,
            "options": {"model": "mock"},
        }

        print("\n=== シンプルなストリーミングテスト ===")
        print(f"送信データ:")
        print(f"  - prompt: {request_data['prompt']}")
        print(
            f"  - repository: {request_data['repository_context']['owner']}/{request_data['repository_context']['repo']}"
        )
        print()

        response = client.post("/api/v1/llm/stream", json=request_data)

        print(f"HTTPステータス: {response.status_code}")

        if response.status_code == 200:
            # レスポンステキストを確認
            response_text = response.text
            print(f"レスポンステキスト（最初の200文字）: {response_text[:200]}...")

            # システムプロンプトが使用されたかをチェック
            if (
                "microsoft/vscode" in response_text
                or "Visual Studio Code" in response_text
            ):
                print(
                    "✅ ストリーミングモードでもシステムプロンプトがレスポンスに反映されています"
                )
                return True
            else:
                print(
                    "⚠️  ストリーミングモードでシステムプロンプトがレスポンスに反映されていない可能性があります"
                )
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
    print("🚀 ストリーミングモードでのシステムプロンプト生成テストを開始...")

    success_count = 0
    total_tests = 2

    if test_streaming_with_system_prompt():
        success_count += 1

    if test_streaming_simple():
        success_count += 1

    print(f"\n✅ テスト完了: {success_count}/{total_tests} 成功")

    if success_count == total_tests:
        print("🎉 すべてのテストが成功しました！")
    else:
        print("⚠️  一部のテストが失敗しました。")


if __name__ == "__main__":
    main()
