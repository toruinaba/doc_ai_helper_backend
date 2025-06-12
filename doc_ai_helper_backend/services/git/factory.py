"""
Git service factory.
"""

from typing import Dict, Optional, Type

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.core.exceptions import GitServiceException
from doc_ai_helper_backend.services.git.base import GitServiceBase
from doc_ai_helper_backend.services.git.github_service import GitHubService


class GitServiceFactory:
    """Factory for creating Git service instances."""

    # Registry of available Git services
    _services: Dict[str, Type[GitServiceBase]] = {
        "github": GitHubService,
    }

    @classmethod
    def register_service(cls, name: str, service_class: Type[GitServiceBase]) -> None:
        """Register a new Git service.

        Args:
            name: Service name
            service_class: Service class
        """
        cls._services[name] = service_class

    @classmethod
    def create(
        cls, service_type: str, access_token: Optional[str] = None
    ) -> GitServiceBase:
        """Create a Git service instance.

        Args:
            service_type: Git service type
            access_token: Access token for the Git service. If None, the token will be
                taken from settings based on the service type.

        Returns:
            GitServiceBase: Git service instance

        Raises:
            GitServiceException: If service type is not supported
        """
        service_type = service_type.lower()

        # Check if service type is supported
        if service_type not in cls._services:
            raise GitServiceException(f"Unsupported Git service: {service_type}")

        # If no access token is provided, use the one from settings
        if access_token is None and service_type == "github":
            access_token = settings.github_token

        # Create service instance
        service_class = cls._services[service_type]
        return service_class(access_token=access_token)
