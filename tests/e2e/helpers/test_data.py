"""
Test data management for E2E tests.

This module provides test data configurations and utilities for E2E tests.
"""

import os
from typing import Dict, Any, List, Optional
from dataclasses import dataclass


@dataclass
class ForgejoTestConfig:
    """Configuration for Forgejo E2E tests."""

    base_url: str
    token: str = None
    username: str = None
    password: str = None
    verify_ssl: bool = True
    owner: str = "test-owner"
    repo: str = "test-repo"
    test_files: List[str] = None

    def __post_init__(self):
        if self.test_files is None:
            self.test_files = ["README.md", "docs/guide.md", "docs/api.md"]


class E2ETestData:
    """
    Test data and configuration management for E2E tests.
    """

    # Test markers for cleanup
    TEST_ISSUE_MARKER = "[E2E-TEST]"
    TEST_BRANCH_PREFIX = "e2e-test-"

    # Default test repository configuration
    DEFAULT_FORGEJO_CONFIG = ForgejoTestConfig(
        base_url=os.getenv("FORGEJO_BASE_URL", "https://git.example.com"),
        token=os.getenv("FORGEJO_TOKEN"),
        username=os.getenv("FORGEJO_USERNAME"),
        password=os.getenv("FORGEJO_PASSWORD"),
        verify_ssl=os.getenv("FORGEJO_VERIFY_SSL", "true").lower() == "true",
        owner=os.getenv("TEST_FORGEJO_OWNER", "test-owner"),
        repo=os.getenv("TEST_FORGEJO_REPO", "test-repo"),
    )

    # Backend API configuration
    BACKEND_API_URL = os.getenv("BACKEND_API_URL", "http://localhost:8000")

    # LLM configuration for tests
    TEST_LLM_PROVIDER = os.getenv("TEST_LLM_PROVIDER", "mock")
    TEST_LLM_MODEL = os.getenv("TEST_LLM_MODEL", "gpt-3.5-turbo")

    # Prompt templates for different scenarios
    PROMPT_TEMPLATES = {
        "document_summary": """
以下のドキュメント内容を要約してください：

タイトル: {title}
パス: {path}
内容:
{content}

要約は200文字以内で、主要なポイントを含めてください。
        """.strip(),
        "issue_creation_request": """
以下の要約をもとに、Issueを作成してください。必ずcreate_git_issue関数を使用してください。

要約: {summary}
リポジトリ: {owner}/{repo}

必須要件:
1. create_git_issue関数を呼び出すこと
2. title: "{marker} ドキュメント改善提案"
3. description: 詳細な改善提案内容
4. labels: ["documentation", "enhancement"]

create_git_issue関数を呼び出して実際にIssueを作成してください。
        """.strip(),
        "analysis_request": """
以下のドキュメントを分析し、品質評価と改善提案を行ってください：

{content}

分析結果として以下の項目を含めてください：
1. 構造の明確さ
2. 内容の完全性
3. 読みやすさ
4. 具体的な改善提案
        """.strip(),
    }

    # Expected document samples for testing
    SAMPLE_DOCUMENTS = {
        "README.md": {
            "expected_keywords": ["プロジェクト", "インストール", "使用方法"],
            "min_length": 100,
            "should_have_links": True,
        },
        "docs/guide.md": {
            "expected_keywords": ["ガイド", "手順", "説明"],
            "min_length": 200,
            "should_have_links": False,
        },
        "docs/api.md": {
            "expected_keywords": ["API", "エンドポイント", "リクエスト"],
            "min_length": 150,
            "should_have_links": True,
        },
    }

    # MCP Tool configurations
    MCP_TOOL_CONFIGS = {
        "github": {
            "create_issue": {
                "required_params": ["repository", "title", "description"],
                "optional_params": ["labels", "assignees"],
            }
        },
        "forgejo": {
            "create_issue": {
                "required_params": ["repository", "title", "description"],
                "optional_params": ["labels", "assignees"],
            }
        },
    }

    @classmethod
    def get_forgejo_config(cls) -> ForgejoTestConfig:
        """Get Forgejo configuration for tests."""
        return cls.DEFAULT_FORGEJO_CONFIG

    @classmethod
    def get_test_prompt(cls, template_name: str, **kwargs) -> str:
        """
        Get a formatted prompt template.

        Args:
            template_name: Name of the template
            **kwargs: Variables to substitute in the template

        Returns:
            Formatted prompt string
        """
        if template_name not in cls.PROMPT_TEMPLATES:
            raise ValueError(f"Unknown prompt template: {template_name}")

        template = cls.PROMPT_TEMPLATES[template_name]
        return template.format(**kwargs)

    @classmethod
    def get_sample_document_expectations(cls, filename: str) -> Dict[str, Any]:
        """
        Get expectations for a sample document.

        Args:
            filename: Document filename

        Returns:
            Dictionary of expectations
        """
        return cls.SAMPLE_DOCUMENTS.get(filename, {})

    @classmethod
    def validate_environment(cls) -> List[str]:
        """
        Validate that the environment is properly configured for E2E tests.

        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []

        config = cls.get_forgejo_config()

        # Check Forgejo configuration
        if not config.base_url or config.base_url == "https://git.example.com":
            errors.append("FORGEJO_BASE_URL must be set to a valid Forgejo instance")

        if not config.token and not (config.username and config.password):
            errors.append(
                "Either FORGEJO_TOKEN or FORGEJO_USERNAME/FORGEJO_PASSWORD must be set"
            )

        if not config.owner or config.owner == "test-owner":
            errors.append("TEST_FORGEJO_OWNER must be set to a valid owner")

        if not config.repo or config.repo == "test-repo":
            errors.append("TEST_FORGEJO_REPO must be set to a valid repository")

        return errors

    @classmethod
    def validate_environment_with_fallback(cls) -> tuple[bool, List[str]]:
        """
        Validate environment with fallback options for development.

        Returns:
            Tuple of (is_valid, warning_messages)
        """
        config = cls.get_forgejo_config()
        warnings = []

        # Critical errors that prevent testing
        critical_errors = []

        # Check if this looks like a development/demo setup
        is_demo_setup = (
            config.base_url == "https://git.example.com"
            or config.owner == "test-owner"
            or config.repo == "test-repo"
        )

        if is_demo_setup:
            warnings.append(
                "Using example/demo configuration - some tests may be skipped"
            )

        # Only require real configuration if not in demo mode
        if not is_demo_setup:
            if not config.base_url:
                critical_errors.append("FORGEJO_BASE_URL must be set")

            if not config.token and not (config.username and config.password):
                critical_errors.append("Forgejo authentication must be configured")

        return len(critical_errors) == 0, critical_errors + warnings

    @classmethod
    def create_test_issue_title(cls, description: str) -> str:
        """
        Create a test issue title with the test marker.

        Args:
            description: Brief description of the test

        Returns:
            Formatted issue title
        """
        return f"{cls.TEST_ISSUE_MARKER} {description}"

    @classmethod
    def create_test_issue_body(cls, content: str, test_id: Optional[str] = None) -> str:
        """
        Create a test issue body with the test marker.

        Args:
            content: Main content of the issue
            test_id: Optional test identifier

        Returns:
            Formatted issue body
        """
        body = f"{cls.TEST_ISSUE_MARKER}\n\n{content}"

        if test_id:
            body += f"\n\n---\nTest ID: {test_id}"

        body += f"\n\n*この Issue は E2E テストによって自動生成されました。*"

        return body
