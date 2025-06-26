"""
Secure GitHub integration tools for MCP server with repository context validation.

This module provides secure GitHub tools that validate repository access
against the current repository context to prevent unauthorized operations.
"""

import logging
from typing import Dict, Any, List, Optional
import json

from ...github.github_client import GitHubClient
from ...github.exceptions import (
    GitHubException,
    GitHubRepositoryNotFoundError,
    GitHubPermissionError,
)
from ....models.repository_context import RepositoryContext

logger = logging.getLogger(__name__)


class RepositoryAccessError(Exception):
    """Raised when trying to access a repository not in the current context."""

    pass


def _validate_repository_access(
    requested_repository: str, repository_context: Optional[RepositoryContext]
) -> None:
    """
    Validate that the requested repository matches the current context.

    Args:
        requested_repository: Repository in "owner/repo" format
        repository_context: Current repository context

    Raises:
        RepositoryAccessError: If repository access is not allowed
    """
    if not repository_context:
        # If no context provided, allow any repository (backward compatibility)
        logger.warning("No repository context provided, allowing unrestricted access")
        return

    current_repository = repository_context.repository_full_name

    if requested_repository != current_repository:
        raise RepositoryAccessError(
            f"Access denied: Requested repository '{requested_repository}' "
            f"does not match current context '{current_repository}'"
        )

    logger.info(f"Repository access validated: {requested_repository}")


async def create_github_issue(
    title: str,
    description: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    github_token: Optional[str] = None,
    repository_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    現在のリポジトリコンテキストに新しいGitHub Issueを作成します。

    Args:
        title: Issueのタイトル（簡潔で分かりやすい日本語で記述）
        description: Issueの詳細説明（問題の内容、再現手順、期待される結果などを日本語で記述）
        labels: 適用するラベル名のリスト（オプション）例：['バグ', '改善提案', 'ドキュメント']
        assignees: アサインするGitHubユーザー名のリスト（オプション）
        github_token: GitHub Personal Access Token（オプション、環境変数から自動取得）
        repository_context: 現在のリポジトリコンテキスト（自動注入）

    Returns:
        作成されたIssue情報（URLと番号を含む）のJSON文字列（日本語）
    """
    repo_ctx = None
    repository = "不明"

    try:
        # Parse repository context
        if repository_context:
            repo_ctx = RepositoryContext(**repository_context)

        if not repo_ctx:
            return json.dumps(
                {
                    "success": False,
                    "error": "リポジトリコンテキストが提供されていません。ドキュメントを表示していることを確認してください。",
                    "error_type": "context_required",
                },
                ensure_ascii=False,
                indent=2,
            )

        repository = repo_ctx.repository_full_name

        # Validate repository access (always passes for same repository)
        _validate_repository_access(repository, repo_ctx)

        # Initialize GitHub client
        client = GitHubClient(token=github_token)

        # Check repository permissions
        logger.info(f"Creating issue in context repository: {repository}")
        permissions = await client.check_repository_permissions(repository)

        if not permissions.get("issues", False):
            return json.dumps(
                {
                    "success": False,
                    "error": f"リポジトリ '{repository}' でIssue機能が無効になっています",
                    "error_type": "permission_error",
                },
                ensure_ascii=False,
                indent=2,
            )

        # Create the issue
        logger.info(f"Creating issue in {repository}: {title}")
        issue_data = await client.create_issue(
            repository=repository,
            title=title,
            body=description,
            labels=labels or [],
            assignees=assignees or [],
        )

        # Extract relevant information
        result = {
            "success": True,
            "message": f"Issue #{issue_data.get('number')} を正常に作成しました",
            "issue_info": {
                "number": issue_data.get("number"),
                "url": issue_data.get("html_url"),
                "api_url": issue_data.get("url"),
                "title": issue_data.get("title"),
                "body": issue_data.get("body"),
                "state": issue_data.get("state"),
                "labels": [label.get("name") for label in issue_data.get("labels", [])],
                "assignees": [
                    assignee.get("login")
                    for assignee in issue_data.get("assignees", [])
                ],
                "created_at": issue_data.get("created_at"),
                "repository": repository,
                "context_verified": True,
            },
        }

        logger.info(
            f"Successfully created issue #{issue_data.get('number')} in context repository {repository}"
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    except RepositoryAccessError as e:
        logger.error(f"Repository access denied: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "error_type": "access_denied",
            },
            ensure_ascii=False,
            indent=2,
        )

    except GitHubRepositoryNotFoundError as e:
        repo_name = repo_ctx.repository_full_name if repo_ctx else "不明"
        logger.error(f"Repository not found: {repo_name}")
        return json.dumps(
            {
                "success": False,
                "error": f"リポジトリが見つかりません: {repo_name}",
                "error_type": "repository_not_found",
            },
            ensure_ascii=False,
            indent=2,
        )

    except GitHubPermissionError as e:
        repo_name = repo_ctx.repository_full_name if repo_ctx else "不明"
        logger.error(f"Permission denied for repository: {repo_name}")
        return json.dumps(
            {
                "success": False,
                "error": f"リポジトリ '{repo_name}' へのアクセス権限がありません。アクセス権を確認してください。",
                "error_type": "permission_denied",
            },
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        logger.error(f"Unexpected error creating GitHub issue: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"予期しないエラー: {str(e)}",
                "error_type": "unexpected_error",
            },
            ensure_ascii=False,
            indent=2,
        )


async def create_github_pull_request(
    title: str,
    description: str,
    head_branch: str,
    base_branch: str = "main",
    github_token: Optional[str] = None,
    repository_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    現在のリポジトリコンテキストに新しいプルリクエストを作成します。

    Args:
        title: プルリクエストのタイトル（簡潔で分かりやすい日本語で記述）
        description: プルリクエストの詳細説明（変更内容、理由、テスト方法などを日本語で記述）
        head_branch: ソースブランチ名（変更がある側のブランチ）
        base_branch: ターゲットブランチ名（マージ先のブランチ、デフォルト: "main"）
        github_token: GitHub Personal Access Token（オプション、環境変数から自動取得）
        repository_context: 現在のリポジトリコンテキスト（自動注入）

    Returns:
        作成されたプルリクエスト情報（URLと番号を含む）のJSON文字列（日本語）
    """
    repo_ctx = None
    repository = "不明"

    try:
        # Parse repository context
        repo_ctx = None
        if repository_context:
            repo_ctx = RepositoryContext(**repository_context)

        if not repo_ctx:
            return json.dumps(
                {
                    "success": False,
                    "error": "リポジトリコンテキストが提供されていません。ドキュメントを表示していることを確認してください。",
                    "error_type": "context_required",
                },
                ensure_ascii=False,
                indent=2,
            )

        repository = repo_ctx.repository_full_name

        # Validate repository access (always passes for same repository)
        _validate_repository_access(repository, repo_ctx)

        # Initialize GitHub client
        client = GitHubClient(token=github_token)

        # Check repository permissions
        logger.info(f"Creating pull request in context repository: {repository}")
        permissions = await client.check_repository_permissions(repository)

        if not permissions.get("pull_requests", False):
            return json.dumps(
                {
                    "success": False,
                    "error": f"リポジトリ '{repository}' でPull Request機能が無効になっています",
                    "error_type": "permission_error",
                },
                ensure_ascii=False,
                indent=2,
            )

        # Create the pull request
        logger.info(f"Creating pull request in {repository}: {title}")
        pr_data = await client.create_pull_request(
            repository=repository,
            title=title,
            body=description,
            head_branch=head_branch,
            base_branch=base_branch,
        )

        # Extract relevant information
        result = {
            "success": True,
            "message": f"Pull Request #{pr_data.get('number')} を正常に作成しました",
            "pull_request": {
                "number": pr_data.get("number"),
                "url": pr_data.get("html_url"),
                "api_url": pr_data.get("url"),
                "title": pr_data.get("title"),
                "body": pr_data.get("body"),
                "state": pr_data.get("state"),
                "head": {
                    "branch": pr_data.get("head", {}).get("ref"),
                    "sha": pr_data.get("head", {}).get("sha"),
                },
                "base": {
                    "branch": pr_data.get("base", {}).get("ref"),
                    "sha": pr_data.get("base", {}).get("sha"),
                },
                "created_at": pr_data.get("created_at"),
                "repository": repository,
                "context_validated": True,
            },
        }

        logger.info(
            f"Successfully created pull request #{pr_data.get('number')} in context repository {repository}"
        )
        return json.dumps(result, indent=2)

    except RepositoryAccessError as e:
        logger.error(f"Repository access denied: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "error_type": "access_denied",
            }
        )

    except GitHubRepositoryNotFoundError as e:
        logger.error(f"Repository not found: {repository}")
        return json.dumps(
            {
                "success": False,
                "error": f"Repository not found: {repository}",
                "error_type": "repository_not_found",
            }
        )

    except GitHubPermissionError as e:
        logger.error(f"Permission denied for repository: {repository}")
        return json.dumps(
            {
                "success": False,
                "error": f"Permission denied for repository: {repository}. Check your access rights.",
                "error_type": "permission_denied",
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error creating GitHub pull request: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"予期しないエラー: {str(e)}",
                "error_type": "unexpected_error",
            },
            ensure_ascii=False,
            indent=2,
        )


async def check_github_repository_permissions(
    github_token: Optional[str] = None,
    repository_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    現在のリポジトリコンテキストの権限を確認します。

    Args:
        github_token: GitHub Personal Access Token（オプション、環境変数から自動取得）
        repository_context: 現在のリポジトリコンテキスト（自動注入）

    Returns:
        リポジトリ権限情報のJSON文字列（日本語）
    """
    try:
        # Parse repository context
        repo_ctx = None
        if repository_context:
            repo_ctx = RepositoryContext(**repository_context)

        if not repo_ctx:
            return json.dumps(
                {
                    "success": False,
                    "error": "No repository context provided. Please ensure you're viewing a document.",
                    "error_type": "context_required",
                }
            )

        repository = repo_ctx.repository_full_name

        # Validate repository access (always passes for same repository)
        _validate_repository_access(repository, repo_ctx)

        # Initialize GitHub client
        client = GitHubClient(token=github_token)

        # Check repository permissions
        logger.info(f"Checking permissions for context repository: {repository}")
        permissions = await client.check_repository_permissions(repository)

        # Extract relevant information
        result = {
            "success": True,
            "repository": repository,
            "permissions": permissions,
            "context_validated": True,
        }

        logger.info(
            f"Successfully retrieved permissions for context repository {repository}"
        )
        return json.dumps(result, indent=2)

    except RepositoryAccessError as e:
        logger.error(f"Repository access denied: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "error_type": "access_denied",
            },
            ensure_ascii=False,
            indent=2,
        )

    except GitHubRepositoryNotFoundError as e:
        logger.error(f"Repository not found: {repository}")
        return json.dumps(
            {
                "success": False,
                "error": f"リポジトリが見つかりません: {repository}",
                "error_type": "repository_not_found",
            },
            ensure_ascii=False,
            indent=2,
        )

    except GitHubPermissionError as e:
        logger.error(f"Permission denied for repository: {repository}")
        return json.dumps(
            {
                "success": False,
                "error": f"リポジトリ '{repository}' へのアクセス権限がありません。アクセス権を確認してください。",
                "error_type": "permission_denied",
            },
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        logger.error(f"Unexpected error creating GitHub pull request: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"予期しないエラー: {str(e)}",
                "error_type": "unexpected_error",
            },
            ensure_ascii=False,
            indent=2,
        )


async def check_github_repository_permissions(
    github_token: Optional[str] = None,
    repository_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    現在のリポジトリコンテキストの権限を確認します。

    Args:
        github_token: GitHub Personal Access Token（オプション、環境変数から自動取得）
        repository_context: 現在のリポジトリコンテキスト（自動注入）

    Returns:
        リポジトリ権限情報のJSON文字列（日本語）
    """
    repo_ctx = None
    repository = "不明"

    try:
        # Parse repository context
        if repository_context:
            repo_ctx = RepositoryContext(**repository_context)

        if not repo_ctx:
            return json.dumps(
                {
                    "success": False,
                    "error": "リポジトリコンテキストが提供されていません。ドキュメントを表示していることを確認してください。",
                    "error_type": "context_required",
                },
                ensure_ascii=False,
                indent=2,
            )

        repository = repo_ctx.repository_full_name

        # Validate repository access (always passes for same repository)
        _validate_repository_access(repository, repo_ctx)

        # Initialize GitHub client
        client = GitHubClient(token=github_token)

        # Check repository permissions
        logger.info(f"Checking permissions for context repository: {repository}")
        permissions = await client.check_repository_permissions(repository)

        # Extract relevant information
        result = {
            "success": True,
            "message": f"リポジトリ '{repository}' の権限を正常に取得しました",
            "repository": repository,
            "permissions": permissions,
            "context_validated": True,
        }

        logger.info(
            f"Successfully retrieved permissions for context repository {repository}"
        )
        return json.dumps(result, ensure_ascii=False, indent=2)

    except RepositoryAccessError as e:
        logger.error(f"Repository access denied: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": str(e),
                "error_type": "access_denied",
            },
            ensure_ascii=False,
            indent=2,
        )

    except GitHubRepositoryNotFoundError as e:
        logger.error(f"Repository not found: {repository}")
        return json.dumps(
            {
                "success": False,
                "error": f"リポジトリが見つかりません: {repository}",
                "error_type": "repository_not_found",
            },
            ensure_ascii=False,
            indent=2,
        )

    except GitHubPermissionError as e:
        logger.error(f"Permission denied for repository: {repository}")
        return json.dumps(
            {
                "success": False,
                "error": f"リポジトリ '{repository}' へのアクセス権限がありません。アクセス権を確認してください。",
                "error_type": "permission_denied",
            },
            ensure_ascii=False,
            indent=2,
        )

    except Exception as e:
        logger.error(
            f"Unexpected error checking GitHub repository permissions: {str(e)}"
        )
        return json.dumps(
            {
                "success": False,
                "error": f"予期しないエラー: {str(e)}",
                "error_type": "unexpected_error",
            },
            ensure_ascii=False,
            indent=2,
        )
