"""
統合テスト用の設定ファイル
"""

import os
import pytest
from typing import Optional, Dict, Any


def pytest_configure(config):
    """統合テストの設定"""
    # カスタムマーカーを登録
    config.addinivalue_line("markers", "integration: integration tests")
    config.addinivalue_line("markers", "mcp: MCP (Model Context Protocol) tests")
    config.addinivalue_line("markers", "function_calling: Function calling tests")
    config.addinivalue_line("markers", "tools: MCP tools tests")
    config.addinivalue_line("markers", "e2e: End-to-end scenario tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "github: Tests requiring GitHub API access")

    # 必要な環境変数をチェック
    required_env_vars = {
        "OPENAI_API_KEY": "OpenAI API integration tests",
        "GITHUB_TOKEN": "GitHub API integration tests",
    }

    missing_vars = []
    for var, description in required_env_vars.items():
        if not os.getenv(var):
            missing_vars.append(f"{var} (for {description})")

    if missing_vars:
        # 環境変数が不足している場合はテストをスキップ
        pytest.skip(
            f"Integration tests skipped. Missing environment variables: {', '.join(missing_vars)}",
            allow_module_level=True,
        )


@pytest.fixture(scope="session")
def openai_api_key() -> Optional[str]:
    """OpenAI APIキーのフィクスチャ"""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        pytest.skip("OPENAI_API_KEY environment variable not set")
    return api_key


@pytest.fixture(scope="session")
def github_token() -> Optional[str]:
    """GitHub トークンのフィクスチャ"""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN environment variable not set")
    return token


@pytest.fixture(scope="session")
def anthropic_api_key() -> Optional[str]:
    """Anthropic APIキーのフィクスチャ（将来の拡張用）"""
    return os.getenv("ANTHROPIC_API_KEY")


@pytest.fixture(scope="session")
def integration_test_config() -> Dict[str, Any]:
    """統合テスト用設定"""
    return {
        "timeout": int(os.getenv("INTEGRATION_TEST_TIMEOUT", "30")),
        "retry_count": int(os.getenv("INTEGRATION_TEST_RETRY", "3")),
        "test_repository": os.getenv("TEST_REPOSITORY", "octocat/Hello-World"),
        "test_branch": os.getenv("TEST_BRANCH", "master"),
        "openai_model": os.getenv("OPENAI_MODEL", "gpt-3.5-turbo"),
        "openai_base_url": os.getenv("OPENAI_BASE_URL"),
    }


@pytest.fixture(scope="session")
def integration_test_limits() -> Dict[str, int]:
    """統合テストのリソース制限"""
    return {
        "max_requests_per_minute": int(os.getenv("MAX_REQUESTS_PER_MINUTE", "10")),
        "max_tokens_per_request": int(os.getenv("MAX_TOKENS_PER_REQUEST", "4000")),
        "max_test_duration_seconds": int(os.getenv("MAX_TEST_DURATION", "300")),
    }


@pytest.fixture
def rate_limiter():
    """レート制限のためのフィクスチャ"""
    import time

    class RateLimiter:
        def __init__(self, max_calls_per_minute: int = 10):
            self.max_calls = max_calls_per_minute
            self.calls = []

        def wait_if_needed(self):
            """必要に応じて待機"""
            now = time.time()
            # 1分以内の呼び出しを計算
            self.calls = [call_time for call_time in self.calls if now - call_time < 60]

            if len(self.calls) >= self.max_calls:
                # レート制限に達している場合は待機
                wait_time = 60 - (now - self.calls[0])
                if wait_time > 0:
                    time.sleep(wait_time)
                    self.calls = []

            self.calls.append(now)

    return RateLimiter()


@pytest.fixture(autouse=True)
def cleanup_after_test():
    """テスト後のクリーンアップ"""
    yield
    # テスト後に実行される処理
    # 必要に応じてキャッシュクリア、一時ファイル削除など
    pass


# マーカーの定義
def pytest_configure(config):
    """カスタムpytestマーカーの設定"""
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line(
        "markers", "external_api: mark test as requiring external API access"
    )
    config.addinivalue_line(
        "markers", "expensive: mark test as expensive (high API usage)"
    )


# テスト実行前の検証
def pytest_runtest_setup(item):
    """テスト実行前のセットアップ検証"""
    # expensive マーカーが付いているテストの場合
    if "expensive" in item.keywords:
        if os.getenv("RUN_EXPENSIVE_TESTS") != "true":
            pytest.skip(
                "Expensive tests disabled. Set RUN_EXPENSIVE_TESTS=true to enable."
            )

    # external_api マーカーが付いているテストの場合
    if "external_api" in item.keywords:
        if os.getenv("SKIP_EXTERNAL_API_TESTS") == "true":
            pytest.skip("External API tests disabled.")


# テスト結果の集計
def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """テスト結果のサマリー表示"""
    if hasattr(terminalreporter, "stats"):
        skipped = len(terminalreporter.stats.get("skipped", []))
        if skipped > 0:
            terminalreporter.write_line(
                f"\n⚠️  {skipped} tests were skipped (likely due to missing environment variables)"
            )
            terminalreporter.write_line(
                "To run all integration tests, ensure the following environment variables are set:"
            )
            terminalreporter.write_line("  - OPENAI_API_KEY")
            terminalreporter.write_line("  - GITHUB_TOKEN")
            terminalreporter.write_line("  - ANTHROPIC_API_KEY (optional)")
