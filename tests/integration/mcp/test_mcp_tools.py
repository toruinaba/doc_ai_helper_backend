"""
各種MCPツールの統合テスト。

Document/Feedback/GitHub/Utility各ツールの実際の動作をテストします。
"""

import os
import pytest
from typing import Dict, Any, List

from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer


@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.tools
class TestMCPToolsIntegration:
    """各種MCPツールの統合テストクラス。"""

    # Document Tools Tests
    async def test_document_tools_integration(
        self, mcp_server: DocumentAIHelperMCPServer, sample_markdown_content: str
    ):
        """Document toolsの統合テスト。"""
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            extract_document_context,
            analyze_document_structure,
            optimize_document_content,
        )

        # Test extract_document_context
        context_result = await extract_document_context(
            document_content=sample_markdown_content,
            repository="test/repo",
            path="README.md",
        )
        assert context_result is not None
        assert isinstance(context_result, str)
        assert len(context_result) > 0

        # Test analyze_document_structure
        structure_result = await analyze_document_structure(
            document_content=sample_markdown_content, document_type="markdown"
        )
        assert structure_result is not None
        assert isinstance(structure_result, dict)
        assert (
            "heading_levels" in structure_result or "total_headings" in structure_result
        )

        # Test optimize_document_content
        optimized_result = await optimize_document_content(
            document_content=sample_markdown_content, optimization_type="readability"
        )
        assert optimized_result is not None
        assert isinstance(optimized_result, str)
        assert len(optimized_result) > 0

    async def test_feedback_tools_integration(
        self,
        mcp_server: DocumentAIHelperMCPServer,
        sample_conversation_history: List[Dict[str, Any]],
        sample_markdown_content: str,
    ):
        """Feedback toolsの統合テスト。"""
        from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
            generate_feedback_from_conversation,
            create_improvement_proposal,
            analyze_conversation_patterns,
        )

        # Test generate_feedback_from_conversation
        feedback_result = await generate_feedback_from_conversation(
            conversation_history=sample_conversation_history,
            document_context=sample_markdown_content,
            feedback_type="improvement",
        )
        assert feedback_result is not None
        assert isinstance(feedback_result, str)
        assert len(feedback_result) > 0

        # Test create_improvement_proposal
        proposal_result = await create_improvement_proposal(
            current_content=sample_markdown_content,
            feedback_data=feedback_result,
            improvement_type="structure",
        )
        assert proposal_result is not None
        assert isinstance(proposal_result, str)
        assert len(proposal_result) > 0

        # Test analyze_conversation_patterns
        pattern_result = await analyze_conversation_patterns(
            conversation_history=sample_conversation_history, analysis_depth="detailed"
        )
        assert pattern_result is not None
        assert isinstance(pattern_result, dict)

    async def test_utility_tools_integration(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """Utility toolsの統合テスト。"""
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
            calculate,
            format_text,
        )

        # Test calculate
        calc_result_1 = await calculate(expression="10 + 20 * 2")
        assert calc_result_1 is not None
        assert isinstance(calc_result_1, (int, float, str))

        calc_result_2 = await calculate(expression="sqrt(16)")
        assert calc_result_2 is not None

        # Test format_text
        format_result_upper = await format_text(text="hello world", style="uppercase")
        assert format_result_upper is not None
        assert isinstance(format_result_upper, str)
        # JSON response contains the formatted text
        assert "HELLO WORLD" in format_result_upper

        format_result_title = await format_text(text="hello world", style="title")
        assert format_result_title is not None
        assert isinstance(format_result_title, str)
        assert "Hello World" in format_result_title

    @pytest.mark.skipif(
        True,  # GitHub tools not implemented yet
        reason="GitHub tools not implemented yet",
    )
    async def test_github_tools_integration(
        self, mcp_server_with_github: DocumentAIHelperMCPServer
    ):
        """GitHub toolsの統合テスト（GitHub token必要）。"""
        # GitHub tools not implemented yet
        pytest.skip("GitHub tools not implemented yet")

    async def test_tool_error_handling(self, mcp_server: DocumentAIHelperMCPServer):
        """各ツールのエラーハンドリングをテスト。"""
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            analyze_document_structure,
        )
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import calculate

        # Document tool - 無効な入力
        try:
            result = await analyze_document_structure(
                document_content="", document_type="invalid_type"
            )
            # エラーにならない場合でも適切な応答を確認
            assert result is not None
        except Exception as e:
            # 適切なエラーハンドリング
            assert str(e)

        # Utility tool - 無効な計算式
        try:
            result = await calculate(expression="invalid expression")
            # エラーハンドリングされた結果を確認
            assert "error" in str(result).lower() or result is None
        except Exception as e:
            # 適切なエラーメッセージ
            assert str(e)

    async def test_tool_performance(self, mcp_server: DocumentAIHelperMCPServer):
        """ツールのパフォーマンスをテスト。"""
        import time
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import calculate

        # 複数の計算を実行して時間を測定
        start_time = time.time()

        tasks = []
        for i in range(10):
            tasks.append(calculate(expression=f"10 + {i}"))

        # 並行実行
        import asyncio

        results = await asyncio.gather(*tasks)

        end_time = time.time()
        execution_time = end_time - start_time

        # パフォーマンス要件（10個のタスクが5秒以内）
        assert (
            execution_time < 5.0
        ), f"Execution time {execution_time} exceeded 5 seconds"
        assert len(results) == 10
        assert all(r is not None for r in results)
