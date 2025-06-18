# github_serviceの統合テスト

統合テストを実行するには、以下の環境変数の設定が必要です：

1. **GITHUB_TOKEN**: GitHub APIにアクセスするためのトークン
2. **TEST_MODE**: テストモード（実際のAPIを使用する場合は `live`、モックを使用する場合は `mock`）

PowerShellでの環境変数設定例:

```powershell
# GitHubトークンの設定
$env:GITHUB_TOKEN = "your_github_token"

# テストモードの設定（live または mock）
$env:TEST_MODE = "live"
```

## テスト実行方法

### すべてのテストの実行

```powershell
python -m pytest
```

### 単体テストのみ実行

```powershell
python -m pytest tests/unit/
```

### 統合テストのみ実行

```powershell
python -m pytest tests/integration/
```

### 特定のテストファイルの実行

```powershell
python -m pytest tests/unit/services/git/test_github_service.py
```

### warningを無視してテスト実行

```powershell
python -m pytest -W ignore
```

## GitHubサービステストの実行

GitHubサービスの単体テストは、内部で`_make_request`メソッドをモックしているため、実際のGitHub APIを呼び出すことなく実行できます：

```powershell
python -m pytest tests/unit/services/git/test_github_service.py -v
```

GitHubサービスの統合テストは、実際のGitHub APIを呼び出すため、有効なGitHubトークンが必要です：

```powershell
# 環境変数設定
$env:GITHUB_TOKEN = "your_github_token"
$env:TEST_MODE = "live"

# テスト実行
python -m pytest tests/integration/test_github_service.py -v
```

## LLMサービステストの実行

LLMサービスのテストには、以下の環境変数が必要です：

1. **OPENAI_API_KEY**: OpenAI APIキー
2. **TEST_MODE**: テストモード（デフォルトは `mock`）

```powershell
# 環境変数設定
$env:OPENAI_API_KEY = "your_openai_api_key"
$env:TEST_MODE = "live"

# テスト実行
python -m pytest tests/unit/services/llm/test_openai_service.py -v
```

## テストレポートの生成

テスト実行結果のレポートを生成するには：

```powershell
python -m pytest --html=report.html
```

## デバッグモードでのテスト実行

詳細なログを表示してテストを実行するには：

```powershell
python -m pytest -v --log-cli-level=DEBUG
```

## 注意事項

1. 統合テストは実際のAPIを呼び出すため、レート制限や利用コストに注意してください
2. トークンやAPIキーなどの秘密情報はバージョン管理システムにコミットしないでください
3. CI/CD環境ではシークレット管理機能を使用して環境変数を設定してください
