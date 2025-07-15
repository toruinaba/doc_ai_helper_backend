"""
Unified Git tools for MCP integration.

This module provides a thin wrapper around the services/git layer,
offering a unified interface for Git operations across different
providers (GitHub, Forgejo) through the MCP layer.
"""

from typing import Optional, List, Dict, Any, Union
import logging
from ...git.factory import GitServiceFactory
from ...git.base import GitServiceBase

logger = logging.getLogger(__name__)

# Global state for configured Git services
_configured_services: Dict[str, GitServiceBase] = {}
_default_service: Optional[str] = None


def configure_git_service(
    service_type: str, config: Dict[str, Any], set_as_default: bool = False
) -> None:
    """
    Configure a Git service for use with unified tools.

    Args:
        service_type: Type of Git service ("github", "forgejo", "mock")
        config: Configuration dictionary for the service
        set_as_default: Whether to set this service as the default

    Example:
        configure_git_service("github", {"access_token": "token"}, True)
    """
    global _configured_services, _default_service

    try:
        # Create service instance using the factory
        service = GitServiceFactory.create(service_type, **config)
        _configured_services[service_type] = service

        if set_as_default:
            _default_service = service_type

        logger.info(f"Configured {service_type} Git service")

    except Exception as e:
        logger.error(f"Failed to configure {service_type} service: {e}")
        raise


def get_configured_service(service_type: Optional[str] = None) -> GitServiceBase:
    """
    Get a configured Git service instance.

    Args:
        service_type: Specific service type to get, or None for default

    Returns:
        GitServiceBase instance

    Raises:
        ValueError: If no service is configured
    """
    global _configured_services, _default_service

    # Use default if no specific type requested
    if service_type is None:
        service_type = _default_service

    if service_type is None or service_type not in _configured_services:
        available = list(_configured_services.keys())
        raise ValueError(
            f"No Git service configured for '{service_type}'. "
            f"Available: {available}"
        )

    return _configured_services[service_type]


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
        # Get the appropriate service
        service = get_configured_service(service_type)
        logger.info(f"Using Git service: {service.__class__.__name__} for {service_type}")

        # Extract repository info from context
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
        else:
            # Default or extract from kwargs
            owner = service_kwargs.get("owner")
            repo = service_kwargs.get("repo")

        if not owner or not repo:
            raise ValueError("Repository owner and name must be provided")

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
        logger.debug(f"Full service response: {result}")
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
        # Get the appropriate service
        service = get_configured_service(service_type)

        # Extract repository info from context
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
        else:
            # Default or extract from kwargs
            owner = service_kwargs.get("owner")
            repo = service_kwargs.get("repo")

        if not owner or not repo:
            raise ValueError("Repository owner and name must be provided")

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
        # Get the appropriate service
        service = get_configured_service(service_type)

        # Extract repository info from context
        if repository_context:
            owner = repository_context.get("owner")
            repo = repository_context.get("repo")
        else:
            # Default or extract from kwargs
            owner = service_kwargs.get("owner")
            repo = service_kwargs.get("repo")

        if not owner or not repo:
            raise ValueError("Repository owner and name must be provided")

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


def get_unified_git_tools() -> Dict[str, Any]:
    """
    Get information about the unified Git tools and configured services.

    Returns:
        Dictionary with tool information and configured services
    """
    global _configured_services, _default_service

    return {
        "configured_services": list(_configured_services.keys()),
        "default_service": _default_service,
        "available_tools": [
            "create_git_issue",
            "create_git_pull_request",
            "check_git_repository_permissions",
        ],
        "supported_services": ["github", "forgejo", "mock"],
    }


# Backward compatibility aliases
git_tools = {
    "configure_git_service": configure_git_service,
    "create_git_issue": create_git_issue,
    "create_git_pull_request": create_git_pull_request,
    "check_git_repository_permissions": check_git_repository_permissions,
    "get_unified_git_tools": get_unified_git_tools,
}

# Export main functions
__all__ = [
    "configure_git_service",
    "create_git_issue",
    "create_git_pull_request",
    "check_git_repository_permissions",
    "get_unified_git_tools",
    "get_configured_service",
    "git_tools",
]
