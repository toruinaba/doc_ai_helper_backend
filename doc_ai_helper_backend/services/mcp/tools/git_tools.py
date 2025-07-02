"""
Unified Git tools for MCP server.

This module provides a unified interface for Git operations across multiple
Git hosting platforms (GitHub, Forgejo, etc.) through the MCP tools abstraction.
"""

import logging
from typing import Any, Dict, List, Optional

from .git.factory import MCPGitToolsFactory
from .git.base import MCPGitToolsBase

logger = logging.getLogger(__name__)


class UnifiedGitTools:
    """
    Unified Git tools interface for MCP server.
    
    This class provides a single interface for Git operations that can work
    with multiple Git hosting platforms based on configuration.
    """
    
    def __init__(self):
        """Initialize unified Git tools."""
        self._adapters: Dict[str, MCPGitToolsBase] = {}
        self._default_service: Optional[str] = None
    
    def configure_service(
        self,
        service_type: str,
        config: Optional[Dict[str, Any]] = None,
        set_as_default: bool = False,
        **kwargs
    ) -> None:
        """
        Configure a Git service for use with unified tools.
        
        Args:
            service_type: Type of Git service ('github', 'forgejo', etc.)
            config: Service configuration dictionary
            set_as_default: Whether to set this as the default service
            **kwargs: Additional configuration parameters
        """
        try:
            adapter = MCPGitToolsFactory.create(service_type, config, **kwargs)
            self._adapters[service_type] = adapter
            
            if set_as_default or not self._default_service:
                self._default_service = service_type
                
            logger.info(f"Configured {service_type} Git service adapter")
            
        except Exception as e:
            logger.error(f"Failed to configure {service_type} Git service: {str(e)}")
            raise
    
    def get_adapter(self, service_type: Optional[str] = None) -> MCPGitToolsBase:
        """
        Get Git tools adapter for specified service.
        
        Args:
            service_type: Type of Git service, uses default if None
            
        Returns:
            MCPGitToolsBase: Git tools adapter
            
        Raises:
            ValueError: If service is not configured
        """
        target_service = service_type or self._default_service
        
        if not target_service:
            raise ValueError("No Git service specified and no default service configured")
        
        if target_service not in self._adapters:
            raise ValueError(f"Git service '{target_service}' not configured")
        
        return self._adapters[target_service]
    
    async def create_issue(
        self,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        repository_context: Optional[Dict[str, Any]] = None,
        service_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create an issue using the appropriate Git service adapter.
        
        Args:
            title: Issue title
            description: Issue description
            labels: Issue labels
            assignees: Issue assignees
            repository_context: Repository context
            service_type: Git service type (uses default if None)
            **kwargs: Additional service-specific parameters
            
        Returns:
            JSON string with operation result
        """
        # Determine service type from context if not specified
        if not service_type and repository_context:
            service_type = repository_context.get("service")
        
        adapter = self.get_adapter(service_type)
        
        return await adapter.create_issue(
            title=title,
            description=description,
            labels=labels,
            assignees=assignees,
            repository_context=repository_context,
            **kwargs
        )
    
    async def create_pull_request(
        self,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        repository_context: Optional[Dict[str, Any]] = None,
        service_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create a pull request using the appropriate Git service adapter.
        
        Args:
            title: PR title
            description: PR description
            head_branch: Source branch
            base_branch: Target branch
            repository_context: Repository context
            service_type: Git service type (uses default if None)
            **kwargs: Additional service-specific parameters
            
        Returns:
            JSON string with operation result
        """
        # Determine service type from context if not specified
        if not service_type and repository_context:
            service_type = repository_context.get("service")
        
        adapter = self.get_adapter(service_type)
        
        return await adapter.create_pull_request(
            title=title,
            description=description,
            head_branch=head_branch,
            base_branch=base_branch,
            repository_context=repository_context,
            **kwargs
        )
    
    async def check_repository_permissions(
        self,
        repository_context: Optional[Dict[str, Any]] = None,
        service_type: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Check repository permissions using the appropriate Git service adapter.
        
        Args:
            repository_context: Repository context
            service_type: Git service type (uses default if None)
            **kwargs: Additional service-specific parameters
            
        Returns:
            JSON string with permission information
        """
        # Determine service type from context if not specified
        if not service_type and repository_context:
            service_type = repository_context.get("service")
        
        adapter = self.get_adapter(service_type)
        
        return await adapter.check_repository_permissions(
            repository_context=repository_context,
            **kwargs
        )
    
    def get_configured_services(self) -> List[str]:
        """Get list of configured Git services."""
        return list(self._adapters.keys())
    
    def get_default_service(self) -> Optional[str]:
        """Get the default Git service."""
        return self._default_service
    
    def set_default_service(self, service_type: str) -> None:
        """
        Set the default Git service.
        
        Args:
            service_type: Git service type to set as default
            
        Raises:
            ValueError: If service is not configured
        """
        if service_type not in self._adapters:
            raise ValueError(f"Git service '{service_type}' not configured")
        
        self._default_service = service_type
        logger.info(f"Set default Git service to: {service_type}")


# Global instance for unified Git tools
_unified_git_tools = UnifiedGitTools()


def get_unified_git_tools() -> UnifiedGitTools:
    """Get the global unified Git tools instance."""
    return _unified_git_tools


def configure_git_service(
    service_type: str,
    config: Optional[Dict[str, Any]] = None,
    set_as_default: bool = False,
    **kwargs
) -> None:
    """
    Configure a Git service for use with unified tools.
    
    Args:
        service_type: Type of Git service ('github', 'forgejo', etc.)
        config: Service configuration dictionary
        set_as_default: Whether to set this as the default service
        **kwargs: Additional configuration parameters
    """
    _unified_git_tools.configure_service(service_type, config, set_as_default, **kwargs)


# Convenience functions that use the unified interface
async def create_git_issue(
    title: str,
    description: str,
    labels: Optional[List[str]] = None,
    assignees: Optional[List[str]] = None,
    repository_context: Optional[Dict[str, Any]] = None,
    service_type: Optional[str] = None,
    **kwargs
) -> str:
    """Create an issue using unified Git tools."""
    return await _unified_git_tools.create_issue(
        title=title,
        description=description,
        labels=labels,
        assignees=assignees,
        repository_context=repository_context,
        service_type=service_type,
        **kwargs
    )


async def create_git_pull_request(
    title: str,
    description: str,
    head_branch: str,
    base_branch: str = "main",
    repository_context: Optional[Dict[str, Any]] = None,
    service_type: Optional[str] = None,
    **kwargs
) -> str:
    """Create a pull request using unified Git tools."""
    return await _unified_git_tools.create_pull_request(
        title=title,
        description=description,
        head_branch=head_branch,
        base_branch=base_branch,
        repository_context=repository_context,
        service_type=service_type,
        **kwargs
    )


async def check_git_repository_permissions(
    repository_context: Optional[Dict[str, Any]] = None,
    service_type: Optional[str] = None,
    **kwargs
) -> str:
    """Check repository permissions using unified Git tools."""
    return await _unified_git_tools.check_repository_permissions(
        repository_context=repository_context,
        service_type=service_type,
        **kwargs
    )
