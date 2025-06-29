"""
MCP Function Calling統合テスト。

LLMサービス経由でのMCPツール呼び出しとFunction Calling機能をテストします。
"""

import os
import pytest
from typing import Dict, Any, List
from unittest.mock import AsyncMock, patch

from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.function_manager import FunctionRegistry
from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer


@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.function_calling
class TestMCPFunctionCallingIntegration:
    """MCP Function Calling統合テストクラス。"""

    async def test_llm_mcp_tool_integration_mock(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """MockLLMサービス経由でのMCPツール統合をテスト。"""
        # MockLLMサービスを使用（外部API不要）
        llm_service = LLMServiceFactory.create("mock")

        # Function Callingオプションを設定
        options = {
            "enable_function_calling": True,
            "available_functions": [
                "extract_document_context",
                "analyze_document_structure",
                "calculate",
            ],
        }

        prompt = """このMarkdownドキュメントを分析してください：
        # テストドキュメント
        これはテスト用のドキュメントです。
        """

        # MockLLMサービスでのFunction Calling（モック動作）
        response = await llm_service.query(prompt, None, options)

        assert response is not None
        assert hasattr(response, "content")

    @pytest.mark.skipif(
        not os.getenv("OPENAI_API_KEY"),
        reason="OpenAI API key not available for integration test",
    )
    async def test_llm_mcp_tool_integration_openai(
        self, mcp_server: DocumentAIHelperMCPServer, sample_markdown_content: str
    ):
        """OpenAIサービス経由でのMCPツール統合をテスト（API key必要）。"""
        # 環境変数から設定を取得
        api_key = os.getenv("OPENAI_API_KEY")
        openai_model = os.getenv(
            "OPENAI_MODEL", "gpt-3.5-turbo"
        )  # デフォルトはgpt-3.5-turbo
        openai_base_url = os.getenv("OPENAI_BASE_URL")  # オプション

        # OpenAIサービスの設定
        openai_config = {"api_key": api_key, "default_model": openai_model}

        # カスタムベースURLが設定されている場合は追加
        if openai_base_url:
            openai_config["base_url"] = openai_base_url

        llm_service = LLMServiceFactory.create("openai", **openai_config)

        # Function Callingオプションを設定
        options = {
            "enable_function_calling": True,
            "available_functions": [
                "extract_document_context",
                "analyze_document_structure",
            ],
            "max_tokens": 500,  # コスト制御
        }

        prompt = f"""以下のMarkdownドキュメントの構造を分析してください：

{sample_markdown_content}

analyze_document_structure関数を使用して分析を行ってください。"""

        # 実際のOpenAI Function Calling
        response = await llm_service.query(prompt, None, options)

        assert response is not None
        assert response.content
        # Function Callingが実行された場合、結果が含まれることを確認
        # （実際の実行結果は OpenAI の判断に依存）

    async def test_function_registry_mcp_integration(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """FunctionRegistryとMCPツールの統合をテスト。"""
        function_registry = FunctionRegistry()

        # MCPツール関数をインポート
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            extract_document_context,
        )

        # MCPツールを実際の関数として登録
        function_registry.register_function(
            name="extract_document_context",
            function=extract_document_context,
            description="Extract structured context from a document",
            parameters={
                "type": "object",
                "properties": {
                    "document_content": {"type": "string"},
                    "repository": {"type": "string"},
                    "path": {"type": "string"},
                },
                "required": ["document_content"],
            },
        )

        # 登録確認
        registered_functions = function_registry.get_all_functions()
        assert len(registered_functions) > 0

        # 特定の関数が登録されていることを確認
        assert "extract_document_context" in registered_functions
        assert (
            registered_functions["extract_document_context"] == extract_document_context
        )

    async def test_mcp_tool_chain_execution(
        self,
        mcp_server: DocumentAIHelperMCPServer,
        sample_markdown_content: str,
        sample_conversation_history: List[Dict[str, Any]],
    ):
        """複数MCPツールのチェーン実行をテスト。"""
        # モックベースでのチェーン実行テスト

        # Step 1: ドキュメント構造分析（ダミー実行）
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            analyze_document_structure,
        )

        structure_result = await analyze_document_structure(
            document_content=sample_markdown_content, document_type="markdown"
        )
        assert structure_result is not None
        assert isinstance(structure_result, dict)

        # Step 2: フィードバック生成（ダミー実行）
        from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
            generate_feedback_from_conversation,
        )

        feedback_result = await generate_feedback_from_conversation(
            conversation_history=sample_conversation_history,
            document_context=sample_markdown_content,
            feedback_type="improvement",
        )
        assert feedback_result is not None
        assert isinstance(feedback_result, str)

        # チェーン実行の完了を確認
        assert len(feedback_result) > 0

    async def test_mcp_function_calling_error_handling(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """MCP Function Callingのエラーハンドリングをテスト。"""
        # 無効なパラメータでのツール呼び出し
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            extract_document_context,
        )

        # 空のパラメータでテスト
        try:
            result = await extract_document_context(
                document_content="", repository="", path=""
            )
            # エラーにならない場合は警告として処理
            assert isinstance(result, str)
        except Exception as e:
            # 適切なエラーハンドリングがされていることを確認
            assert str(e)  # エラーメッセージが存在

    async def test_mcp_async_function_execution(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """MCPツールの非同期実行をテスト。"""
        import asyncio

        # 複数のツールを並行実行
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
            calculate,
            format_text,
        )

        tasks = [
            calculate(expression="10 + 20"),
            calculate(expression="50 * 2"),
            format_text(text="test content", style="uppercase"),
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # すべてのタスクが完了することを確認
        assert len(results) == 3

        # エラーではない結果を確認
        successful_results = [r for r in results if not isinstance(r, Exception)]
        assert len(successful_results) > 0
