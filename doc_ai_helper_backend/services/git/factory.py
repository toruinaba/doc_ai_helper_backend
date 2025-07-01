"""
Git service factory.
"""

from typing import Any, Dict, List, Optional, Type

from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.core.exceptions import GitServiceException
from doc_ai_helper_backend.services.git.base import GitServiceBase
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService
from doc_ai_helper_backend.services.git.github_service import GitHubService
from doc_ai_helper_backend.services.git.mock_service import MockGitService


class GitServiceFactory:
    """Factory for creating Git service instances."""

    # Registry of available Git services
    _services: Dict[str, Type[GitServiceBase]] = {
        "github": GitHubService,
        "forgejo": ForgejoService,
        "mock": MockGitService,
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
        cls, service_type: str, access_token: Optional[str] = None, **kwargs
    ) -> GitServiceBase:
        """Create a Git service instance.

        Args:
            service_type: Git service type
            access_token: Access token for the Git service. If None, the token will be
                taken from settings based on the service type.
            **kwargs: Additional service-specific configuration

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
        if access_token is None:
            if service_type == "github":
                access_token = settings.github_token
            elif service_type == "forgejo":
                access_token = settings.forgejo_token

        # Create service instance
        service_class = cls._services[service_type]

        # Handle Forgejo service with additional parameters
        if service_type == "forgejo":
            base_url = kwargs.get("base_url") or settings.forgejo_base_url
            if not base_url:
                raise GitServiceException(
                    "Forgejo base URL is required. Set FORGEJO_BASE_URL environment variable "
                    "or provide base_url parameter."
                )
            return service_class(
                base_url=base_url,
                access_token=access_token or settings.forgejo_token,
                username=kwargs.get("username") or settings.forgejo_username,
                password=kwargs.get("password") or settings.forgejo_password,
                **{
                    k: v
                    for k, v in kwargs.items()
                    if k not in ["base_url", "username", "password"]
                },
            )

        return service_class(access_token=access_token)

    @classmethod
    def get_available_services(cls) -> List[str]:
        """Get list of available Git services.

        Returns:
            List[str]: List of available service names
        """
        return list(cls._services.keys())

    @classmethod
    def is_service_supported(cls, service_type: str) -> bool:
        """Check if a Git service type is supported.

        Args:
            service_type: Git service type

        Returns:
            bool: True if supported, False otherwise
        """
        return service_type.lower() in cls._services

    @classmethod
    def create_with_config(
        cls, service_type: str, config: Optional[Dict[str, Any]] = None
    ) -> GitServiceBase:
        """Create a Git service instance with additional configuration.

        Args:
            service_type: Git service type
            config: Additional configuration parameters

        Returns:
            GitServiceBase: Git service instance

        Raises:
            GitServiceException: If service type is not supported
        """
        service_type = service_type.lower()
        config = config or {}

        # Check if service type is supported
        if service_type not in cls._services:
            raise GitServiceException(f"Unsupported Git service: {service_type}")

        service_class = cls._services[service_type]

        if service_type == "forgejo":
            base_url = config.get("base_url") or settings.forgejo_base_url
            if not base_url:
                raise GitServiceException(
                    "Forgejo base URL is required in config or settings."
                )
            return service_class(
                base_url=base_url,
                access_token=config.get("access_token") or settings.forgejo_token,
                username=config.get("username") or settings.forgejo_username,
                password=config.get("password") or settings.forgejo_password,
            )
        elif service_type == "github":
            return service_class(
                access_token=config.get("access_token", settings.github_token)
            )
        else:
            return service_class(**config)

    @classmethod
    def test_service_connection(cls, service_type: str, **kwargs) -> Dict[str, Any]:
        """Test connection to a Git service.

        Args:
            service_type: Git service type
            **kwargs: Service-specific configuration

        Returns:
            Dict[str, Any]: Connection test results
        """
        try:
            service = cls.create(service_type, **kwargs)
            return {
                "service": service_type,
                "status": "created",
                "auth_methods": service.get_supported_auth_methods(),
                "configured": bool(
                    service.access_token
                    or (
                        hasattr(service, "username")
                        and getattr(service, "username", None)
                    )
                ),
            }
        except Exception as e:
            return {"service": service_type, "status": "error", "error": str(e)}

    @classmethod
    def _get_access_token_from_settings(cls, service_type: str) -> Optional[str]:
        """Get access token from settings based on service type.

        Args:
            service_type: Git service type

        Returns:
            Optional[str]: Access token or None
        """
        if service_type == "github":
            return settings.github_token
        elif service_type == "forgejo":
            return settings.forgejo_token
        elif service_type == "gitlab":
            return getattr(settings, "gitlab_token", None)
        return None
