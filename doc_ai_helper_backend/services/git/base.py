"""
Abstract base class for Git services.
"""

import abc
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from doc_ai_helper_backend.core.exceptions import (
    GitServiceException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
)
from doc_ai_helper_backend.models.document import (
    DocumentContent,
    DocumentMetadata,
    DocumentResponse,
    DocumentType,
    FileTreeItem,
    RepositoryStructureResponse,
)


class GitServiceBase(abc.ABC):
    """Abstract base class for Git services."""

    def __init__(self, access_token: Optional[str] = None, **kwargs):
        """Initialize Git service.

        Args:
            access_token: Access token for the Git service
            **kwargs: Additional service-specific configuration
        """
        self.access_token = access_token
        self.service_name = self._get_service_name()
        self.config = kwargs

    @abc.abstractmethod
    def _get_service_name(self) -> str:
        """Get service name.

        Returns:
            str: Service name
        """
        pass

    @abc.abstractmethod
    def get_supported_auth_methods(self) -> List[str]:
        """Get supported authentication methods.

        Returns:
            List[str]: List of supported authentication methods
        """
        pass

    @abc.abstractmethod
    async def authenticate(self) -> bool:
        """Test authentication with the Git service.

        Returns:
            bool: True if authentication is successful, False otherwise

        Raises:
            UnauthorizedException: If authentication fails
            GitServiceException: If there is an error with the Git service
        """
        pass

    @abc.abstractmethod
    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information.

        Returns:
            Dict[str, Any]: Rate limit information including current usage and limits

        Raises:
            GitServiceException: If there is an error with the Git service
            UnauthorizedException: If access is unauthorized
        """
        pass

    @abc.abstractmethod
    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to the Git service.

        Returns:
            Dict[str, Any]: Connection test results including status and service info

        Raises:
            GitServiceException: If connection test fails
        """
        pass

    @abc.abstractmethod
    async def get_document(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> DocumentResponse:
        """Get document from a repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Document path
            ref: Branch or tag name. Default is "main"

        Returns:
            DocumentResponse: Document data

        Raises:
            NotFoundException: If document is not found
            GitServiceException: If there is an error with the Git service
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        pass

    @abc.abstractmethod
    async def get_repository_structure(
        self, owner: str, repo: str, ref: str = "main", path: str = ""
    ) -> RepositoryStructureResponse:
        """Get repository structure.

        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch or tag name. Default is "main"
            path: Path prefix to filter by. Default is ""

        Returns:
            RepositoryStructureResponse: Repository structure data

        Raises:
            NotFoundException: If repository is not found
            GitServiceException: If there is an error with the Git service
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        pass

    @abc.abstractmethod
    async def search_repository(
        self, owner: str, repo: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search repository.

        Args:
            owner: Repository owner
            repo: Repository name
            query: Search query
            limit: Maximum number of results. Default is 10

        Returns:
            List[Dict[str, Any]]: Search results

        Raises:
            NotFoundException: If repository is not found
            GitServiceException: If there is an error with the Git service
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        pass

    @abc.abstractmethod
    async def check_repository_exists(self, owner: str, repo: str) -> bool:
        """Check if repository exists.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            bool: True if repository exists, False otherwise

        Raises:
            GitServiceException: If there is an error with the Git service
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        pass

    def _handle_http_error(self, response: Any, context: str) -> None:
        """Handle HTTP errors in a standardized way.

        Args:
            response: HTTP response object
            context: Context description for error logging

        Raises:
            NotFoundException: If resource is not found (404)
            UnauthorizedException: If access is unauthorized (401)
            RateLimitException: If rate limit is exceeded (429)
            GitServiceException: For other HTTP errors
        """
        status_code = getattr(response, "status_code", None)

        if status_code == 404:
            raise NotFoundException(f"{context}: Resource not found")
        elif status_code == 401:
            raise UnauthorizedException(f"{context}: Unauthorized access")
        elif status_code == 403:
            raise UnauthorizedException(f"{context}: Forbidden access")
        elif status_code == 429:
            raise RateLimitException(f"{context}: Rate limit exceeded")
        else:
            error_msg = f"{context}: HTTP {status_code}"
            if hasattr(response, "text"):
                error_msg += f" - {response.text}"
            raise GitServiceException(error_msg)

    @staticmethod
    def detect_document_type(path: str) -> DocumentType:
        """Detect document type from file extension.

        Args:
            path: Document path

        Returns:
            DocumentType: Document type
        """
        if path.endswith(".md"):
            return DocumentType.MARKDOWN
        elif path.endswith(".qmd"):
            return DocumentType.QUARTO
        elif path.endswith(".html"):
            return DocumentType.HTML
        else:
            return DocumentType.OTHER

    def _get_default_headers(self) -> Dict[str, str]:
        """Get default headers for API requests.

        Returns:
            Dict[str, str]: Default headers
        """
        headers = {
            "User-Agent": f"doc-ai-helper/{self.service_name}",
            "Accept": "application/json",
        }

        if self.access_token:
            headers.update(self._get_auth_headers())

        return headers

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers.

        This method should be overridden by subclasses to provide
        service-specific authentication headers.

        Returns:
            Dict[str, str]: Authentication headers
        """
        if self.access_token:
            return {"Authorization": f"token {self.access_token}"}
        return {}

    async def _make_request(self, client: Any, method: str, url: str, **kwargs) -> Any:
        """Make an HTTP request with error handling.

        Args:
            client: HTTP client instance
            method: HTTP method
            url: Request URL
            **kwargs: Additional request parameters

        Returns:
            Response object

        Raises:
            GitServiceException: If request fails
        """
        try:
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response
        except Exception as e:
            self._handle_http_error(getattr(e, "response", None), f"Request to {url}")
            raise GitServiceException(f"Request failed: {str(e)}")
