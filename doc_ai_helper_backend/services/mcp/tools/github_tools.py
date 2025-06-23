"""
GitHub integration tools for MCP server.

This module provides tools for GitHub operations including issue creation,
pull request creation, and repository management.
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

logger = logging.getLogger(__name__)


async def create_github_issue(
    repository: str,
    title: str,
    description: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    github_token: Optional[str] = None,
) -> str:
    """
    Create a new issue in a GitHub repository.

    Args:
        repository: Repository in "owner/repo" format
        title: Issue title
        description: Issue description/body
        labels: List of label names to apply (optional)
        assignees: List of GitHub usernames to assign (optional)
        github_token: GitHub Personal Access Token (optional, uses env var if not provided)

    Returns:
        JSON string containing the created issue information including URL and number
    """
    try:
        # Validate repository format first
        if "/" not in repository:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Invalid repository format: {repository}. Expected 'owner/repo'",
                    "error_type": "validation_error",
                }
            )

        # Initialize GitHub client
        client = GitHubClient(token=github_token)

        # Check repository permissions
        logger.info(f"Checking permissions for repository: {repository}")
        permissions = await client.check_repository_permissions(repository)

        if not permissions.get("issues", False):
            return json.dumps(
                {
                    "success": False,
                    "error": f"Issues are disabled for repository: {repository}",
                    "error_type": "permission_error",
                }
            )

        if not permissions.get("write", False):
            logger.warning(
                f"No write access to {repository}, but attempting to create issue"
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
            "issue": {
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
            },
        }

        logger.info(
            f"Successfully created issue #{issue_data.get('number')} in {repository}"
        )
        return json.dumps(result, indent=2)

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

    except GitHubException as e:
        logger.error(f"GitHub API error: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"GitHub API error: {str(e)}",
                "error_type": "github_api_error",
                "status_code": getattr(e, "status_code", None),
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error creating GitHub issue: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error",
            }
        )


async def create_github_pull_request(
    repository: str,
    title: str,
    description: str,
    head_branch: str,
    base_branch: str = "main",
    github_token: Optional[str] = None,
) -> str:
    """
    Create a new pull request in a GitHub repository.

    Args:
        repository: Repository in "owner/repo" format
        title: Pull request title
        description: Pull request description/body
        head_branch: Source branch name
        base_branch: Target branch name (default: "main")
        github_token: GitHub Personal Access Token (optional, uses env var if not provided)

    Returns:
        JSON string containing the created pull request information including URL and number
    """
    try:
        # Validate repository format first
        if "/" not in repository:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Invalid repository format: {repository}. Expected 'owner/repo'",
                    "error_type": "validation_error",
                }
            )

        # Initialize GitHub client
        client = GitHubClient(token=github_token)

        # Check repository permissions
        logger.info(f"Checking permissions for repository: {repository}")
        permissions = await client.check_repository_permissions(repository)

        if not permissions.get("pull_requests", False):
            return json.dumps(
                {
                    "success": False,
                    "error": f"Pull requests are disabled for repository: {repository}",
                    "error_type": "permission_error",
                }
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
            },
        }

        logger.info(
            f"Successfully created pull request #{pr_data.get('number')} in {repository}"
        )
        return json.dumps(result, indent=2)

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

    except GitHubException as e:
        logger.error(f"GitHub API error: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"GitHub API error: {str(e)}",
                "error_type": "github_api_error",
                "status_code": getattr(e, "status_code", None),
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error creating GitHub pull request: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error",
            }
        )


async def check_github_repository_permissions(
    repository: str,
    github_token: Optional[str] = None,
) -> str:
    """
    Check permissions for a GitHub repository.

    Args:
        repository: Repository in "owner/repo" format
        github_token: GitHub Personal Access Token (optional, uses env var if not provided)

    Returns:
        JSON string containing permission information
    """
    try:
        # Validate repository format first
        if "/" not in repository:
            return json.dumps(
                {
                    "success": False,
                    "error": f"Invalid repository format: {repository}. Expected 'owner/repo'",
                    "error_type": "validation_error",
                }
            )

        # Initialize GitHub client
        client = GitHubClient(token=github_token)

        # Check permissions
        logger.info(f"Checking permissions for repository: {repository}")
        permissions = await client.check_repository_permissions(repository)

        # Get repository info
        repo_info = await client.get_repository_info(repository)

        result = {
            "success": True,
            "repository": repository,
            "permissions": permissions,
            "repository_info": {
                "name": repo_info.get("name"),
                "full_name": repo_info.get("full_name"),
                "private": repo_info.get("private"),
                "has_issues": repo_info.get("has_issues"),
                "has_projects": repo_info.get("has_projects"),
                "has_wiki": repo_info.get("has_wiki"),
                "default_branch": repo_info.get("default_branch"),
            },
        }

        logger.info(f"Successfully checked permissions for {repository}")
        return json.dumps(result, indent=2)

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

    except GitHubException as e:
        logger.error(f"GitHub API error: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"GitHub API error: {str(e)}",
                "error_type": "github_api_error",
                "status_code": getattr(e, "status_code", None),
            }
        )

    except Exception as e:
        logger.error(f"Unexpected error checking repository permissions: {str(e)}")
        return json.dumps(
            {
                "success": False,
                "error": f"Unexpected error: {str(e)}",
                "error_type": "unexpected_error",
            }
        )
