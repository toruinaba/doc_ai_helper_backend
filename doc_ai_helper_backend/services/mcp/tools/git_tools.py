"""
Git tools for MCP integration.

This module provides direct Git operations using GitServiceFactory.
"""

from typing import Optional, List, Dict, Any
import logging
from ...git.factory import GitServiceFactory
from ....core.config import settings

logger = logging.getLogger(__name__)


async def create_git_issue(
    title: str,
    description: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    repository_context: Optional[Dict[str, Any]] = None,
    service_type: Optional[str] = None,
    **service_kwargs,
) -> str:
    """
    Create a new issue in the Git repository.

    Args:
        title: Issue title
        description: Issue description/body
        labels: List of labels to apply
        assignees: List of usernames to assign
        repository_context: Repository context (owner/repo info)
        service_type: Specific Git service to use
        **service_kwargs: Additional service-specific arguments

    Returns:
        Result message with issue URL
    """
    try:
        # Extract repository info from context
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
        else:
            owner = service_kwargs.get("owner")
            repo = service_kwargs.get("repo")

        if not owner or not repo:
            raise ValueError("Repository owner and name must be provided")

        # Use service_type or fallback to default
        if not service_type:
            service_type = settings.default_git_service or "github"

        # Create service instance directly via factory
        service = GitServiceFactory.create(service_type)
        
        logger.info(f"Creating issue in {owner}/{repo} using {service.__class__.__name__}")
        logger.debug(f"Issue parameters: title='{title}', labels={labels}, assignees={assignees}")

        # Create the issue using the service
        result = await service.create_issue(
            owner=owner,
            repo=repo,
            title=title,
            body=description,
            labels=labels,
            assignees=assignees,
        )

        success_msg = f"Issue created successfully: {result.get('html_url', 'N/A')}"
        logger.info(f"Git issue creation result: {success_msg}")
        return success_msg

    except Exception as e:
        logger.error(f"Failed to create Git issue: {e}")
        return f"Failed to create issue: {str(e)}"


async def create_git_pull_request(
    title: str,
    description: str,
    head_branch: str,
    base_branch: str = "main",
    repository_context: Optional[Dict[str, Any]] = None,
    service_type: Optional[str] = None,
    **service_kwargs,
) -> str:
    """
    Create a new pull request in the Git repository.

    Args:
        title: PR title
        description: PR description/body
        head_branch: Source branch for the PR
        base_branch: Target branch for the PR
        repository_context: Repository context (owner/repo info)
        service_type: Specific Git service to use
        **service_kwargs: Additional service-specific arguments

    Returns:
        Result message with PR URL
    """
    try:
        # Extract repository info from context
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
        else:
            owner = service_kwargs.get("owner")
            repo = service_kwargs.get("repo")

        if not owner or not repo:
            raise ValueError("Repository owner and name must be provided")

        # Use service_type or fallback to default
        if not service_type:
            service_type = settings.default_git_service or "github"

        # Create service instance directly via factory
        service = GitServiceFactory.create(service_type)

        # Create the PR using the service
        result = await service.create_pull_request(
            owner=owner,
            repo=repo,
            title=title,
            body=description,
            head=head_branch,
            base=base_branch,
        )

        return f"Pull request created successfully: {result.get('html_url', 'N/A')}"

    except Exception as e:
        logger.error(f"Failed to create Git pull request: {e}")
        return f"Failed to create pull request: {str(e)}"


async def check_git_repository_permissions(
    repository_context: Optional[Dict[str, Any]] = None,
    service_type: Optional[str] = None,
    **service_kwargs,
) -> Dict[str, Any]:
    """
    Check repository permissions for the configured Git service.

    Args:
        repository_context: Repository context (owner/repo info)
        service_type: Specific Git service to use
        **service_kwargs: Additional service-specific arguments

    Returns:
        Dictionary with permission information
    """
    try:
        # Extract repository info from context
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
        else:
            owner = service_kwargs.get("owner")
            repo = service_kwargs.get("repo")

        if not owner or not repo:
            raise ValueError("Repository owner and name must be provided")

        # Use service_type or fallback to default
        if not service_type:
            service_type = settings.default_git_service or "github"

        # Create service instance directly via factory
        service = GitServiceFactory.create(service_type)

        # Check permissions using the service
        if hasattr(service, "check_repository_permissions"):
            result = await service.check_repository_permissions(owner, repo)
            return result
        else:
            # Fallback - try to get basic repository info
            repo_info = await service.get_repository_info(owner, repo)
            return {
                "can_read": True,
                "can_write": repo_info.get("permissions", {}).get("push", False),
                "repository_exists": True,
            }

    except Exception as e:
        logger.error(f"Failed to check Git repository permissions: {e}")
        return {
            "can_read": False,
            "can_write": False,
            "repository_exists": False,
            "error": str(e),
        }


__all__ = [
    "create_git_issue",
    "create_git_pull_request", 
    "check_git_repository_permissions",
]