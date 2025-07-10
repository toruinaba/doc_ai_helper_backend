"""
統合テスト用の設定ファイル
"""

import os
import pytest
from typing import Optional, Dict, Any, List
from doc_ai_helper_backend.core.config import settings


def pytest_configure(config):
    """統合テスト用の設定とマーカー登録"""
    # カスタムマーカーを登録
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "git: Git service integration tests")
    config.addinivalue_line("markers", "llm: LLM service integration tests")
    config.addinivalue_line("markers", "mcp: MCP (Model Context Protocol) tests")
    config.addinivalue_line("markers", "function_calling: Function calling tests")
    config.addinivalue_line("markers", "streaming: Streaming functionality tests")
    config.addinivalue_line("markers", "tools: MCP tools tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "github: Tests requiring GitHub API access")
    config.addinivalue_line("markers", "forgejo: Tests requiring Forgejo API access")
    config.addinivalue_line("markers", "openai: Tests requiring OpenAI API access")


@pytest.fixture(scope="session")
def openai_api_key() -> Optional[str]:
    """OpenAI APIキーのフィクスチャ"""
    api_key = settings.openai_api_key
    if not api_key:
        pytest.skip("OPENAI_API_KEY environment variable not set")
    return api_key


@pytest.fixture(scope="session")
def github_token() -> Optional[str]:
    """GitHub トークンのフィクスチャ"""
    token = settings.github_token
    if not token:
        pytest.skip("GITHUB_TOKEN environment variable not set")
    return token


@pytest.fixture(scope="session")
def forgejo_config() -> Optional[Dict[str, str]]:
    """Forgejo設定のフィクスチャ"""
    base_url = settings.forgejo_base_url
    access_token = settings.forgejo_token
    username = settings.forgejo_username
    password = settings.forgejo_password

    if not base_url:
        pytest.skip("FORGEJO_BASE_URL environment variable not set")

    if not (access_token or (username and password)):
        pytest.skip(
            "Either FORGEJO_TOKEN or FORGEJO_USERNAME/FORGEJO_PASSWORD must be set"
        )

    config = {"base_url": base_url}
    if access_token:
        config["access_token"] = access_token
    elif username and password:
        config["username"] = username
        config["password"] = password

    return config


@pytest.fixture(scope="session")
def test_repository_context() -> Dict[str, str]:
    """テスト用リポジトリコンテキスト"""
    return {
        "owner": "testowner",
        "repo": "testrepo",
        "ref": "main",
        "path": "README.md",
    }


@pytest.fixture
def sample_markdown_content() -> str:
    """サンプルMarkdownコンテンツ"""
    return """# テストドキュメント

これはテスト用のMarkdownドキュメントです。

## セクション1

サンプルテキストです。

### サブセクション

- リスト項目1
- リスト項目2
- リスト項目3

## セクション2

[リンクテキスト](https://example.com)

```python
# コードブロック
def hello():
    print("Hello, World!")
```

## まとめ

これでテストドキュメントは終了です。
"""


@pytest.fixture
def sample_conversation_history() -> List[Dict[str, str]]:
    """サンプル会話履歴"""
    return [
        {"role": "user", "content": "こんにちは"},
        {
            "role": "assistant",
            "content": "こんにちは！何かお手伝いできることはありますか？",
        },
        {"role": "user", "content": "Pythonについて教えてください"},
        {
            "role": "assistant",
            "content": "Pythonは高水準プログラミング言語です。読みやすい構文と豊富なライブラリが特徴です。",
        },
        {"role": "user", "content": "ありがとうございます"},
    ]


# 統合テスト用のスキップ条件
def skip_if_no_openai():
    """OpenAI APIキーがない場合はスキップ"""
    return pytest.mark.skipif(
        not settings.openai_api_key,
        reason="OPENAI_API_KEY environment variable not set",
    )


def skip_if_no_github():
    """GitHub トークンがない場合はスキップ"""
    return pytest.mark.skipif(
        not settings.github_token,
        reason="GITHUB_TOKEN environment variable not set",
    )


def skip_if_no_forgejo():
    """Forgejo設定がない場合はスキップ"""
    base_url = settings.forgejo_base_url
    access_token = settings.forgejo_token
    username = settings.forgejo_username
    password = settings.forgejo_password

    return pytest.mark.skipif(
        not base_url or not (access_token or (username and password)),
        reason="Forgejo configuration not complete",
    )
