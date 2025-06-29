"""
MCPパフォーマンス統合テスト。

MCPサーバーとツールのパフォーマンス、メモリ使用量、スケーラビリティをテストします。
"""

import asyncio
import time
import pytest
import psutil
import os
from typing import Dict, Any, List

from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer


@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.performance
class TestMCPPerformanceIntegration:
    """MCPパフォーマンス統合テストクラス。"""

    async def test_mcp_server_startup_performance(self):
        """MCPサーバーの起動時間をテスト。"""
        start_time = time.perf_counter()

        # MCPサーバー初期化
        server = DocumentAIHelperMCPServer()

        end_time = time.perf_counter()
        startup_time = end_time - start_time

        # 起動時間は2秒以内であることを確認
        assert startup_time < 2.0, f"Startup time {startup_time:.3f}s exceeded 2.0s"

        print(f"MCP Server startup time: {startup_time:.3f}s")

    async def test_tool_execution_performance(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """個別ツールの実行時間をテスト。"""
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import calculate
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            analyze_document_structure,
        )

        # Test data
        large_content = "# Large Document\n" + "This is a test content. " * 1000

        # Utility tool performance test
        start_time = time.perf_counter()
        calc_result = await calculate("100 * 200 + 50")
        calc_time = time.perf_counter() - start_time

        # 最小実行時間の保護
        if calc_time < 0.001:
            calc_time = 0.001

        assert (
            calc_time < 1.0
        ), f"Calculate execution time {calc_time:.2f}s exceeded 1.0s"

        # Document tool performance test
        start_time = time.perf_counter()
        doc_result = await analyze_document_structure(large_content, "markdown")
        doc_time = time.perf_counter() - start_time

        # 最小実行時間の保護
        if doc_time < 0.001:
            doc_time = 0.001

        assert doc_time < 3.0, f"Document analysis time {doc_time:.2f}s exceeded 3.0s"

        print(
            f"Tool execution times - Calculate: {calc_time:.3f}s, Document: {doc_time:.3f}s"
        )

    async def test_concurrent_tool_execution_performance(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """並行ツール実行のパフォーマンスをテスト。"""
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import calculate

        # 100個の並行計算タスク
        tasks = [calculate(f"10 + {i}") for i in range(100)]

        start_time = time.perf_counter()  # より高精度な時間計測
        results = await asyncio.gather(*tasks)
        end_time = time.perf_counter()

        execution_time = end_time - start_time

        # 実行時間が極めて短い場合の保護処理
        if execution_time < 0.001:  # 1ms未満の場合
            execution_time = 0.001  # 最小値として1msを設定

        throughput = len(tasks) / execution_time

        # 100タスクを10秒以内で実行（スループット 10 tasks/sec以上）
        assert (
            execution_time < 10.0
        ), f"Concurrent execution time {execution_time:.3f}s exceeded 10.0s"
        assert throughput > 10.0, f"Throughput {throughput:.2f} tasks/sec is below 10.0"

        # 全タスクが成功したことを確認
        assert len(results) == 100
        assert all(r is not None for r in results)

        print(
            f"Concurrent performance: {throughput:.2f} tasks/sec, {execution_time:.3f}s total"
        )

    async def test_memory_usage_during_execution(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """ツール実行中のメモリ使用量をテスト。"""
        import gc

        # 初期メモリ使用量
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        # 大量のドキュメント処理タスク
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            extract_document_context,
        )

        large_documents = []
        for i in range(20):
            content = f"# Document {i}\n" + "Large content. " * 500
            large_documents.append(content)

        tasks = [
            extract_document_context(doc, f"repo_{i}", f"doc_{i}.md")
            for i, doc in enumerate(large_documents)
        ]

        # タスク実行
        results = await asyncio.gather(*tasks)

        # 実行後のメモリ使用量
        peak_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = peak_memory - initial_memory

        # メモリ増加量が500MB以下であることを確認
        assert (
            memory_increase < 500
        ), f"Memory increase {memory_increase:.2f}MB exceeded 500MB"

        # ガベージコレクション後のメモリ
        gc.collect()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        print(
            f"Memory usage - Initial: {initial_memory:.2f}MB, Peak: {peak_memory:.2f}MB, Final: {final_memory:.2f}MB"
        )

        # 結果の確認
        assert len(results) == 20
        assert all(isinstance(r, str) for r in results)

    async def test_long_running_session_stability(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """長時間セッションの安定性をテスト。"""
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
            calculate,
            format_text,
        )

        start_time = time.perf_counter()
        successful_operations = 0
        error_count = 0

        # 5分間または500回の操作（どちらか早い方）
        for i in range(500):
            try:
                if time.perf_counter() - start_time > 300:  # 5分でタイムアウト
                    break

                # 交互に異なるツールを実行
                if i % 2 == 0:
                    result = await calculate(f"10 * {i % 100}")
                else:
                    result = await format_text(f"text_{i}", "uppercase")

                if result is not None:
                    successful_operations += 1

                # 10操作ごとに短い待機
                if i % 10 == 0:
                    await asyncio.sleep(0.1)

            except Exception:
                error_count += 1
                if error_count > 10:  # エラーが多すぎる場合は中断
                    break

        end_time = time.perf_counter()
        duration = end_time - start_time

        # 成功率が95%以上であることを確認
        total_operations = successful_operations + error_count
        if total_operations > 0:
            success_rate = successful_operations / total_operations
            assert success_rate >= 0.95, f"Success rate {success_rate:.2%} is below 95%"
        else:
            # 操作が実行されなかった場合はテストを失敗とする
            assert False, "No operations were executed during the test"

        print(
            f"Long-running stability: {successful_operations} successful ops in {duration:.2f}s, {success_rate:.2%} success rate"
            if total_operations > 0
            else f"Long-running stability: No operations executed in {duration:.2f}s"
        )

    async def test_resource_cleanup_after_errors(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """エラー後のリソースクリーンアップをテスト。"""
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import calculate

        initial_memory = psutil.Process().memory_info().rss / 1024 / 1024

        # 意図的にエラーを発生させるタスク
        error_tasks = [calculate("invalid_expression") for _ in range(50)]

        # エラーを含む実行
        results = await asyncio.gather(*error_tasks, return_exceptions=True)

        # ガベージコレクション
        import gc

        gc.collect()
        await asyncio.sleep(1)  # クリーンアップ時間

        final_memory = psutil.Process().memory_info().rss / 1024 / 1024
        memory_change = abs(final_memory - initial_memory)

        # エラー処理後のメモリリークが50MB以下であることを確認
        assert memory_change < 50, f"Memory leak {memory_change:.2f}MB after errors"

        # エラーが適切に処理されたことを確認
        # calculateはJSONでエラーを返すため、結果の内容を確認
        import json

        error_count = 0
        for result in results:
            if isinstance(result, str):
                try:
                    result_data = json.loads(result)
                    if not result_data.get(
                        "success", True
                    ):  # successがFalseまたは存在しない場合
                        error_count += 1
                except (json.JSONDecodeError, TypeError):
                    # JSONパースエラーもエラーとしてカウント
                    error_count += 1
            elif isinstance(result, Exception):
                error_count += 1

        assert error_count > 0, "Error tasks should generate some errors"

        print(
            f"Resource cleanup test: {error_count} errors handled, {memory_change:.2f}MB memory change"
        )

    @pytest.mark.slow
    async def test_stress_test_mixed_operations(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """混合操作のストレステスト。"""
        from doc_ai_helper_backend.services.mcp.tools.document_tools import (
            analyze_document_structure,
        )
        from doc_ai_helper_backend.services.mcp.tools.utility_tools import (
            calculate,
            format_text,
        )
        from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
            generate_feedback_from_conversation,
        )

        # テストデータ
        test_content = "# Stress Test Document\n" + "Content for stress testing. " * 100
        test_conversation = [
            {
                "role": "user",
                "content": "Test message",
                "timestamp": "2024-01-01T00:00:00Z",
            }
        ]

        # 混合タスクセット
        mixed_tasks = []

        # Document tasks (30%)
        for i in range(30):
            mixed_tasks.append(analyze_document_structure(test_content, "markdown"))

        # Utility tasks (50%)
        for i in range(50):
            if i % 2 == 0:
                mixed_tasks.append(calculate(f"100 + {i}"))
            else:
                mixed_tasks.append(format_text(f"stress_test_{i}", "title"))

        # Feedback tasks (20%)
        for i in range(20):
            mixed_tasks.append(
                generate_feedback_from_conversation(
                    test_conversation, test_content, "analysis"
                )
            )

        # ストレステスト実行
        start_time = time.perf_counter()
        results = await asyncio.gather(*mixed_tasks, return_exceptions=True)
        end_time = time.perf_counter()

        execution_time = end_time - start_time
        successful_count = sum(1 for r in results if not isinstance(r, Exception))
        error_count = len(results) - successful_count
        total_results = len(results)

        if total_results > 0:
            success_rate = successful_count / total_results
        else:
            assert False, "No tasks were executed during stress test"

        # パフォーマンス要件
        assert execution_time < 60.0, f"Stress test took {execution_time:.2f}s (>60s)"
        assert success_rate >= 0.90, f"Success rate {success_rate:.2%} below 90%"

        print(
            f"Stress test: {len(mixed_tasks)} tasks in {execution_time:.2f}s, {success_rate:.2%} success rate"
        )
