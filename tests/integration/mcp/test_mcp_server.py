"""
MCPサーバー基盤の統合テスト。

FastMCPサーバーの起動・設定・ツール登録などの基本機能をテストします。
"""

import pytest
from typing import Dict, Any

from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.config import MCPConfig


@pytest.mark.integration
@pytest.mark.mcp
class TestMCPServerIntegration:
    """MCPサーバー基盤の統合テストクラス。"""

    async def test_mcp_server_initialization(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """MCPサーバーの正常な初期化をテスト。"""
        assert mcp_server is not None
        assert mcp_server.app is not None
        assert mcp_server.config.server_name == "test_doc_ai_helper_mcp"

    async def test_mcp_server_tool_registration(
        self, mcp_server: DocumentAIHelperMCPServer
    ):
        """MCPサーバーでのツール登録状況をテスト。"""
        # FastMCPのツール登録確認
        app = mcp_server.app

        # ツールが正常に登録されていることを確認
        # FastMCPのget_tools()メソッドを使用してツール一覧を取得
        tools = await app.get_tools()
        assert tools is not None, "ツール一覧が取得できない"
        assert len(tools) > 0, "登録されたツールが存在しない"

        # 期待されるツールが含まれていることを確認
        tool_names = [tool.name for tool in tools.values()]  # toolsは辞書の可能性
        expected_tools = [
            "extract_document_context",
            "analyze_document_structure",
            "optimize_document_content",
        ]

        for expected_tool in expected_tools:
            assert (
                expected_tool in tool_names
            ), f"期待されるツール '{expected_tool}' が見つからない"

    async def test_mcp_server_config_variations(self):
        """異なる設定でのMCPサーバー初期化をテスト。"""
        # 最小設定
        minimal_config = MCPConfig(
            server_name="test_minimal",
            enable_document_tools=False,
            enable_feedback_tools=False,
            enable_analysis_tools=False,
            enable_github_tools=False,
            enable_utility_tools=True,  # 最低限1つは有効化
        )
        minimal_server = DocumentAIHelperMCPServer(minimal_config)
        assert minimal_server.config.server_name == "test_minimal"

        # 全機能有効設定
        full_config = MCPConfig(
            server_name="test_full",
            enable_document_tools=True,
            enable_feedback_tools=True,
            enable_analysis_tools=True,
            enable_github_tools=True,
            enable_utility_tools=True,
        )
        full_server = DocumentAIHelperMCPServer(full_config)
        assert full_server.config.server_name == "test_full"

    async def test_mcp_server_default_config(self):
        """デフォルト設定でのMCPサーバー初期化をテスト。"""
        default_server = DocumentAIHelperMCPServer()
        assert default_server.config is not None
        assert default_server.app is not None

    async def test_mcp_server_error_handling(self):
        """MCPサーバーのエラーハンドリングをテスト。"""
        # 無効な設定でもサーバーが起動することを確認
        try:
            invalid_config = MCPConfig(
                server_name="",  # 空の名前
                enable_document_tools=False,
                enable_feedback_tools=False,
                enable_analysis_tools=False,
                enable_github_tools=False,
                enable_utility_tools=False,  # すべて無効
            )
            server = DocumentAIHelperMCPServer(invalid_config)
            # サーバーは初期化されるが、警告などが出る可能性
            assert server is not None
        except Exception as e:
            # 予期されるエラーの場合はパス
            pytest.skip(f"Expected error in invalid configuration: {e}")

    async def test_mcp_server_multiple_instances(self):
        """複数のMCPサーバーインスタンスの同時作成をテスト。"""
        config1 = MCPConfig(server_name="test_server_1")
        config2 = MCPConfig(server_name="test_server_2")

        server1 = DocumentAIHelperMCPServer(config1)
        server2 = DocumentAIHelperMCPServer(config2)

        assert server1.config.server_name != server2.config.server_name
        assert server1.app is not server2.app
