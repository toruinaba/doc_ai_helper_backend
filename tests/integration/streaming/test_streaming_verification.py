"""
ストリーミングモードでのシステムプロンプト生成の簡単な検証テスト
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


def test_streaming_system_prompt_verification():
    """ストリーミングモードでのシステムプロンプト生成の簡単な検証"""

    # FastAPIアプリケーションをインポートして依存関数をオーバーライド
    from doc_ai_helper_backend.main import app
    from doc_ai_helper_backend.api.dependencies import get_llm_service

    # 依存関数をモックサービスにオーバーライド
    app.dependency_overrides[get_llm_service] = get_mock_llm_service

    try:
        # 直接MockLLMServiceをテストしてシステムプロンプトが機能することを確認
        mock_service = MockLLMService(response_delay=0.1)

        print("=== MockLLMService ストリーミング機能直接テスト ===")

        # SystemPromptBuilderをMockServiceに設定
        from doc_ai_helper_backend.services.llm.utils import SystemPromptBuilder

        mock_service.system_prompt_builder = SystemPromptBuilder()

        # リポジトリコンテキストを作成
        from doc_ai_helper_backend.models.repository_context import (
            RepositoryContext,
            DocumentMetadata,
        )

        repository_context = RepositoryContext(
            service="github",
            owner="microsoft",
            repo="vscode",
            ref="main",
            current_path="README.md",
        )

        document_metadata = DocumentMetadata(
            title="Visual Studio Code",
            type="markdown",
            filename="README.md",
            file_size=5120,
            language="en",
        )

        # ストリーミングクエリを実行
        async def test_streaming():
            print("ストリーミングクエリを実行中...")
            chunks = []
            async for chunk in mock_service.stream_query(
                "このドキュメントについて説明してください",
                repository_context=repository_context,
                document_metadata=document_metadata,
                system_prompt_template="contextual_document_assistant_ja",
                include_document_in_system_prompt=True,
                options={"model": "mock"},
            ):
                chunks.append(chunk)
                print(f"📥 chunk: {chunk[:50]}...")

            full_response = "".join(chunks)
            print(f"\n📋 完全なレスポンス: {full_response}")

            # システムプロンプトが反映されているかチェック
            if (
                "microsoft/vscode" in full_response
                or "Visual Studio Code" in full_response
            ):
                print(
                    "✅ ストリーミングモードでシステムプロンプトが正常に反映されています"
                )
                return True
            else:
                print("⚠️  システムプロンプトがレスポンスに反映されていません")
                return False

        # 非同期テストを実行
        result = asyncio.run(test_streaming())
        return result

    finally:
        # オーバーライドをクリア
        app.dependency_overrides.clear()


def main():
    """メイン関数"""
    print("🚀 ストリーミングモードでのシステムプロンプト生成の検証テストを開始...")

    success = test_streaming_system_prompt_verification()

    if success:
        print(
            "\n🎉 ストリーミングモードでのシステムプロンプト生成が正常に動作しています！"
        )
    else:
        print("\n⚠️  ストリーミングモードでのシステムプロンプト生成に問題があります。")


if __name__ == "__main__":
    main()
