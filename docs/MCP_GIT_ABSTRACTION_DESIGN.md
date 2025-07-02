# MCP Git Tools Abstraction Design

## 概要

doc_ai_helper_backendのMCPツール層を抽象化し、複数のGitホスティングサービス（GitHub、Forgejo等）に対応できる統一インターフェースを提供するアーキテクチャ設計文書です。

## 🎯 目標

1. **統一インターフェース**: 複数のGitサービスを統一的な方法で操作
2. **拡張性**: 新しいGitサービスの簡単な追加
3. **セキュリティ**: リポジトリコンテキスト検証による安全な操作
4. **後方互換性**: 既存のGitHub MCPツールとの互換性維持
5. **設定の柔軟性**: 環境変数やconfig経由での動的設定

## 🏗️ アーキテクチャ設計

### レイヤー構造

```
┌─────────────────────────────────────────────────────────┐
│                    MCP Server                           │
│  - 統合Gitツール登録                                      │
│  - リポジトリコンテキスト管理                               │
│  - ツール呼び出し処理                                      │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│                Unified Git Tools                        │
│  - マルチサービス管理                                      │
│  - サービス切り替え                                        │
│  - デフォルトサービス設定                                   │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│               Git Tools Factory                         │
│  - アダプター生成                                          │
│  - 設定管理                                              │
│  - サービス登録                                            │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│            Abstract Base Classes                       │
│  - MCPGitToolsBase: 共通操作定義                          │
│  - MCPGitClientBase: APIクライアント抽象化                │
│  - リポジトリコンテキスト検証                               │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│           Service-Specific Adapters                    │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │ GitHub Adapter   │  │ Forgejo Adapter  │              │
│  │ - GitHub API連携  │  │ - Forgejo API連携 │              │
│  │ - GitHub認証      │  │ - Token/Basic認証 │              │
│  │ - エラーハンドリング │  │ - エラーハンドリング │              │
│  └──────────────────┘  └──────────────────┘              │
└─────────────────────────────────────────────────────────┘
                              │
┌─────────────────────────────────────────────────────────┐
│              Git Service Layer                          │
│  ┌──────────────────┐  ┌──────────────────┐              │
│  │ GitHub Service   │  │ Forgejo Service  │              │ 
│  │ (既存)            │  │ (既存)            │              │
│  └──────────────────┘  └──────────────────┘              │
└─────────────────────────────────────────────────────────┘
```

### クラス設計

#### 1. Abstract Base Classes

**MCPGitClientBase**
```python
class MCPGitClientBase(ABC):
    """Git APIクライアントの抽象基底クラス"""
    
    @abstractmethod
    async def create_issue(
        self, repository: str, title: str, description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None, **kwargs
    ) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def create_pull_request(
        self, repository: str, title: str, description: str,
        head_branch: str, base_branch: str = "main", **kwargs
    ) -> Dict[str, Any]:
        pass
    
    @abstractmethod
    async def check_repository_permissions(
        self, repository: str, **kwargs
    ) -> Dict[str, Any]:
        pass
```

**MCPGitToolsBase**
```python
class MCPGitToolsBase(ABC):
    """MCPツールの抽象基底クラス"""
    
    def __init__(self, client: MCPGitClientBase):
        self.client = client
    
    async def create_issue(self, ...) -> str:
        # 共通処理: コンテキスト検証、エラーハンドリング
        pass
    
    async def create_pull_request(self, ...) -> str:
        # 共通処理: コンテキスト検証、エラーハンドリング
        pass
    
    async def check_repository_permissions(self, ...) -> str:
        # 共通処理: コンテキスト検証、エラーハンドリング
        pass
    
    def _validate_repository_context(self, context) -> RepositoryContext:
        # リポジトリコンテキスト検証
        pass
    
    def _validate_repository_access(self, requested_repo, context) -> None:
        # リポジトリアクセス検証（セキュリティ）
        pass
    
    @property
    @abstractmethod
    def service_name(self) -> str:
        pass
```

#### 2. Service-Specific Adapters

**GitHub Adapter**
```python
class MCPGitHubClient(MCPGitClientBase):
    """GitHub API専用クライアント"""
    
    def __init__(self, access_token: Optional[str] = None):
        self.github_client = GitHubClient(token=access_token)
    
    async def create_issue(self, ...) -> Dict[str, Any]:
        # GitHub APIを使用したIssue作成
        pass

class MCPGitHubAdapter(MCPGitToolsBase):
    """GitHub専用MCPツールアダプター"""
    
    def __init__(self, access_token: Optional[str] = None, **kwargs):
        client = MCPGitHubClient(access_token=access_token)
        super().__init__(client)
    
    @property
    def service_name(self) -> str:
        return "github"
    
    async def create_issue(self, ...) -> str:
        # GitHub特有のエラーハンドリング付きでベースクラス呼び出し
        pass
```

**Forgejo Adapter**
```python
class MCPForgejoClient(MCPGitClientBase):
    """Forgejo API専用クライアント"""
    
    def __init__(self, base_url: str, access_token: Optional[str] = None,
                 username: Optional[str] = None, password: Optional[str] = None):
        self.forgejo_service = ForgejoService(...)
    
    async def create_issue(self, ...) -> Dict[str, Any]:
        # Forgejo APIを使用したIssue作成
        pass

class MCPForgejoAdapter(MCPGitToolsBase):
    """Forgejo専用MCPツールアダプター"""
    
    @property
    def service_name(self) -> str:
        return "forgejo"
```

#### 3. Factory Pattern

```python
class MCPGitToolsFactory:
    """Gitツールアダプターのファクトリー"""
    
    _adapters = {
        "github": MCPGitHubAdapter,
        "forgejo": MCPForgejoAdapter,
    }
    
    @classmethod
    def create(cls, service_type: str, config: Optional[Dict] = None, **kwargs) -> MCPGitToolsBase:
        # サービス種別に応じたアダプター生成
        pass
    
    @classmethod
    def create_from_repository_context(cls, repository_context: Dict, **kwargs) -> MCPGitToolsBase:
        # リポジトリコンテキストからサービス自動判定してアダプター生成
        pass
```

#### 4. Unified Interface

```python
class UnifiedGitTools:
    """統合Gitツールインターフェース"""
    
    def __init__(self):
        self._adapters: Dict[str, MCPGitToolsBase] = {}
        self._default_service: Optional[str] = None
    
    def configure_service(self, service_type: str, config: Dict, set_as_default: bool = False):
        # サービス設定
        pass
    
    async def create_issue(self, ..., service_type: Optional[str] = None) -> str:
        # 統一インターフェースでのIssue作成
        pass
    
    def get_adapter(self, service_type: Optional[str] = None) -> MCPGitToolsBase:
        # 指定サービスまたはデフォルトのアダプター取得
        pass
```

### データフロー

#### Issue作成のデータフロー

```
[MCP Server] 
    ↓ create_git_issue()
[Unified Git Tools]
    ↓ service_type判定 (context or explicit)
[GitHub/Forgejo Adapter]
    ↓ repository context validation
[MCPGitToolsBase]
    ↓ _validate_repository_access()
[GitHub/Forgejo Client]
    ↓ GitHub API / Forgejo API
[External Git Service]
    ↓ Response
[Adapter] 
    ↓ error handling & formatting
[MCP Server]
    ↓ JSON response
[Frontend/LLM]
```

## 🔧 実装仕様

### 1. ファイル構成

```
doc_ai_helper_backend/
├── services/mcp/tools/
│   ├── git/                          # Git抽象化層
│   │   ├── __init__.py
│   │   ├── base.py                   # 抽象基底クラス
│   │   ├── github_adapter.py         # GitHub実装
│   │   ├── forgejo_adapter.py        # Forgejo実装
│   │   └── factory.py                # ファクトリー
│   ├── git_tools.py                  # 統合インターフェース
│   └── github_tools.py               # 既存 (後方互換性)
├── services/mcp/
│   ├── server.py                     # MCPサーバー統合
│   └── config.py                     # 設定拡張
```

### 2. 設定管理

**環境変数**
```bash
# デフォルトGitサービス
DEFAULT_GIT_SERVICE=github

# GitHub設定
GITHUB_TOKEN=ghp_xxxxx

# Forgejo設定
FORGEJO_BASE_URL=http://localhost:3000
FORGEJO_TOKEN=xxxxx
# または
FORGEJO_USERNAME=user
FORGEJO_PASSWORD=pass
```

**MCPConfig拡張**
```python
class MCPConfig(BaseModel):
    # 既存設定...
    
    # Git統合設定
    default_git_service: str = "github"
    
    # GitHub設定
    github_token: Optional[str] = None
    github_default_labels: List[str] = ["documentation", "improvement"]
    
    # Forgejo設定
    forgejo_base_url: Optional[str] = None
    forgejo_token: Optional[str] = None
    forgejo_username: Optional[str] = None
    forgejo_password: Optional[str] = None
    forgejo_default_labels: List[str] = ["documentation", "improvement"]
```

### 3. MCPサーバー統合

**ツール登録**
```python
class DocumentAIHelperMCPServer:
    def _setup_unified_git_tools(self):
        # 設定に基づいてGitサービスを構成
        pass
    
    def _register_git_tools(self):
        @self.app.tool("create_git_issue")
        async def create_issue_tool(
            title: str, description: str,
            labels: Optional[List[str]] = None,
            assignees: Optional[List[str]] = None,
            service_type: Optional[str] = None,
            github_token: Optional[str] = None,
            forgejo_token: Optional[str] = None,
            # ...
        ) -> str:
            # 統合インターフェース経由でIssue作成
            pass
```

### 4. リポジトリコンテキスト検証

**セキュリティ仕様**
```python
def _validate_repository_access(requested_repository: str, repository_context: RepositoryContext):
    """
    要求されたリポジトリが現在のコンテキストと一致することを検証
    
    - 異なるリポジトリへのアクセス試行をブロック
    - セキュリティ侵害の防止
    - 意図しない操作の防止
    """
    if requested_repository != repository_context.repository_full_name:
        raise PermissionError("Access denied: Repository mismatch")
```

### 5. エラーハンドリング

**統一エラーレスポンス**
```json
{
  "success": false,
  "error": "エラーメッセージ",
  "error_type": "repository_not_found",
  "service": "github"
}
```

**サービス固有エラー**
- GitHub: `GitHubRepositoryNotFoundError`, `GitHubPermissionError`
- Forgejo: `NotFoundException`, `UnauthorizedException`

## 🧪 テスト戦略

### 1. Unit Tests

**抽象基底クラス**
- `test_base.py`: MCPGitToolsBase, MCPGitClientBase
- Mock実装でのインターフェース検証
- リポジトリコンテキスト検証テスト

**アダプター実装**
- `test_github_adapter.py`: GitHub特有機能
- `test_forgejo_adapter.py`: Forgejo特有機能
- API呼び出しのmock化

**ファクトリー**
- `test_factory.py`: サービス生成、設定管理
- 環境変数からの設定読み込み

### 2. Integration Tests

**サービス統合**
- 実際のAPI呼び出し（スキップ可能）
- エラーケースハンドリング
- レスポンス形式検証

**MCP統合**
- MCPサーバーでのツール実行
- マルチサービス切り替え
- コンテキスト管理

### 3. E2E Tests

**フロントエンド統合**
- API経由でのMCPツール実行
- サービス選択機能
- エラー表示とハンドリング

## 🚀 デプロイメント

### 1. 段階的展開

**Phase 1: 基盤実装**
- 抽象基底クラス
- GitHub/Forgejoアダプター
- ファクトリー実装

**Phase 2: MCPサーバー統合**
- 統合ツール登録
- 設定管理拡張
- 既存機能との互換性確保

**Phase 3: テスト実装**
- 単体テスト
- 統合テスト
- デモスクリプト

**Phase 4: 文書化**
- API文書更新
- 使用例追加
- セットアップガイド

### 2. 後方互換性

**既存GitHubツール**
- `github_tools.py`は引き続き利用可能
- 既存のMCPツール名は維持
- 段階的移行サポート

**設定移行**
- 既存の`GITHUB_TOKEN`は継続利用
- 新しい統合設定は追加的に導入

## 📊 メトリクス

### 1. パフォーマンス指標

- アダプター生成時間: < 100ms
- API応答時間: サービス依存（通常1-3秒）
- メモリ使用量: サービス毎に+50MB以下

### 2. 拡張性指標

- 新サービス追加: 3ファイル（client, adapter, test）
- 設定項目追加: MCPConfig拡張のみ
- テストカバレッジ: 95%以上

## 🔮 将来拡張

### 1. 追加Gitサービス

**GitLab対応**
```python
class MCPGitLabAdapter(MCPGitToolsBase):
    @property
    def service_name(self) -> str:
        return "gitlab"
```

**BitBucket対応**
```python
class MCPBitBucketAdapter(MCPGitToolsBase):
    @property  
    def service_name(self) -> str:
        return "bitbucket"
```

### 2. 高度な機能

**バッチ処理**
- 複数リポジトリへの一括操作
- 並列処理サポート

**キャッシュ機能**
- 権限情報のキャッシュ
- API結果のキャッシュ

**監査ログ**
- 操作履歴の記録
- セキュリティ監査

## 🔒 セキュリティ考慮事項

### 1. アクセス制御

- リポジトリコンテキスト検証の強制
- 異なるリポジトリへのアクセス拒否
- トークン/認証情報の安全な管理

### 2. 入力検証

- リポジトリ名の形式検証
- ブランチ名の検証
- ファイルパスの検証

### 3. エラー情報

- 機密情報の漏洩防止
- 適切なエラーメッセージ
- ログ出力の制御

## 📋 制限事項

### 1. 現在の制限

- リポジトリコンテキストが必要（セキュリティのため）
- サービス毎に異なる認証方式
- API制限はサービス依存

### 2. 設計上の制限

- 同期的な処理（async/awaitベース）
- JSON形式のレスポンス
- リポジトリ単位での操作

## 💡 まとめ

このMCPツール抽象化設計により：

1. **統一性**: 複数のGitサービスを統一インターフェースで操作
2. **拡張性**: 新しいサービスの簡単な追加
3. **セキュリティ**: リポジトリコンテキスト検証による安全性
4. **保守性**: 明確な責任分離と抽象化
5. **互換性**: 既存機能との後方互換性

この設計により、doc_ai_helper_backendはGitホスティングサービスに依存しない柔軟なソリューションとなります。
