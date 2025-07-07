# 統合テストリファクタリング計画

**作成日**: 2025年7月7日  
**対象**: `tests/integration/` ディレクトリの構造改善とテスト品質向上

## 📊 現状分析

### ソースコード層の実装状況

#### Git層 (`services/git/`)
- **実装サービス**: GitHub, Forgejo, Mock
- **ファイル構成**:
  - `base.py` - GitServiceBase抽象基底クラス
  - `factory.py` - GitServiceFactory (github/forgejo/mock対応)
  - `github_service.py` - GitHub API実装
  - `forgejo_service.py` - Forgejo API実装
  - `mock_service.py` - Mock実装 (ユニットテスト用)
  - `mock_data.py` - Mockデータ定義

#### LLM層 (`services/llm/`)
- **実装サービス**: OpenAI, Mock
- **ファイル構成**:
  - `base.py` - LLMServiceBase抽象基底クラス
  - `factory.py` - LLMServiceFactory (動的登録方式)
  - `openai_service.py` - OpenAI API実装
  - `mock_service.py` - Mock実装 (ユニットテスト用)
  - `query_manager.py` - クエリ管理
  - `functions/` - Function Calling機能群
  - `messaging/` - メッセージング機能
  - `processing/` - 処理機能
  - `utils/` - ユーティリティ
  - `mock/` - Mockサポート機能

#### MCP層 (`services/mcp/`)
- **実装機能**: MCPサーバー, Function Calling, ツール群
- **ファイル構成**:
  - `server.py` - FastMCPベースのMCPサーバー
  - `config.py` - MCP設定管理
  - `function_adapter.py` - Function Calling アダプター
  - `tools/` - MCPツール群 (document/feedback/analysis/git/utility)

### 統合テスト層の現状

#### 現在のディレクトリ構造
```
tests/integration/
├── conftest.py                     # 統合テスト共通設定
├── git/                            # Git層統合テスト
│   ├── test_github_service.py      # GitHub API統合テスト
│   ├── test_forgejo_api_integration.py # Forgejo API統合テスト
│   └── README.md                   # Git統合テストドキュメント
├── github/                         # GitHub統合テスト (統合対象)
│   ├── test_secure_github_integration.py
│   ├── test_llm_github_e2e.py
│   └── test_llm_github_e2e_fixed.py (重複)
├── llm/                            # LLM層統合テスト
│   ├── test_openai_service.py      # OpenAI API統合テスト
│   ├── test_llm_api_integration.py # LLM API統合テスト
│   └── README.md                   # LLM統合テストドキュメント
├── mcp/                            # MCP層統合テスト
│   ├── test_mcp_server.py          # MCPサーバー統合テスト
│   ├── test_mcp_function_calling.py # Function Calling統合テスト
│   ├── test_mcp_tools.py           # MCPツール統合テスト
│   ├── test_git_tools_server_integration.py # Git-MCP統合テスト
│   ├── test_mcp_e2e_scenarios.py   # MCPシナリオテスト
│   └── test_mcp_performance.py     # MCPパフォーマンステスト
├── streaming/                      # ストリーミング統合テスト (統合対象)
│   ├── test_streaming_verification.py
│   └── test_sse_streaming.py
├── api/                            # API統合テスト (E2E移動対象)
│   ├── test_git_tools_api_integration.py
│   └── test_html_documents.py
└── test_mcp_tools_integration.py   # 統合・整理対象
```

## 🎯 リファクタリング方針

### 基本方針
1. **外部サービステスト重視**: Mock例外処理を削除し、実際の外部API統合に特化
2. **層別分離**: Git/LLM/MCP層ごとの明確な責任分界
3. **E2E分離**: API経由のワークフローテストをE2E層に移動
4. **統合・重複排除**: 散在するテストファイルの統合と重複排除

### 統合テスト方針
- **外部サービスのみ**: 実際のGitHub/Forgejo/OpenAI API使用
- **環境変数チェック**: API キー未設定時はテストスキップ
- **統一インターフェース**: 抽象基底クラスによる統一実装
- **Mock使用禁止**: 統合テストでのMockサービス使用を廃止

## 📁 新しいディレクトリ構成

### 統合テスト層 (`tests/integration/`)
```
tests/integration/
├── conftest.py                     # 統合テスト共通設定 (外部サービス用)
├── git/                            # Git層統合テスト
│   ├── __init__.py
│   ├── test_github_integration.py   # GitHub外部API統合
│   ├── test_forgejo_integration.py  # Forgejo外部API統合
│   └── test_git_operations.py       # Git操作横断テスト
├── llm/                            # LLM層統合テスト
│   ├── __init__.py
│   ├── test_openai_integration.py   # OpenAI外部API統合
│   ├── test_streaming_integration.py # ストリーミング統合
│   └── test_llm_functions.py        # LLM Function統合
└── mcp/                            # MCP層統合テスト
    ├── __init__.py
    ├── test_mcp_server.py           # MCPサーバー統合
    ├── test_function_calling.py     # Function Calling統合
    ├── test_mcp_tools.py            # MCPツール統合
    └── test_mcp_git_integration.py  # MCP-Git統合
```

### E2Eテスト層 (`tests/e2e/`)
```
tests/e2e/                          # E2Eテスト (API経由)
├── conftest.py                     # E2E専用設定
├── test_api_documents.py           # ドキュメントAPI E2E
├── test_api_llm.py                 # LLM API E2E
├── test_api_mcp.py                 # MCP API E2E
├── test_workflow_github.py         # GitHub連携ワークフロー
├── test_workflow_scenarios.py      # 複合ワークフローシナリオ
└── test_forgejo_e2e_workflow.py    # 既存Forgejo E2E (維持)
```

## 🔄 実装計画

### Phase 1: ディレクトリ構造準備
1. **新しい統合テスト構造の作成**
   - `tests/integration/git/__init__.py` 作成
   - `tests/integration/llm/__init__.py` 作成  
   - `tests/integration/mcp/__init__.py` 作成

2. **E2Eテスト構造の作成**
   - `tests/e2e/conftest.py` 作成 (API用設定)

### Phase 2: ファイル移動・統合

#### 2.1 GitHub関連テストの統合
**移動・統合:**
- `tests/integration/github/test_secure_github_integration.py` → `tests/integration/git/test_github_integration.py` (統合)
- `tests/integration/github/test_llm_github_e2e.py` → `tests/e2e/test_workflow_github.py` (移動)
- `tests/integration/github/test_llm_github_e2e_fixed.py` → 削除 (重複)

**統合方針:**
- Git API操作テスト → `git/test_github_integration.py`
- E2Eワークフローテスト → `e2e/test_workflow_github.py`

#### 2.2 ストリーミングテストの統合
**移動・統合:**
- `tests/integration/streaming/test_streaming_verification.py` → `tests/integration/llm/test_streaming_integration.py` (統合)
- `tests/integration/streaming/test_sse_streaming.py` → `tests/integration/llm/test_streaming_integration.py` (統合)

**統合方針:**
- ストリーミング機能はLLMサービスの一部として統合

#### 2.3 API統合テストのE2E移動
**移動:**
- `tests/integration/api/test_git_tools_api_integration.py` → `tests/e2e/test_api_mcp.py` (統合)
- `tests/integration/api/test_html_documents.py` → `tests/e2e/test_api_documents.py` (統合)

#### 2.4 MCP統合テストの整理
**統合・整理:**
- `tests/integration/mcp/test_mcp_e2e_scenarios.py` → `tests/e2e/test_workflow_scenarios.py` (移動)
- MCP関連の重複ファイル統合と整理

### Phase 3: 既存ファイルの整理

#### 3.1 削除対象
- `tests/integration/github/` ディレクトリ全体
- `tests/integration/streaming/` ディレクトリ全体  
- `tests/integration/api/` ディレクトリ全体
- 重複・古いテストファイル

#### 3.2 統合対象
- `tests/integration/test_mcp_tools_integration.py` → 適切な層に統合

### Phase 4: Mock例外処理削除

#### 4.1 削除対象パターン
1. **Mock判定による分岐処理**
   ```python
   # ❌ 削除対象
   if isinstance(service, MockGitService):
       # Mock固有の処理
   ```

2. **Mock専用パラメータ・設定**
   ```python
   # ❌ 削除対象
   async def some_method(self, param: str, mock_behavior: Optional[str] = None):
   ```

3. **Mock固有の例外処理**
   ```python
   # ❌ 削除対象
   if service_type == "mock":
       return MockSpecificResponse()
   ```

4. **統合テスト内のMockサービス使用**
   ```python
   # ❌ 削除対象
   mock_service = MockGitService()
   ```

#### 4.2 正しい実装パターン
```python
# ✅ 正しい: 統一インターフェース
async def get_repository_structure(self, owner: str, repo: str, ref: str = "main"):
    """全てのサービスで統一されたインターフェース"""
    # Mock判定なしの統一実装

# ✅ 正しい: 抽象基底クラスの活用
class GitServiceBase(ABC):
    @abstractmethod
    async def get_file_content(self, owner: str, repo: str, path: str, ref: str) -> FileContent:
        """全実装で統一されたメソッド"""
        pass
```

### Phase 5: テスト設定とユーティリティの整理

#### 5.1 統合テスト設定 (`tests/integration/conftest.py`)
```python
# 外部サービス用設定
@pytest.fixture(scope="session")
def github_token():
    """GitHub統合テスト用トークン（環境変数から取得）"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN not set")
    return token

@pytest.fixture(scope="session")
def forgejo_config():
    """Forgejo統合テスト用設定"""
    config = {
        "base_url": os.getenv("FORGEJO_BASE_URL"),
        "access_token": os.getenv("FORGEJO_TOKEN")
    }
    if not all(config.values()):
        pytest.skip("Forgejo config not complete")
    return config

@pytest.fixture(scope="session")
def openai_api_key():
    """OpenAI統合テスト用APIキー"""
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        pytest.skip("OPENAI_API_KEY not set")
    return key
```

#### 5.2 E2Eテスト設定 (`tests/e2e/conftest.py`)
```python
# API経由テスト用設定
@pytest.fixture
def api_client():
    """E2Eテスト用APIクライアント"""
    return TestClient(app)

@pytest.fixture
def end_to_end_config():
    """E2E環境設定"""
    return {
        "base_url": "http://localhost:8000",
        "timeout": 30
    }
```

#### 5.3 テストマーカーの整理
```python
# pytest.ini または conftest.py
markers = [
    "integration: integration tests",
    "git: Git service integration tests", 
    "llm: LLM service integration tests",
    "mcp: MCP integration tests",
    "e2e: End-to-end tests",
    "streaming: Streaming functionality tests",
    "function_calling: Function calling tests",
    "github: Tests requiring GitHub API access",
    "forgejo: Tests requiring Forgejo API access",
    "openai: Tests requiring OpenAI API access"
]
```

### Phase 6: テスト実行設定の更新

#### 6.1 新しいテスト実行コマンド
```bash
# 層別テスト実行
pytest tests/integration/git/ -v      # Git層統合テスト
pytest tests/integration/llm/ -v      # LLM層統合テスト  
pytest tests/integration/mcp/ -v      # MCP層統合テスト
pytest tests/e2e/ -v                  # E2Eテスト

# マーカー別テスト実行
pytest -m git -v                      # Git関連テスト
pytest -m llm -v                      # LLM関連テスト
pytest -m mcp -v                      # MCP関連テスト
pytest -m "not (github or forgejo or openai)" -v  # 外部API不要テスト
```

#### 6.2 CI/CD設定更新
- テストパス変更に伴うCI設定の更新
- 環境変数設定の見直し
- 外部APIテストの適切な管理

## 🎯 期待される効果

### 1. テスト分類の明確化
- **統合テスト**: 各層の外部サービス統合テスト
- **E2Eテスト**: API経由のエンドツーエンド動作確認
- **ユニットテスト**: Mock使用による単体機能検証

### 2. メンテナンス性の向上
- 層別のテスト構成で責任境界が明確
- 関連テストの集約でデバッグ効率向上
- Mock例外処理削除による実装簡素化

### 3. 実行効率の改善
- 必要な層のみのテスト実行が可能
- 適切なマーカー付けでフィルタリング実行
- 環境依存テストの適切な管理

### 4. 拡張性の確保
- 新しいGitサービス追加時のテスト構造が明確
- 新しいLLMプロバイダー追加に対応
- 新しいMCPツール追加への対応

### 5. 品質向上
- 実際の外部サービスとの統合確認
- Mock依存の排除による実装品質向上
- テストの実行可能性と信頼性向上

## ⚠️ 注意事項

### 実施時の注意点
1. **段階的実施**: 一度に全てを移動せず、段階的にリファクタリング
2. **テスト実行確認**: 各段階でテストが正常実行されることを確認
3. **CI/CD更新**: テストパス変更に伴うCI設定の更新
4. **ドキュメント更新**: README.mdやテスト実行ガイドの更新

### 環境依存への対応
- 外部APIキー未設定時の適切なスキップ処理
- 外部サービス障害時のテスト失敗対策
- レート制限への対応

### バックアップとロールバック
- 作業前の現状テストファイルのバックアップ
- 各フェーズでのコミット・タグ作成
- 問題発生時のロールバック手順の準備

---

**最終更新**: 2025年7月7日  
**作成者**: GitHub Copilot  
**ステータス**: 計画策定完了 - 実装準備中
