"""
Git tools for MCP integration.

This module provides direct Git operations using GitServiceFactory.
Repository context is automatically injected by the LLM service.
"""

from typing import Optional, List, Dict, Any
import logging
from ...git.factory import GitServiceFactory
from ....core.config import settings

logger = logging.getLogger(__name__)


def _extract_service_type_from_context(repository_context: Dict[str, Any]) -> str:
    """
    Extract git service type from repository context.
    
    Args:
        repository_context: Repository context containing service info
        
    Returns:
        Service type (github, forgejo, etc.)
    """
    # Check if service type is explicitly specified in context
    if "service" in repository_context:
        return repository_context["service"]
    
    # Detect service type from URL patterns if available
    if "base_url" in repository_context:
        base_url = repository_context["base_url"].lower()
        if "github.com" in base_url:
            return "github"
        elif "forgejo" in base_url or repository_context.get("is_forgejo"):
            return "forgejo"
    
    # Check for service-specific indicators
    if repository_context.get("github_token"):
        return "github"
    elif repository_context.get("forgejo_token") or repository_context.get("forgejo_username"):
        return "forgejo"
    
    # Fallback to configured default
    return settings.default_git_service or "github"


def _validate_repository_context(repository_context: Dict[str, Any]) -> None:
    """
    Validate repository context contains required fields.
    
    Args:
        repository_context: Repository context dictionary
        
    Raises:
        ValueError: If required fields are missing or invalid
    """
    if not repository_context:
        raise ValueError("repository_context is required")
    
    owner = repository_context.get("owner")
    repo = repository_context.get("repo")
    service = repository_context.get("service")
    
    if not owner:
        raise ValueError("repository_context must contain 'owner' field")
    
    if not repo:
        raise ValueError("repository_context must contain 'repo' field")
    
    if not service:
        raise ValueError("repository_context must contain 'service' field")
    
    if not isinstance(owner, str) or not owner.strip():
        raise ValueError("repository_context 'owner' must be a non-empty string")
    
    if not isinstance(repo, str) or not repo.strip():
        raise ValueError("repository_context 'repo' must be a non-empty string")
    
    if not isinstance(service, str) or not service.strip():
        raise ValueError("repository_context 'service' must be a non-empty string")


async def create_git_issue(
    title: str,
    description: str,
<<<<<<< Updated upstream
    repository_context: Dict[str, Any],  # Required: automatically injected by LLM service
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
=======
    repository_context: Dict[str, Any],
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    service_type: Optional[str] = None,
    **service_kwargs,
>>>>>>> Stashed changes
) -> str:
    """
    Create a new issue in the Git repository.

    Args:
        title: Issue title
        description: Issue description/body
<<<<<<< Updated upstream
        repository_context: Repository context with owner/repo/service info (injected by LLM)
        labels: List of labels to apply
        assignees: List of usernames to assign
=======
        repository_context: Repository context (owner/repo info) - REQUIRED
        labels: List of labels to apply
        assignees: List of usernames to assign
        service_type: Specific Git service to use (overrides repository_context.service)
        **service_kwargs: Additional service-specific arguments
>>>>>>> Stashed changes

    Returns:
        Result message with issue URL
        
<<<<<<< Updated upstream
    Note:
        repository_context is automatically injected by the LLM service and contains:
        - owner: Repository owner
        - repo: Repository name  
        - service: Git service type (github, forgejo, etc.)
        - Authentication info (tokens, etc.)
    """
    try:
        # Validate repository context
        if not repository_context:
            raise ValueError(
                "Repository context is required but not provided. "
                "This context should be automatically injected by the LLM service."
            )

        # Extract repository info from context
        owner = repository_context.get("owner")
        repo = repository_context.get("repo")
        
        if not owner or not repo:
            raise ValueError(
                f"Repository owner and name must be provided in repository_context. "
                f"Got: owner='{owner}', repo='{repo}'"
            )

        # Determine service type from repository context
        service_type = _extract_service_type_from_context(repository_context)
        
        logger.info(f"Creating issue in {owner}/{repo} using service: {service_type}")
=======
    Raises:
        ValueError: If repository_context is invalid or missing required fields
    """
    try:
        # Validate repository_context first
        _validate_repository_context(repository_context)
        
        # Extract repository info from context (guaranteed to be valid after validation)
        owner = repository_context["owner"]
        repo = repository_context["repo"]
        context_service_type = repository_context["service"]
        
        # Use explicit service_type if provided, otherwise use from context
        final_service_type = service_type or context_service_type
        
        # Get the appropriate service
        service = get_configured_service(final_service_type)
        logger.info(f"Using Git service: {service.__class__.__name__} for {final_service_type}")
        logger.info(f"Creating issue in {owner}/{repo} using {service.__class__.__name__}")
>>>>>>> Stashed changes
        logger.debug(f"Issue parameters: title='{title}', labels={labels}, assignees={assignees}")

        # Create service instance directly via factory
        service = GitServiceFactory.create(service_type)
        
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

    except ValueError as e:
        logger.error(f"Invalid repository context for Git issue creation: {e}")
        return f"Invalid repository context: {str(e)}"
    except Exception as e:
        logger.error(f"Failed to create Git issue: {e}")
        return f"Failed to create issue: {str(e)}"


async def create_git_pull_request(
    title: str,
    description: str,
    head_branch: str,
<<<<<<< Updated upstream
    repository_context: Dict[str, Any],  # Required: automatically injected by LLM service
    base_branch: str = "main",
=======
    repository_context: Dict[str, Any],
    base_branch: str = "main",
    service_type: Optional[str] = None,
    **service_kwargs,
>>>>>>> Stashed changes
) -> str:
    """
    Create a new pull request in the Git repository.

    Args:
        title: PR title
        description: PR description/body
        head_branch: Source branch for the PR
<<<<<<< Updated upstream
        repository_context: Repository context with owner/repo/service info (injected by LLM)
        base_branch: Target branch for the PR
=======
        repository_context: Repository context (owner/repo info) - REQUIRED
        base_branch: Target branch for the PR
        service_type: Specific Git service to use (overrides repository_context.service)
        **service_kwargs: Additional service-specific arguments
>>>>>>> Stashed changes

    Returns:
        Result message with PR URL
        
<<<<<<< Updated upstream
    Note:
        repository_context is automatically injected by the LLM service and contains:
        - owner: Repository owner
        - repo: Repository name  
        - service: Git service type (github, forgejo, etc.)
        - Authentication info (tokens, etc.)
    """
    try:
        # Validate repository context
        if not repository_context:
            raise ValueError(
                "Repository context is required but not provided. "
                "This context should be automatically injected by the LLM service."
            )

        # Extract repository info from context
        owner = repository_context.get("owner")
        repo = repository_context.get("repo")
        
        if not owner or not repo:
            raise ValueError(
                f"Repository owner and name must be provided in repository_context. "
                f"Got: owner='{owner}', repo='{repo}'"
            )

        # Determine service type from repository context
        service_type = _extract_service_type_from_context(repository_context)
        
        logger.info(f"Creating PR in {owner}/{repo} using service: {service_type}")

        # Create service instance directly via factory
        service = GitServiceFactory.create(service_type)
=======
    Raises:
        ValueError: If repository_context is invalid or missing required fields
    """
    try:
        # Validate repository_context first
        _validate_repository_context(repository_context)
        
        # Extract repository info from context (guaranteed to be valid after validation)
        owner = repository_context["owner"]
        repo = repository_context["repo"]
        context_service_type = repository_context["service"]
        
        # Use explicit service_type if provided, otherwise use from context
        final_service_type = service_type or context_service_type
        
        # Get the appropriate service
        service = get_configured_service(final_service_type)
        logger.info(f"Using Git service: {service.__class__.__name__} for {final_service_type}")
        logger.info(f"Creating PR in {owner}/{repo} using {service.__class__.__name__}")
        logger.debug(f"PR parameters: title='{title}', head='{head_branch}', base='{base_branch}'")
>>>>>>> Stashed changes

        # Create the PR using the service
        result = await service.create_pull_request(
            owner=owner,
            repo=repo,
            title=title,
            body=description,
            head=head_branch,
            base=base_branch,
        )

        success_msg = f"Pull request created successfully: {result.get('html_url', 'N/A')}"
        logger.info(f"Git PR creation result: {success_msg}")
<<<<<<< Updated upstream
=======
        logger.debug(f"Full service response: {result}")
>>>>>>> Stashed changes
        return success_msg

    except ValueError as e:
        logger.error(f"Invalid repository context for Git PR creation: {e}")
        return f"Invalid repository context: {str(e)}"
    except Exception as e:
        logger.error(f"Failed to create Git pull request: {e}")
        return f"Failed to create pull request: {str(e)}"


async def check_git_repository_permissions(
    repository_context: Dict[str, Any],  # Required: automatically injected by LLM service
) -> Dict[str, Any]:
    """
    Check repository permissions for the configured Git service.

    Args:
        repository_context: Repository context with owner/repo/service info (injected by LLM)

    Returns:
        Dictionary with permission information
        
    Note:
        repository_context is automatically injected by the LLM service and contains:
        - owner: Repository owner
        - repo: Repository name  
        - service: Git service type (github, forgejo, etc.)
        - Authentication info (tokens, etc.)
    """
    try:
        # Validate repository context
        if not repository_context:
            raise ValueError(
                "Repository context is required but not provided. "
                "This context should be automatically injected by the LLM service."
            )

        # Extract repository info from context
        owner = repository_context.get("owner")
        repo = repository_context.get("repo")
        
        if not owner or not repo:
            return {
                "error": f"Repository owner and name must be provided in repository_context. Got: owner='{owner}', repo='{repo}'",
                "can_read": False,
                "can_write": False,
                "repository_exists": False,
            }

        # Determine service type from repository context
        service_type = _extract_service_type_from_context(repository_context)
        
        logger.info(f"Checking permissions for {owner}/{repo} using service: {service_type}")

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
                "service_type": service_type,
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