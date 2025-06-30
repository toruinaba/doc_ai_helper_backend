# MCP統合テスト設計書

## 概要

Model Context Protocol（MCP）連携の統合テストの設計と実装方針を定義します。

## 現状の整理

### 実装済みコンポーネント
- ✅ MCPサーバー（FastMCPベース）: `doc_ai_helper_backend/services/mcp/server.py`
- ✅ MCPツール群: `doc_ai_helper_backend/services/mcp/tools/`
  - document_tools.py（ドキュメント解析・最適化）
  - feedback_tools.py（フィードバック収集・分析）
  - analysis_tools.py（テキスト分析・感情分析）
  - utility_tools.py（汎用ツール）
  - github_tools.py（GitHub連携）
- ✅ Function Calling機能: `doc_ai_helper_backend/services/llm/function_manager.py`
- ✅ MCPアダプター: `doc_ai_helper_backend/services/mcp/function_adapter.py`

### 既存ユニットテスト
- ✅ MCPサーバーテスト: `tests/unit/services/mcp_tests/test_mcp_server.py`
- ✅ MCPツールテスト: `tests/unit/services/mcp_tests/test_*_tools.py`
- ✅ Function Callingテスト: `tests/unit/api/test_function_calling_api.py`

## 統合テスト設計

### ディレクトリ構成

```
tests/
├── integration/
│   ├── mcp/                           # MCP統合テスト [新規作成]
│   │   ├── __init__.py
│   │   ├── conftest.py                # MCP統合テスト用フィクスチャ
│   │   ├── test_mcp_server_integration.py     # MCPサーバー統合テスト
│   │   ├── test_function_calling_e2e.py       # Function Calling E2Eテスト
│   │   ├── test_mcp_tools_integration.py      # MCPツール統合テスト
│   │   ├── test_mcp_llm_integration.py        # MCP-LLM統合テスト
│   │   └── test_mcp_performance.py            # MCPパフォーマンステスト
│   ├── llm/                           # 既存LLM統合テスト
│   │   ├── test_openai_service.py     # OpenAI実API統合テスト
│   │   └── test_llm_api_integration.py
│   └── git/                           # 既存Git統合テスト
│       └── test_github_service.py
```

### 統合テストの検証観点

#### 1. MCPサーバー統合テスト (`test_mcp_server_integration.py`)
```python
"""
MCPサーバーの統合テスト
- サーバー起動・停止
- ツール登録・発見
- クライアント接続・切断
- エラーハンドリング
"""

@pytest.mark.integration
@pytest.mark.mcp
class TestMCPServerIntegration:
    async def test_server_startup_and_shutdown(self):
        """MCPサーバーの起動・停止テスト"""
        
    async def test_tool_registration_and_discovery(self):
        """ツール登録と発見機能のテスト"""
        
    async def test_client_connection_lifecycle(self):
        """クライアント接続ライフサイクルテスト"""
        
    async def test_concurrent_clients(self):
        """複数クライアント同時接続テスト"""
```

#### 2. Function Calling E2Eテスト (`test_function_calling_e2e.py`)
```python
"""
Function Calling機能のE2Eテスト
- LLM → Function Calling → MCPツール → 結果返却
"""

@pytest.mark.integration
@pytest.mark.e2e
@pytest.mark.mcp
class TestFunctionCallingE2E:
    async def test_openai_to_mcp_tool_execution(self):
        """OpenAI → Function Calling → MCPツール実行"""
        
    async def test_mock_llm_to_mcp_tool_execution(self):
        """Mock LLM → Function Calling → MCPツール実行"""
        
    async def test_streaming_function_calling(self):
        """ストリーミング中のFunction Calling"""
        
    async def test_function_calling_error_recovery(self):
        """Function Callingエラー回復テスト"""
```

#### 3. MCPツール統合テスト (`test_mcp_tools_integration.py`)
```python
"""
各MCPツールの統合テスト
- 実際のドキュメント・フィードバックデータを使用
"""

@pytest.mark.integration
@pytest.mark.mcp
class TestMCPToolsIntegration:
    async def test_document_analysis_tools(self):
        """ドキュメント解析ツールの統合テスト"""
        
    async def test_feedback_collection_tools(self):
        """フィードバック収集ツールの統合テスト"""
        
    async def test_text_analysis_tools(self):
        """テキスト分析ツールの統合テスト"""
        
    async def test_github_tools_integration(self):
        """GitHubツールの統合テスト（API呼び出しモック）"""
        
    async def test_tool_chaining(self):
        """ツール連鎖実行テスト"""
```

#### 4. MCP-LLM統合テスト (`test_mcp_llm_integration.py`)
```python
"""
MCP機能とLLMサービスの統合テスト
- コンテキスト変換・最適化
"""

@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.llm
class TestMCPLLMIntegration:
    async def test_document_context_conversion(self):
        """ドキュメントコンテキスト変換テスト"""
        
    async def test_context_optimization(self):
        """コンテキスト最適化テスト"""
        
    async def test_conversation_history_integration(self):
        """会話履歴統合テスト"""
        
    async def test_mcp_prompt_template_integration(self):
        """MCPプロンプトテンプレート統合テスト"""
```

#### 5. MCPパフォーマンステスト (`test_mcp_performance.py`)
```python
"""
MCPのパフォーマンステスト
- レスポンス時間・スループット測定
"""

@pytest.mark.integration
@pytest.mark.mcp
@pytest.mark.performance
class TestMCPPerformance:
    async def test_tool_execution_performance(self):
        """ツール実行パフォーマンステスト"""
        
    async def test_concurrent_tool_execution(self):
        """同時ツール実行パフォーマンステスト"""
        
    async def test_large_context_processing(self):
        """大規模コンテキスト処理パフォーマンステスト"""
```

### pytest設定とマーカー

#### pyproject.tomlまたはpytest.ini追加設定
```ini
[tool.pytest.ini_options]
markers = [
    "integration: 統合テスト",
    "mcp: MCP関連テスト", 
    "e2e: エンドツーエンドテスト",
    "performance: パフォーマンステスト",
    "slow: 実行時間が長いテスト"
]
```

#### テスト実行コマンド例
```bash
# MCP統合テストのみ実行
pytest tests/integration/mcp/ -m mcp

# E2Eテストのみ実行  
pytest tests/integration/mcp/ -m e2e

# パフォーマンステスト除外
pytest tests/integration/mcp/ -m "mcp and not performance"

# 詳細出力でMCP統合テスト実行
pytest tests/integration/mcp/ -v -s --tb=short
```

### 環境変数管理

#### MCP統合テスト用環境変数
```python
# tests/integration/mcp/conftest.py
import os
import pytest
from doc_ai_helper_backend.services.mcp.server import MCPServer

@pytest.fixture
def mcp_test_config():
    """MCP統合テスト用設定"""
    return {
        "MCP_SERVER_HOST": "localhost",
        "MCP_SERVER_PORT": 8001,  # テスト用ポート
        "MCP_LOG_LEVEL": "DEBUG",
        "GITHUB_API_MOCK": "true",  # GitHub APIモック使用
        "OPENAI_API_KEY": os.getenv("OPENAI_API_KEY_TEST", "test-key"),
    }

@pytest.fixture
async def mcp_server(mcp_test_config):
    """MCPサーバーテスト用フィクスチャ"""
    server = MCPServer(config=mcp_test_config)
    await server.start()
    yield server
    await server.stop()
```

## 実装優先順位

### Phase 1: 基本統合テスト（1週間）
1. MCPサーバー統合テスト実装
2. 基本的なMCPツール統合テスト実装
3. テストフィクスチャとヘルパー実装

### Phase 2: E2E・高度な統合テスト（1週間）  
1. Function Calling E2Eテスト実装
2. MCP-LLM統合テスト実装
3. エラー・例外処理テストの拡充

### Phase 3: パフォーマンス・セキュリティテスト（1週間）
1. パフォーマンステスト実装
2. セキュリティテスト実装
3. CI/CD統合とテストレポート改善

## 期待効果

### 品質向上
- MCP機能の品質保証
- リグレッション防止
- パフォーマンス監視

### 開発効率向上
- 統合バグの早期発見
- リファクタリング時の安全性確保
- 新機能追加時の影響範囲把握

### 運用安定性向上
- 本番環境での問題予防
- 監視・アラート精度向上
- 障害時の原因特定迅速化

## 次のステップ

1. **Phase 1実装開始**: MCPサーバー統合テスト作成
2. **CI/CD統合**: 統合テスト自動実行環境構築
3. **テストデータ整備**: 統合テスト用のサンプルデータ作成
4. **ドキュメント更新**: 統合テスト実行方法とトラブルシューティング
