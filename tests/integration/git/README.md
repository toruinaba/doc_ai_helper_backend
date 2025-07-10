# Git統合テスト

Git層の統合テストを実行するには、以下の環境変数の設定が必要です：

## GitHub統合テスト

1. **GITHUB_TOKEN**: GitHub APIにアクセスするためのトークン

```powershell
# GitHubトークンの設定
$env:GITHUB_TOKEN = "your_github_token"
```

## Forgejo統合テスト

1. **FORGEJO_BASE_URL**: ForgejoインスタンスのベースURL
2. **FORGEJO_TOKEN**: Forgejoアクセストークン（推奨）
   または
   **FORGEJO_USERNAME** + **FORGEJO_PASSWORD**: ユーザー名とパスワード
3. **FORGEJO_TEST_OWNER**: テスト用リポジトリのオーナー（オプション、デフォルト: testowner）
4. **FORGEJO_TEST_REPO**: テスト用リポジトリ名（オプション、デフォルト: testrepo）

```powershell
# Forgejoトークン認証の場合
$env:FORGEJO_BASE_URL = "https://your-forgejo-instance.com"
$env:FORGEJO_TOKEN = "your_forgejo_token"

# または、基本認証の場合
$env:FORGEJO_BASE_URL = "https://your-forgejo-instance.com"
$env:FORGEJO_USERNAME = "your_username"
$env:FORGEJO_PASSWORD = "your_password"

# テスト用リポジトリの設定（オプション）
$env:FORGEJO_TEST_OWNER = "your_test_owner"
$env:FORGEJO_TEST_REPO = "your_test_repo"
```

## テスト実行方法

### Git層統合テスト全体の実行

```powershell
pytest tests/integration/git/ -v
```

### GitHub統合テストのみ実行

```powershell
pytest tests/integration/git/test_github_integration.py -v
pytest tests/integration/git/test_github_service.py -v
```

### Forgejo統合テストのみ実行

```powershell
pytest tests/integration/git/test_forgejo_integration.py -v
```

### マーカー別実行

```powershell
# GitHub関連テスト
pytest -m github -v

# Forgejo関連テスト
pytest -m forgejo -v

# Git層全体
pytest -m git -v
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
