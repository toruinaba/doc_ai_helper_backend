# E2E Testing for Document AI Helper Backend

このディレクトリには、Document AI Helper BackendのEnd-to-End（E2E）テストが含まれています。

## 新しいユーザーストーリーベースE2Eテスト

Document AI Helper Backendでは、従来のAPI/ワークフロー中心のE2Eテストから、真のユーザージャーニーベースのE2Eテストに移行しました。

### 新しいE2Eテスト構造

```
tests/e2e/
├── user_stories/           # ユーザーストーリーベースのテスト
│   ├── test_onboarding_journey.py
│   ├── test_document_exploration_journey.py
│   ├── test_ai_assisted_improvement_journey.py
│   └── test_team_collaboration_journey.py
├── helpers/                # ヘルパーモジュール
│   ├── frontend_simulator.py
│   ├── user_journey_tracker.py
│   └── story_assertions.py
├── fixtures/               # テストデータとフィクスチャ
│   ├── user_personas.json
│   ├── story_scenarios.json
│   └── sample_documents/
├── pytest.ini             # pytest設定
└── [従来のテスト]          # 既存のE2Eテスト（共存）
```

### ユーザーストーリーテスト実行

```bash
# 全てのユーザーストーリーテストを実行
pytest tests/e2e/user_stories/ -m e2e_user_story

# 特定のストーリータイプのみ実行
pytest tests/e2e/user_stories/ -m onboarding
pytest tests/e2e/user_stories/ -m document_exploration
pytest tests/e2e/user_stories/ -m ai_assistance
pytest tests/e2e/user_stories/ -m team_collaboration

# 詳細ログ付きで実行
pytest tests/e2e/user_stories/ -v --tb=short
```

詳細な実装内容については、本READMEの下部をご参照ください。

---

## 従来のE2Eテスト（既存）

### 概要

E2Eテストは以下の完全なワークフローを検証します：

1. **ドキュメント取得**: ForgejoリポジトリからAPIエンドポイント経由でドキュメントを取得
2. **LLM処理**: 取得したドキュメント内容をLLMで要約・分析
3. **MCPツール実行**: LLMの判断に基づいてForgejoにIssueを作成

### 前提条件

#### 1. バックエンドサーバー
- バックエンドAPIサーバーが別プロセスで動作している必要があります
- デフォルトURL: `http://localhost:8000`
- 環境変数 `BACKEND_API_URL` で変更可能

#### 2. Forgejoインスタンス
- アクセス可能なForgejoインスタンス
- テスト用リポジトリの存在
- 適切な認証情報（トークンまたはユーザー名/パスワード）

#### 3. 環境設定
`.env` ファイルに以下の設定が必要です：

```bash
# Forgejo設定
FORGEJO_BASE_URL=https://your-forgejo-instance.com
FORGEJO_TOKEN=your_access_token_here
# または
FORGEJO_USERNAME=your_username
FORGEJO_PASSWORD=your_password

# テスト用リポジトリ
TEST_FORGEJO_OWNER=test-owner
TEST_FORGEJO_REPO=test-repo

# LLM設定（オプション）
TEST_LLM_PROVIDER=mock  # または openai
TEST_LLM_MODEL=gpt-3.5-turbo

# その他
FORGEJO_VERIFY_SSL=true
DEBUG=true
```

### 従来のテスト実行方法

### 1. 基本実行
```bash
# E2Eテストを実行（--run-e2e フラグが必要）
pytest tests/e2e/ --run-e2e -v

# 特定のテストクラスのみ実行
pytest tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow --run-e2e -v

# 特定のテストメソッドのみ実行
pytest tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_basic_document_retrieval --run-e2e -v
```

### 2. 詳細ログ付き実行
```bash
# ログレベルを設定してデバッグ情報を表示
pytest tests/e2e/ --run-e2e -v -s --log-cli-level=INFO

# さらに詳細なデバッグ情報
pytest tests/e2e/ --run-e2e -v -s --log-cli-level=DEBUG
```

### 3. 特定のマーク付きテストのみ実行
```bash
# MCPツール関連テストのみ
pytest tests/e2e/ --run-e2e -v -m "mcp"

# LLM関連テストのみ  
pytest tests/e2e/ --run-e2e -v -m "llm"

# 低速テストを除外
pytest tests/e2e/ --run-e2e -v -m "not slow"
```

## テストの構成

### テストクラス

#### `TestForgejoE2EWorkflow`
基本的なE2Eワークフローテスト：
- `test_basic_document_retrieval`: 基本的なドキュメント取得
- `test_repository_structure_retrieval`: リポジトリ構造取得
- `test_llm_document_summarization`: LLMによるドキュメント要約
- `test_streaming_llm_response`: ストリーミングレスポンステスト
- `test_llm_with_mcp_issue_creation`: 🌟 **メインE2Eテスト** - 完全ワークフロー
- `test_multiple_document_analysis`: 複数ドキュメント分析
- `test_error_handling_*`: エラーハンドリング

#### `TestForgejoAdvancedWorkflows`
高度なワークフローテスト：
- `test_document_comparison_workflow`: ドキュメント比較ワークフロー

### ヘルパーモジュール

#### `helpers/api_client.py`
- `BackendAPIClient`: バックエンドAPIとの通信クライアント
- ドキュメント取得、LLMクエリ、ストリーミングレスポンス対応

#### `helpers/forgejo_client.py`
- `ForgejoVerificationClient`: Forgejo APIとの直接通信クライアント
- Issue確認、クリーンアップ機能

#### `helpers/test_data.py`
- `E2ETestData`: テストデータとプロンプトテンプレート管理
- 環境検証、設定管理

## テストの流れ

### メインE2Eテスト (`test_llm_with_mcp_issue_creation`)

```
1. 📄 ドキュメント取得
   ↓ GET /api/v1/documents/contents/forgejo/{owner}/{repo}/README.md
   
2. 🤖 LLM要約処理  
   ↓ POST /api/v1/llm/query (tools_enabled=false)
   
3. 🔧 MCPツール実行
   ↓ POST /api/v1/llm/query (tools_enabled=true)
   ↓ Function Calling: create_forgejo_issue
   
4. ✅ 結果検証
   ↓ Forgejo API直接確認
   ↓ Issue存在確認 & 内容検証
```

## 期待される結果

### 成功パターン
- ドキュメントが正常に取得される
- LLMが適切な要約を生成する
- MCPツールがIssueを作成する
- 作成されたIssueがForgejoで確認できる

### Mock LLMの場合
- ワークフローは完了するが、実際のIssue作成は行われない
- `{"mock": true, "status": "completed"}` が返される

### エラーハンドリング
- 存在しないリポジトリ/ファイルへのアクセス時に適切なエラー
- ネットワーク障害時の適切な例外処理

## トラブルシューティング

### よくある問題

#### 1. "Environment validation failed"
```bash
# 原因: 環境変数が設定されていない
# 解決: .env ファイルを確認・設定
```

#### 2. "Backend API server is not available"
```bash
# 原因: バックエンドサーバーが起動していない
# 解決: 別ターミナルでサーバーを起動
uvicorn doc_ai_helper_backend.main:app --reload
```

#### 3. "Forgejo instance is not accessible"
```bash
# 原因: Forgejo設定が間違っている
# 解決: FORGEJO_BASE_URL、認証情報を確認
```

#### 4. "Test repository does not exist"
```bash
# 原因: 指定されたテストリポジトリが存在しない
# 解決: TEST_FORGEJO_OWNER、TEST_FORGEJO_REPO を確認
```

### デバッグ方法

#### 1. 個別コンポーネントのテスト
```bash
# APIクライアントのみテスト
python -c "
import asyncio
from tests.e2e.helpers.api_client import BackendAPIClient

async def test():
    async with BackendAPIClient() as client:
        healthy = await client.health_check()
        print(f'Backend healthy: {healthy}')

asyncio.run(test())
"
```

#### 2. Forgejo接続のテスト
```bash
# Forgejoクライアントのみテスト
python -c "
import asyncio
from tests.e2e.helpers.forgejo_client import ForgejoVerificationClient
from tests.e2e.helpers.test_data import E2ETestData

async def test():
    config = E2ETestData.get_forgejo_config()
    async with ForgejoVerificationClient(
        config.base_url, config.token, 
        config.username, config.password
    ) as client:
        connected = await client.check_connection()
        print(f'Forgejo connected: {connected}')

asyncio.run(test())
"
```

## 継続的インテグレーション

CI/CDパイプラインでの実行例：

```yaml
# GitHub Actions例
- name: Run E2E Tests
  env:
    FORGEJO_BASE_URL: ${{ secrets.FORGEJO_BASE_URL }}
    FORGEJO_TOKEN: ${{ secrets.FORGEJO_TOKEN }}
    TEST_FORGEJO_OWNER: test-org
    TEST_FORGEJO_REPO: test-docs
  run: |
    # バックエンドサーバー起動
    uvicorn doc_ai_helper_backend.main:app --host 0.0.0.0 --port 8000 &
    sleep 10
    
    # E2Eテスト実行
    pytest tests/e2e/ --run-e2e -v --maxfail=1
```

## 注意事項

1. **実際のリソース作成**: テストは実際のForgejoインスタンスにIssueを作成します
2. **クリーンアップ**: テスト後に自動的にテスト用Issueをクローズします
3. **レート制限**: Forgejo APIのレート制限に注意してください
4. **認証情報**: 本番環境の認証情報を使用しないでください
5. **並列実行**: 複数テストの並列実行時はリソース競合に注意してください
