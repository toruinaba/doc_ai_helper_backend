# テスト実行ガイド

このドキュメントでは、doc_ai_helper_backendプロジェクトでのテスト実行方法について説明します。

## テスト戦略の概要

### ユニットテスト（Unit Tests）
- **場所**: `tests/unit/`
- **特徴**: 外部依存なし、高速実行（<30秒）
- **用途**: 日常開発での継続的なテスト実行

### 統合テスト（Integration Tests）
- **場所**: `tests/integration/`
- **特徴**: 実際の外部API使用、環境変数必須
- **用途**: 本番前検証、CI/CDでの品質確認

## 日常開発でのテスト実行

### 基本的なユニットテスト実行

```bash
# すべてのユニットテストを実行（推奨）
pytest tests/unit/ -v

# 特定のモジュールのテスト
pytest tests/unit/api/ -v
pytest tests/unit/services/llm/ -v
pytest tests/unit/document_processors/ -v

# カバレッジ付きでテスト実行
pytest tests/unit/ --cov=doc_ai_helper_backend --cov-report=html
```

### 特定機能のテスト実行

```bash
# LLM関連のテストのみ
pytest tests/unit/ -k "llm" -v

# ドキュメント処理のテストのみ
pytest tests/unit/ -k "document" -v

# APIエンドポイントのテストのみ
pytest tests/unit/api/ -v

# エラーハンドリングのテストのみ
pytest tests/unit/ -k "error" -v
```

### パフォーマンステスト実行

```bash
# パフォーマンステストのみ
pytest tests/unit/api/test_performance.py -v

# ベンチマーク結果の詳細表示
pytest tests/unit/api/test_performance.py --benchmark-only --benchmark-verbose
```

## 本番前検証での統合テスト実行

### 環境変数の設定

統合テストを実行する前に、必要な環境変数を設定してください：

```bash
# OpenAI APIキー（LLMサービステスト用）
export OPENAI_API_KEY="your-openai-api-key"

# GitHub トークン（Gitサービステスト用）
export GITHUB_TOKEN="your-github-token"

# Anthropic APIキー（将来の拡張用）
export ANTHROPIC_API_KEY="your-anthropic-api-key"

# モデル指定（オプション）
export OPENAI_MODEL="gpt-3.5-turbo"
```

### 統合テスト実行

```bash
# 統合テストのみ実行
pytest tests/integration/ -v

# タイムアウト付きで実行
pytest tests/integration/ -v --timeout=300

# 特定のサービスの統合テスト
pytest tests/integration/llm/ -v
pytest tests/integration/git/ -v
```

### 全テスト実行

```bash
# ユニットテスト + 統合テスト
pytest tests/ -v

# カバレッジ付きで全テスト
pytest tests/ --cov=doc_ai_helper_backend --cov-report=html --cov-report=xml
```

## テスト結果の解釈

### 成功時の出力例

```
tests/unit/api/test_llm.py::TestLLMAPI::test_query_basic ✓
tests/unit/api/test_llm.py::TestLLMAPI::test_query_with_context ✓
tests/unit/services/llm/test_mock_service.py::TestMockLLMService::test_basic_query ✓

========================== 15 passed in 2.34s ==========================
```

### 失敗時の対応

```
tests/unit/api/test_llm.py::TestLLMAPI::test_query_basic FAILED

======================= FAILURES =======================
_______ TestLLMAPI.test_query_basic _______

    def test_query_basic(self):
        # テスト内容...
>       assert response.status_code == 200
E       assert 500 == 200

tests/unit/api/test_llm.py:42: AssertionError
```

**対応手順**:
1. エラーメッセージを確認
2. 関連するコードを調査
3. 必要に応じてデバッグ実行：`pytest tests/unit/api/test_llm.py::TestLLMAPI::test_query_basic -v -s`

## テスト環境の設定

### 依存関係のインストール

```bash
# 基本の依存関係
pip install -r requirements.txt

# テスト用の依存関係
pip install pytest pytest-asyncio pytest-cov pytest-mock pytest-benchmark
```

### 開発環境の設定確認

```bash
# Python環境の確認
python --version

# インストール済みパッケージの確認
pip list | grep pytest

# プロジェクト構造の確認
pytest --collect-only tests/unit/
```

## CI/CDでのテスト実行

### GitHub Actions

プロジェクトでは以下のGitHub Actionsワークフローが設定されています：

1. **ユニットテスト** (常時実行)
   - 全てのPRで自動実行
   - Python 3.9, 3.10, 3.11での検証
   - カバレッジレポート生成

2. **統合テスト** (条件付き実行)
   - mainブランチへのマージ時
   - `integration-test`ラベル付きのPR
   - 定期実行（スケジュール）

3. **パフォーマンステスト** (mainブランチのみ)
   - mainブランチへのマージ時のみ実行

### 統合テストの手動トリガー

プルリクエストで統合テストを実行したい場合：

1. PRに `integration-test` ラベルを追加
2. CI/CDが統合テストを実行
3. 結果をPRのチェックで確認

## トラブルシューティング

### よくある問題と解決方法

#### 1. 統合テストがスキップされる

**問題**: 統合テストが環境変数不足でスキップされる

**解決**: 必要な環境変数を設定
```bash
export OPENAI_API_KEY="your-key"
export GITHUB_TOKEN="your-token"
```

#### 2. テストが遅い

**問題**: ユニットテストの実行が遅い

**対応**:
- 特定のテストファイルのみ実行
- `-x` オプションで最初の失敗で停止
- `--lf` オプションで前回失敗したテストのみ実行

```bash
pytest tests/unit/ -x --lf
```

#### 3. カバレッジが低い

**問題**: コードカバレッジが期待値を下回る

**対応**:
- カバレッジレポートを確認: `pytest tests/unit/ --cov-report=html`
- `htmlcov/index.html` でどの行がテストされていないか確認
- 不足している部分のテストを追加

#### 4. Mockサービスが動作しない

**問題**: MockLLMServiceが期待通りに動作しない

**対応**:
- `TEST_MODE=mock` 環境変数を確認
- Mockサービスのログを確認
- ファクトリーパターンの設定を確認

```bash
export TEST_MODE=mock
pytest tests/unit/services/llm/test_mock_service.py -v -s
```

## ベストプラクティス

### テスト作成時の注意点

1. **ユニットテストでの外部依存排除**
   - 実際のAPIやデータベースに依存しない
   - `pytest-mock` や `unittest.mock` を積極使用
   - 環境変数に依存しない設計

2. **テストの独立性確保**
   - テスト間で状態を共有しない
   - フィクスチャで適切なセットアップ・クリーンアップ
   - テスト順序に依存しない設計

3. **明確なテスト名とドキュメント**
   - テスト名から何をテストしているか明確に
   - 複雑なテストには適切なコメント
   - エラーメッセージから問題が特定しやすく

### パフォーマンス考慮事項

1. **高速なフィードバックループ**
   - ユニットテストは30秒以内で完了
   - 並列実行の活用: `pytest -n auto`
   - キャッシュの活用

2. **効率的なテスト実行**
   - 開発中は関連するテストのみ実行
   - CI/CDでは全テスト実行
   - 失敗時の早期停止

## 参考資料

- [pytest公式ドキュメント](https://docs.pytest.org/)
- [FastAPIテストガイド](https://fastapi.tiangolo.com/tutorial/testing/)
- [Python mock ライブラリ](https://docs.python.org/3/library/unittest.mock.html)
- [プロジェクトのCopilot Instructions](.github/copilot-instructions.md)
