# 設定ファイル整理完了レポート

## 整理内容概要

### 削除された不要な設定

#### core/config.py から削除
- `secret_key`: 現在使用されていない
- `database_url`: データベースは現在モック実装のみ
- `gitlab_*`: GitLab統合は未実装
- `anthropic_*`, `gemini_*`: 現在OpenAIのみ実装
- `default_llm_provider`: OpenAI固定
- `supported_git_services`: 不要なリスト管理
- `llm_cache_ttl`, `llm_rate_limit`: 詳細設定は将来実装
- `cache_*`, `redis_url`: キャッシュは現在インメモリのみ
- `test_*`, `backend_api_url`: テスト設定は分離

#### services/mcp/config.py から削除
- `enable_github_tools`, `enable_utility_tools`: MCPサーバーから削除済み
- `allowed_origins`: CORS設定は本体アプリで管理
- `default_git_service`: core/config.pyで管理
- `github_*`, `forgejo_*`: 重複、環境変数から直接取得に変更
- `analysis_*`: LLM設定は統一
- `_register_utility_tools`: テスト用機能は削除済み

#### .env.example から削除
- 重複したGitHub/Forgejo設定セクション
- 未実装機能の設定（MCP_*, Database, Cache, Security, Testing）
- GitLab設定
- 詳細なForgejo設定（SSL, timeout, retries）
- 複雑なラベル設定

## 実装された修正

### MCPサーバーコード (services/mcp/server.py) の修正
- `enable_github_tools`, `enable_utility_tools` の参照を削除
- Git設定を環境変数から直接取得するように修正
- `_register_utility_tools` メソッドを削除
- サーバー情報レスポンスから削除された設定項目を除去
- Git tools は常に有効として簡略化

### 主要な変更点
1. **Git設定の統一**: GitHub/Forgejo設定は環境変数から直接取得
2. **不要な機能の削除**: Utility tools機能を完全削除
3. **設定の簡略化**: MCPConfigはサーバー基本情報とツール有効化フラグのみ
4. **エラー対策**: `extra="ignore"` でPydanticエラーを回避

## 残された必要最小限の設定

### core/config.py (メイン設定)
```python
class Settings(BaseSettings):
    # Basic settings
    debug: bool
    environment: str
    log_level: str
    app_name: str
    app_version: str
    api_prefix: str
    
    # Git services
    github_token: Optional[str]
    forgejo_token: Optional[str]
    forgejo_base_url: Optional[str]
    forgejo_username: Optional[str]
    forgejo_password: Optional[str]
    default_git_service: str
    
    # LLM (OpenAI only)
    openai_api_key: Optional[str]
    openai_base_url: Optional[str]
    default_openai_model: str
```

### services/mcp/config.py (MCP専用設定)
```python
class MCPConfig(BaseModel):
    # Server info
    server_name: str
    server_version: str
    description: str
    
    # Tool toggles
    enable_document_tools: bool
    enable_feedback_tools: bool
    enable_analysis_tools: bool
    
    # Security limits
    max_content_length: int
    max_tools_per_request: int
```

### .env.example (シンプル化)
```bash
# Basic app settings
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=DEBUG
APP_NAME=doc_ai_helper
APP_VERSION=0.1.0
API_PREFIX=/api/v1

# Git services
DEFAULT_GIT_SERVICE=github
GITHUB_TOKEN=your_token_here
FORGEJO_BASE_URL=https://git.example.com
FORGEJO_TOKEN=your_token_here

# LLM
DEFAULT_OPENAI_MODEL=gpt-3.5-turbo
OPENAI_API_KEY=your_api_key_here
```

## 設定階層の明確化

1. **core/config.py**: アプリケーション全体の基本設定
2. **services/mcp/config.py**: MCP機能固有の設定
3. **.env.example**: 環境変数のテンプレート

## 利点

1. **重複排除**: 同じ設定が複数箇所にある問題を解決
2. **現実的**: 実際に実装されている機能のみの設定
3. **保守性向上**: 設定の管理が簡素化
4. **理解しやすさ**: 必要最小限で分かりやすい構造
5. **将来拡張性**: 新機能追加時に適切な場所に設定を追加可能

## 注意事項

- 既存の`.env`ファイルがある場合は、新しい`.env.example`に合わせて更新が必要
- 削除された設定を使用しているコードがある場合は、適切にデフォルト値を使用するよう修正済み
- 将来の機能拡張時は、段階的に設定を追加することを推奨
