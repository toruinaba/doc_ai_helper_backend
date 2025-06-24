"""
MCP統合テスト用の共通設定とフィクスチャ。
"""

import asyncio
import os
import pytest
from typing import AsyncGenerator, Dict, Any

from doc_ai_helper_backend.services.mcp.server import DocumentAIHelperMCPServer
from doc_ai_helper_backend.services.mcp.config import MCPConfig


@pytest.fixture(scope="session")
def event_loop():
    """セッション全体で使用するイベントループ。"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
async def mcp_server() -> AsyncGenerator[DocumentAIHelperMCPServer, None]:
    """MCP統合テスト用のサーバーインスタンス。"""
    # テスト用設定
    config = MCPConfig(
        server_name="test_doc_ai_helper_mcp",
        enable_document_tools=True,
        enable_feedback_tools=True,
        enable_analysis_tools=True,
        enable_github_tools=False,  # 統合テストでは無効化（API制限回避）
        enable_utility_tools=True,
    )

    server = DocumentAIHelperMCPServer(config)
    yield server
    # クリーンアップは特に不要（in-memoryのため）


@pytest.fixture
async def mcp_server_with_github() -> AsyncGenerator[DocumentAIHelperMCPServer, None]:
    """GitHub機能有効化したMCP統合テスト用サーバー。"""
    # GitHub API制限を考慮し、環境変数でのみ有効化
    github_enabled = (
        os.getenv("ENABLE_GITHUB_INTEGRATION_TESTS", "false").lower() == "true"
    )

    config = MCPConfig(
        server_name="test_doc_ai_helper_mcp_github",
        enable_document_tools=True,
        enable_feedback_tools=True,
        enable_analysis_tools=True,
        enable_github_tools=github_enabled,
        enable_utility_tools=True,
    )

    server = DocumentAIHelperMCPServer(config)
    yield server


@pytest.fixture
def sample_markdown_content() -> str:
    """統合テスト用のMarkdownサンプルコンテンツ。"""
    return """# プロジェクト概要

このプロジェクトは文書AI支援ツールです。

## 主な機能

1. **ドキュメント解析**: Markdownファイルの構造分析
2. **フィードバック生成**: 会話からの改善提案作成
3. **GitHub連携**: Issue/PR自動作成

### 技術スタック

- Python 3.12+
- FastAPI
- FastMCP

## 使用方法

```python
from doc_ai_helper_backend import DocumentService

service = DocumentService()
result = service.analyze("README.md")
```

詳細は [公式ドキュメント](https://docs.example.com) を参照してください。
"""


@pytest.fixture
def sample_conversation_history() -> list[Dict[str, Any]]:
    """統合テスト用の会話履歴サンプル。"""
    return [
        {
            "role": "user",
            "content": "このREADME.mdの構造について教えてください。",
            "timestamp": "2024-01-15T10:00:00Z",
        },
        {
            "role": "assistant",
            "content": "README.mdは以下の構造になっています：\n1. プロジェクト概要\n2. 主な機能\n3. 技術スタック\n4. 使用方法",
            "timestamp": "2024-01-15T10:00:05Z",
        },
        {
            "role": "user",
            "content": "もう少し詳しい説明が必要だと思います。改善提案をお願いします。",
            "timestamp": "2024-01-15T10:01:00Z",
        },
    ]


# pytest markers for MCP integration tests
pytestmark = [
    pytest.mark.integration,
    pytest.mark.mcp,
    pytest.mark.asyncio,
]
