# OpenAIService 統合テストの実行方法

このドキュメントでは、OpenAIServiceの統合テストの実行方法について説明します。

## 前提条件

- Python 3.9以上
- pytestとpytest-asyncioがインストールされていること
- OpenAI APIキー（実際のAPIテスト用）

## テスト実行モード

OpenAIServiceの統合テストは、2つのモードで実行できます：

1. **モックモード**: 実際のOpenAI APIを呼び出さずにテストを実行します。このモードはAPI呼び出しのコストがかからず、CI/CDパイプラインでの定期的なテストに適しています。
2. **ライブモード**: 実際のOpenAI APIを呼び出してテストを実行します。このモードは、OpenAI APIとの実際の統合を確認するために使用します。

## 環境変数の設定

テストを実行する前に、以下の環境変数を設定します：

- `TEST_MODE`: テストモードを指定します。`mock`または`live`を設定します。
- `OPENAI_API_KEY`: ライブモードでテストを実行する場合に必要なOpenAI APIキーを設定します。
- `OPENAI_BASE_URL`: （オプション）カスタムベースURL（LiteLLMなどのプロキシサーバー）を使用する場合に設定します。
- `OPENAI_MODEL`: （オプション）使用するモデル名を指定します。デフォルトは`gpt-3.5-turbo`です。

### Windows PowerShellでの環境変数設定

```powershell
# モックモードでテストを実行
$env:TEST_MODE = "mock"

# ライブモードでテストを実行（APIキーが必要）
$env:TEST_MODE = "live"
$env:OPENAI_API_KEY = "your-api-key-here"

# LiteLLMなどのプロキシサーバーを使用
$env:OPENAI_BASE_URL = "http://localhost:8000/v1"  # LiteLLMのデフォルトエンドポイント

# カスタムモデルを使用
$env:OPENAI_MODEL = "claude-3-opus-20240229"  # LiteLLMプロキシ経由でAnthropicモデルを使用する例
```

## テストの実行

### 特定の統合テストのみを実行

```powershell
# プロジェクトのルートディレクトリから実行
pytest tests/integration/test_openai_service.py -v
```

### 特定のテストケースのみを実行

```powershell
# 例: 基本的なクエリのテストのみ実行
pytest tests/integration/test_openai_service.py::TestOpenAIServiceIntegration::test_basic_query -v
```

### すべての統合テストを実行

```powershell
pytest tests/integration/ -v
```

## テスト結果の確認

テスト実行後、pytest は以下のような結果を表示します：

```
============================= test session starts =============================
...
collected 6 items

tests/integration/test_openai_service.py::TestOpenAIServiceIntegration::test_basic_query PASSED
tests/integration/test_openai_service.py::TestOpenAIServiceIntegration::test_query_with_system_instruction PASSED
tests/integration/test_openai_service.py::TestOpenAIServiceIntegration::test_caching PASSED
tests/integration/test_openai_service.py::TestOpenAIServiceIntegration::test_capabilities PASSED
tests/integration/test_openai_service.py::TestOpenAIServiceIntegration::test_error_handling PASSED
tests/integration/test_openai_service.py::TestOpenAIServiceIntegration::test_token_estimation PASSED

============================= 6 passed in 5.67s ==============================
```

## CI/CDでの使用

CI/CDパイプラインでは、コストを抑えるためにモックモードでテストを実行することをお勧めします：

```yaml
# .github/workflows/test.yml の例
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.10'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
          pip install pytest pytest-asyncio
      - name: Run integration tests with mock
        run: |
          export TEST_MODE=mock
          pytest tests/integration/
```

定期的に（例: 週に1回）ライブモードでのテストを実行するスケジュールされたワークフローを設定することも検討してください。その場合は、APIキーをGitHubのSecretsとして設定します。

## トラブルシューティング

### テストがスキップされる

一部のテストが `pytest.skip` でスキップされる場合があります：

1. **APIキーが設定されていない**: ライブモードでテストを実行する場合は、`OPENAI_API_KEY` 環境変数を設定してください。
2. **特定の機能がサービスに実装されていない**: 例えば、`test_token_estimation` は `estimate_tokens` メソッドがサービスに実装されている場合のみ実行されます。
3. **カスタムベースURLのテスト**: `test_custom_base_url` は `OPENAI_BASE_URL` が設定されている場合のみ実行されます。

### テストが失敗する

1. **API制限**: ライブモードで大量のテストを実行すると、OpenAI APIの制限に達する可能性があります。その場合は、テスト間に遅延を追加するか、モックモードでテストを実行してください。
2. **不正な設定**: 環境変数やAPIキーが正しく設定されていることを確認してください。
3. **LiteLLMの接続エラー**: カスタムベースURLを使用している場合、LiteLLMサーバーが実行中であり、正しいURLを設定していることを確認してください。
4. **モデル名の不一致**: LiteLLMを使用する場合、指定したモデル名がLiteLLMの設定と一致していることを確認してください。モデル名の不一致はエラーの原因となります。
5. **非対応モデル**: 指定したモデルがLiteLLMの設定で対応していない場合、エラーが発生します。その場合は、`OPENAI_MODEL`環境変数で対応モデルを指定してください。
