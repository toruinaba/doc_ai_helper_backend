# E2Eテスト クイックスタートガイド

## 🚀 すぐに始める方法

### 1. デモ/モック環境での実行

実際のForgejoインスタンスがない場合、デモ設定でバックエンドAPIとLLMの動作を確認できます：

```bash
# .env にデモ設定
BACKEND_API_URL=http://localhost:8000
TEST_LLM_PROVIDER=mock

# バックエンドサーバー起動
uvicorn doc_ai_helper_backend.main:app --reload

# E2Eテスト実行（Forgejoテストはスキップされる）
pytest tests/e2e/ --run-e2e -v
```

### 2. 実際のForgejo環境での実行

実際のForgejoインスタンスとリポジトリを使用する場合：

```bash
# .env に実際の設定
FORGEJO_BASE_URL=https://your-forgejo-instance.com
FORGEJO_TOKEN=your_access_token
TEST_FORGEJO_OWNER=your-username
TEST_FORGEJO_REPO=your-test-repo

BACKEND_API_URL=http://localhost:8000
TEST_LLM_PROVIDER=openai  # または mock
OPENAI_API_KEY=your_openai_key  # LLMプロバイダーがopenaiの場合

# バックエンドサーバー起動
uvicorn doc_ai_helper_backend.main:app --reload

# 完全なE2Eテスト実行
pytest tests/e2e/ --run-e2e -v
```

## 📋 環境変数の説明

### 必須設定

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `BACKEND_API_URL` | バックエンドAPIのURL | `http://localhost:8000` |

### Forgejo関連（実際のForgejoテスト時）

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `FORGEJO_BASE_URL` | ForgejoインスタンスのURL | `https://git.yourcompany.com` |
| `FORGEJO_TOKEN` | Forgejoアクセストークン | `your_access_token` |
| `TEST_FORGEJO_OWNER` | テスト用リポジトリのオーナー | `your-username` |
| `TEST_FORGEJO_REPO` | テスト用リポジトリ名 | `test-docs` |

### LLM関連（オプション）

| 変数名 | 説明 | 例 |
|--------|------|-----|
| `TEST_LLM_PROVIDER` | テスト用LLMプロバイダー | `mock` / `openai` |
| `OPENAI_API_KEY` | OpenAI APIキー | `sk-...` |

## 🎯 テストのスキップパターン

### 自動スキップされるケース

1. **デモ設定の場合** - Forgejoテストをスキップし、バックエンドAPIテストのみ実行
2. **バックエンドサーバー未起動** - 全テストをスキップ
3. **Forgejo接続失敗** - Forgejo関連テストをスキップ
4. **テストリポジトリ未存在** - リポジトリアクセステストをスキップ

### スキップメッセージの例

```
SKIPPED - Skipping Forgejo tests - demo/example configuration detected
SKIPPED - Backend API server is not available  
SKIPPED - Forgejo instance at https://git.example.com is not accessible
SKIPPED - Test repository test-owner/test-repo does not exist
```

## 🔧 トラブルシューティング

### Q: 「Environment validation failed」エラーが出る

**A:** `.env`ファイルに必要な設定がない、またはデフォルト値のままです。

```bash
# 最小設定例
BACKEND_API_URL=http://localhost:8000
TEST_LLM_PROVIDER=mock

# バックエンドサーバーを起動してから再実行
```

### Q: 「Backend API server is not available」

**A:** バックエンドサーバーが起動していません。

```bash
# 別ターミナルでサーバー起動
uvicorn doc_ai_helper_backend.main:app --reload

# または自動起動スクリプト使用
python scripts/run_e2e_tests.py --start-server
```

### Q: Forgejoテストが全てスキップされる

**A:** 正常です。実際のForgejoインスタンスがない場合の期待動作です。

バックエンドAPIとLLMの機能は引き続きテストされます。

## 📊 実行結果の例

### デモ設定での実行結果
```
tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_basic_document_retrieval SKIPPED
tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_llm_document_summarization PASSED
tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_streaming_llm_response PASSED

=== 2 passed, 1 skipped in 3.45s ===
```

### 完全設定での実行結果
```
tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_basic_document_retrieval PASSED
tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_llm_document_summarization PASSED
tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_llm_with_mcp_issue_creation PASSED
tests/e2e/test_forgejo_e2e_workflow.py::TestForgejoE2EWorkflow::test_streaming_llm_response PASSED

=== 4 passed in 12.34s ===
```
