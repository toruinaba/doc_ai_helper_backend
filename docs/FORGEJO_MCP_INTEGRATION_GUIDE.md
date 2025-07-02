# Forgejo MCP Integration Guide

## 概要

doc_ai_helper_backendにForgejoサポートを追加し、MCPツール層でGitHub/Forgejo両方に対応できる統合ガイドです。

## 🎯 Forgejoについて

**Forgejo**は軽量でセルフホスト可能なGit forgeです：

- **オープンソース**: Giteaからフォークされた完全にオープンなプロジェクト
- **セルフホスト**: プライベート環境での完全制御
- **Gitea互換**: Gitea APIとの完全互換性
- **軽量**: 最小限のリソースで動作
- **機能豊富**: Issue、PR、Wiki、Actions等をサポート

## 🚀 セットアップガイド

### 1. Forgejoインスタンスの準備

#### Docker Composeでの簡単セットアップ

```yaml
# docker-compose.forgejo.yml
version: '3.8'
services:
  forgejo:
    image: codeberg.org/forgejo/forgejo:7
    container_name: forgejo
    environment:
      - USER_UID=1000
      - USER_GID=1000
    restart: always
    volumes:
      - ./forgejo:/data
      - /etc/timezone:/etc/timezone:ro
      - /etc/localtime:/etc/localtime:ro
    ports:
      - "3000:3000"
      - "222:22"
    
  # PostgreSQL (オプション)
  postgres:
    image: postgres:15
    container_name: forgejo-postgres
    restart: always
    environment:
      POSTGRES_DB: forgejo
      POSTGRES_USER: forgejo
      POSTGRES_PASSWORD: forgejo_password
    volumes:
      - ./postgres-data:/var/lib/postgresql/data
```

```bash
# Forgejoを起動
docker-compose -f docker-compose.forgejo.yml up -d

# 初期設定は http://localhost:3000 でブラウザから実行
```

#### 手動セットアップ

```bash
# Forgejoバイナリダウンロード (Linux例)
wget https://codeberg.org/forgejo/forgejo/releases/download/v7.0.0/forgejo-7.0.0-linux-amd64
chmod +x forgejo-7.0.0-linux-amd64
mv forgejo-7.0.0-linux-amd64 /usr/local/bin/forgejo

# サービス起動
forgejo web
```

### 2. アクセストークンの作成

1. Forgejoにログイン: `http://localhost:3000`
2. ユーザー設定 → アプリケーション → アクセストークン
3. 新しいトークン作成
4. 必要な権限を選択:
   - `repo`: リポジトリアクセス
   - `write:issue`: Issue作成・編集
   - `write:pull_request`: PR作成・編集

### 3. 環境変数設定

```bash
# .env または環境変数
FORGEJO_BASE_URL=http://localhost:3000
FORGEJO_TOKEN=your_forgejo_access_token

# または基本認証
FORGEJO_USERNAME=your_username
FORGEJO_PASSWORD=your_password

# デフォルトサービスにする場合
DEFAULT_GIT_SERVICE=forgejo
```

## 🔧 実装詳細

### 1. Forgejoアダプター

#### 主要機能

```python
class MCPForgejoAdapter(MCPGitToolsBase):
    """Forgejo専用MCPツールアダプター"""
    
    # サポート機能
    - Issue作成 (create_issue)
    - Pull Request作成 (create_pull_request)  
    - リポジトリ権限確認 (check_repository_permissions)
    
    # 認証方式
    - アクセストークン認証
    - 基本認証 (username/password)
    
    # エラーハンドリング
    - 404: リポジトリ未発見
    - 401: 認証失敗
    - その他のHTTPエラー
```

#### API マッピング

| MCP操作 | Forgejo API | エンドポイント |
|---------|-------------|---------------|
| Issue作成 | POST /api/v1/repos/{owner}/{repo}/issues | Issue creation |
| PR作成 | POST /api/v1/repos/{owner}/{repo}/pulls | Pull request creation |
| 権限確認 | GET /api/v1/repos/{owner}/{repo} | Repository permissions |

### 2. 設定管理

#### MCPConfig拡張

```python
class MCPConfig(BaseModel):
    # 既存設定...
    
    # Git統合設定
    default_git_service: str = "github"  # または "forgejo"
    
    # Forgejo設定
    forgejo_base_url: Optional[str] = None
    forgejo_token: Optional[str] = None
    forgejo_username: Optional[str] = None
    forgejo_password: Optional[str] = None
    forgejo_default_labels: List[str] = ["documentation", "improvement"]
```

#### 設定優先順位

1. 関数呼び出し時の引数
2. MCPConfig設定
3. 環境変数
4. デフォルト値

### 3. MCPツール統合

#### 統合Gitツール

```python
# 使用例: サービス自動判定
await create_git_issue(
    title="Issue via Unified Interface",
    description="Auto-detected service from context",
    repository_context={
        "service": "forgejo",  # 自動的にForgejoアダプターを使用
        "owner": "user",
        "repo": "project",
        # ...
    }
)

# 使用例: 明示的サービス指定
await create_git_issue(
    title="Issue via Explicit Service",
    description="Explicitly use Forgejo",
    service_type="forgejo",
    forgejo_token="custom_token",
    repository_context={...}
)
```

#### MCPサーバーツール

```python
# MCPサーバー経由での呼び出し
mcp_server = get_mcp_server()

result = await mcp_server.call_tool(
    "create_git_issue",
    title="Issue from MCP Server",
    description="Created via MCP server interface",
    service_type="forgejo",
    forgejo_token="your_token"
)
```

## 🧪 テストとデバッグ

### 1. 基本接続テスト

```python
# examples/test_forgejo_mcp_tools.py
python examples/test_forgejo_mcp_tools.py
```

**期待される出力:**
```
🔧 Testing Forgejo MCP Tools Integration
==================================================
🌐 Forgejo Base URL: http://localhost:3000
🔑 Authentication: Token
✅ Forgejo adapter initialized successfully

📋 Test repository context: testuser/test-repo

🔐 Testing repository permissions check...
✅ Permissions check result: {"success": true, ...}

📝 Testing issue creation...
✅ Issue creation result: {"success": true, ...}

🎉 Forgejo MCP Tools test completed!
```

### 2. 統合テスト

```python
# examples/test_git_mcp_abstraction.py  
python examples/test_git_mcp_abstraction.py
```

### 3. マルチサービスデモ

```python
# examples/demo_multi_git_mcp.py
python examples/demo_multi_git_mcp.py
```

### 4. デバッグのヒント

#### 一般的な問題と解決法

**1. 接続エラー**
```
❌ Error: connection refused
```
- Forgejoが起動しているか確認: `curl http://localhost:3000`
- ファイアウォール設定確認
- ポート番号確認

**2. 認証エラー**
```
❌ Error: 401 authentication failed
```
- トークンの有効性確認
- トークンの権限確認
- 基本認証の場合はユーザー名/パスワード確認

**3. リポジトリアクセスエラー**
```
❌ Error: 404 repository not found
```
- リポジトリが存在するか確認
- リポジトリ名のフォーマット確認 (`owner/repo`)
- アクセス権限確認

#### ログ設定

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# より詳細なログ出力
logger = logging.getLogger("doc_ai_helper")
logger.setLevel(logging.DEBUG)
```

## 📋 使用例

### 1. 基本的なIssue作成

```python
from doc_ai_helper_backend.services.mcp.tools.git_tools import create_git_issue

# Forgejoリポジトリコンテキスト
forgejo_context = {
    "service": "forgejo",
    "owner": "myuser",
    "repo": "myproject", 
    "repository_full_name": "myuser/myproject",
    "current_path": "README.md",
    "base_url": "http://localhost:3000",
    "ref": "main"
}

result = await create_git_issue(
    title="Documentation Improvement",
    description="README needs better examples",
    labels=["documentation", "enhancement"],
    assignees=["myuser"],
    repository_context=forgejo_context,
    forgejo_token="your_token"
)

print(result)  # JSON形式の結果
```

### 2. Pull Request作成

```python
from doc_ai_helper_backend.services.mcp.tools.git_tools import create_git_pull_request

result = await create_git_pull_request(
    title="Add new feature",
    description="Implementing requested feature X",
    head_branch="feature/new-feature",
    base_branch="main",
    repository_context=forgejo_context,
    forgejo_token="your_token"
)
```

### 3. 権限確認

```python
from doc_ai_helper_backend.services.mcp.tools.git_tools import check_git_repository_permissions

result = await check_git_repository_permissions(
    repository_context=forgejo_context,
    forgejo_token="your_token"
)
```

### 4. MCPサーバー経由（推奨）

```python
from doc_ai_helper_backend.services.mcp import get_mcp_server

mcp_server = get_mcp_server()

# リポジトリコンテキストをセット
setattr(mcp_server, "_current_repository_context", forgejo_context)

# ツール実行
result = await mcp_server.call_tool(
    "create_git_issue",
    title="Issue via MCP",
    description="Created via MCP server",
    labels=["mcp", "test"],
    service_type="forgejo",
    forgejo_token="your_token"
)
```

## 🔄 GitHub/Forgejo 切り替え

### 1. 動的切り替え

```python
from doc_ai_helper_backend.services.mcp.tools.git_tools import (
    configure_git_service, 
    get_unified_git_tools
)

# 複数サービス設定
configure_git_service("github", {"access_token": "github_token"})
configure_git_service("forgejo", {
    "base_url": "http://localhost:3000",
    "access_token": "forgejo_token"
})

# デフォルトサービス切り替え
unified_tools = get_unified_git_tools()
unified_tools.set_default_service("forgejo")

# コンテキストに基づく自動切り替え
github_context = {"service": "github", ...}
forgejo_context = {"service": "forgejo", ...}

# 同じ関数で異なるサービスを使用
await create_git_issue(..., repository_context=github_context)   # GitHub使用
await create_git_issue(..., repository_context=forgejo_context)  # Forgejo使用
```

### 2. 設定ベース切り替え

```bash
# 環境変数でデフォルト変更
export DEFAULT_GIT_SERVICE=forgejo

# または設定ファイル
DEFAULT_GIT_SERVICE=forgejo
FORGEJO_BASE_URL=http://localhost:3000
FORGEJO_TOKEN=your_token
```

## 🔒 セキュリティ考慮事項

### 1. アクセス制御

**リポジトリコンテキスト検証**
- 現在表示中のリポジトリでのみ操作可能
- 意図しないリポジトリへのアクセス防止
- クロスリポジトリ攻撃の防止

**認証情報管理**
- 環境変数での安全な管理
- トークンの最小権限原則
- 定期的なトークンローテーション

### 2. ネットワークセキュリティ

**HTTPS使用推奨**
```bash
# プロダクションではHTTPS使用
FORGEJO_BASE_URL=https://git.example.com
```

**ファイアウォール設定**
- 必要なポートのみ開放
- 内部ネットワークからのアクセス制限

### 3. 監査ログ

```python
# ログ出力例
logger.info(f"Creating issue in {repository} via {service_type}")
logger.info(f"Repository access validated for {repository}")
```

## 🚀 プロダクションデプロイ

### 1. 環境設定

```bash
# プロダクション環境変数
export FORGEJO_BASE_URL=https://git.company.com
export FORGEJO_TOKEN=${FORGEJO_SECRET_TOKEN}
export DEFAULT_GIT_SERVICE=forgejo

# Docker環境での設定
docker run -e FORGEJO_BASE_URL=https://git.company.com \
           -e FORGEJO_TOKEN=${TOKEN} \
           doc-ai-helper-backend
```

### 2. ヘルスチェック

```python
# ヘルスチェックエンドポイント追加例
@app.get("/health/forgejo")
async def forgejo_health():
    try:
        # Forgejo接続テスト
        adapter = MCPForgejoAdapter(
            base_url=config.forgejo_base_url,
            access_token=config.forgejo_token
        )
        # 軽量な接続テスト実行
        return {"status": "healthy", "service": "forgejo"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
```

### 3. モニタリング

```python
# メトリクス収集例
from prometheus_client import Counter, Histogram

forgejo_requests = Counter('forgejo_api_requests_total', 'Total Forgejo API requests')
forgejo_duration = Histogram('forgejo_api_duration_seconds', 'Forgejo API request duration')

# アダプター内でメトリクス記録
@forgejo_duration.time()
async def create_issue(self, ...):
    forgejo_requests.inc()
    # API処理
```

## 🔮 将来の拡張

### 1. 高度な機能

**バッチ処理**
```python
# 複数Issue一括作成
await create_multiple_issues([
    {"title": "Issue 1", "description": "..."},
    {"title": "Issue 2", "description": "..."},
], repository_context=forgejo_context)
```

**テンプレート機能**
```python
# Issueテンプレート
issue_template = {
    "title": "Bug Report: {component}",
    "description": "Bug in {component}\n\nSteps to reproduce:\n{steps}",
    "labels": ["bug", "{component}"]
}
```

### 2. 統合機能

**CI/CDパイプライン連携**
- Forgejo Actions との統合
- 自動PR作成とマージ
- ビルド結果の自動Issue作成

**Webhook処理**
- Forgejoイベントの受信
- 自動的なドキュメント更新
- リアルタイム通知

## 📚 参考資料

### 1. Forgejo関連

- [Forgejo公式サイト](https://forgejo.org/)
- [Forgejo API ドキュメント](https://forgejo.org/docs/latest/user/api-usage/)
- [Gitea API 仕様](https://try.gitea.io/api/swagger) (Forgejo互換)

### 2. 実装参考

- [FastMCP ドキュメント](https://github.com/phodal/fast-mcp)
- [httpx ドキュメント](https://www.python-httpx.org/)
- [Pydantic ドキュメント](https://docs.pydantic.dev/)

### 3. セキュリティ

- [OWASP API セキュリティ](https://owasp.org/www-project-api-security/)
- [Git セキュリティベストプラクティス](https://git-scm.com/docs/gitnamespaces)

## 🏁 まとめ

このガイドにより、doc_ai_helper_backendでForgejoを使用できるようになりました：

✅ **実装完了**
- Forgejoアダプター実装
- 統合MCPツール対応
- セキュリティ機能実装
- テストスクリプト提供

✅ **主要機能**  
- Issue/PR作成
- 権限確認
- GitHub/Forgejo切り替え
- エラーハンドリング

✅ **セキュリティ**
- リポジトリコンテキスト検証
- 認証情報の安全な管理
- アクセス制御

これで自己ホストGitサービスとしてForgejoを活用しながら、GitHub環境と同等のMCP機能を提供できます。
