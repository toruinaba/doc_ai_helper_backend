"""
Forgejo service implementation.

Forgejo is a self-hosted Git service that is compatible with Gitea API.
This implementation provides access to Forgejo repositories and files.
"""

import base64
import logging
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import HttpUrl

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
from doc_ai_helper_backend.services.document_processors.factory import (
    DocumentProcessorFactory,
)
from doc_ai_helper_backend.services.git.base import GitServiceBase

# Logger
logger = logging.getLogger("doc_ai_helper")


class ForgejoService(GitServiceBase):
    """Forgejo Git service implementation.

    Supports both token and basic authentication.
    Compatible with Gitea API v1.
    """

    def __init__(
        self,
        base_url: str,
        access_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        """Initialize Forgejo service.

        Args:
            base_url: Base URL of the Forgejo instance (e.g., https://git.example.com)
            access_token: API access token (preferred method)
            username: Username for basic authentication
            password: Password for basic authentication
            **kwargs: Additional configuration options
        """
        super().__init__(access_token=access_token, **kwargs)
        self.base_url = base_url.rstrip("/")
        self.api_base_url = f"{self.base_url}/api/v1"
        self.username = username
        self.password = password

        # Validate authentication configuration
        if not (access_token or (username and password)):
            logger.warning("No authentication configured for Forgejo service")

    def _get_service_name(self) -> str:
        """Get service name."""
        return "forgejo"

    def get_supported_auth_methods(self) -> List[str]:
        """Get supported authentication methods."""
        return ["token", "basic_auth"]

    def _get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for Forgejo API."""
        if self.access_token:
            # Forgejo/Gitea uses Bearer token authentication
            return {"Authorization": f"Bearer {self.access_token}"}
        elif self.username and self.password:
            # Basic authentication
            credentials = base64.b64encode(
                f"{self.username}:{self.password}".encode()
            ).decode()
            return {"Authorization": f"Basic {credentials}"}
        return {}

    async def authenticate(self) -> bool:
        """Test authentication with Forgejo."""
        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                # Use repository search endpoint instead of /user for authentication test
                response = await self._make_request(
                    client, "GET", f"{self.api_base_url}/repos/search", headers=headers
                )
                return response.status_code == 200
        except (UnauthorizedException, GitServiceException):
            return False

    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get rate limit information from Forgejo.

        Note: Forgejo/Gitea may not have the same rate limiting as GitHub.
        This method returns available information or defaults.
        """
        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                # Use repository search endpoint instead of /user
                response = await self._make_request(
                    client, "GET", f"{self.api_base_url}/repos/search", headers=headers
                )

                # Extract rate limit info from headers if available
                rate_limit_info = {
                    "service": "forgejo",
                    "authenticated": True,
                    "remaining": response.headers.get("X-RateLimit-Remaining"),
                    "limit": response.headers.get("X-RateLimit-Limit"),
                    "reset": response.headers.get("X-RateLimit-Reset"),
                }
                return rate_limit_info
        except Exception as e:
            logger.error(f"Failed to get rate limit info: {str(e)}")
            return {"service": "forgejo", "authenticated": False, "error": str(e)}

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Forgejo instance."""
        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                # Test basic connectivity
                response = await self._make_request(
                    client, "GET", f"{self.api_base_url}/version", headers=headers
                )

                version_info = response.json() if response.status_code == 200 else {}

                # Test authentication with repository search (less privileged endpoint)
                auth_test_response = await self._make_request(
                    client, "GET", f"{self.api_base_url}/repos/search", headers=headers
                )
                auth_test = auth_test_response.status_code == 200

                return {
                    "service": "forgejo",
                    "base_url": self.base_url,
                    "api_url": self.api_base_url,
                    "status": "connected",
                    "authenticated": auth_test,
                    "version": version_info.get("version", "unknown"),
                    "auth_method": (
                        "token"
                        if self.access_token
                        else "basic" if self.username else "none"
                    ),
                }
        except Exception as e:
            logger.error(f"Connection test failed: {str(e)}")
            return {
                "service": "forgejo",
                "base_url": self.base_url,
                "status": "failed",
                "error": str(e),
            }

    async def check_repository_exists(self, owner: str, repo: str) -> bool:
        """Check if repository exists in Forgejo."""
        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                response = await client.get(
                    f"{self.api_base_url}/repos/{owner}/{repo}", headers=headers
                )
                return response.status_code == 200
        except Exception:
            return False

    async def get_document(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> DocumentResponse:
        """Get document from Forgejo repository."""
        try:
            # Check if repository exists
            if not await self.check_repository_exists(owner, repo):
                raise NotFoundException(f"Repository {owner}/{repo} not found")

            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                # Get file content
                response = await self._make_request(
                    client,
                    "GET",
                    f"{self.api_base_url}/repos/{owner}/{repo}/contents/{path}",
                    headers=headers,
                    params={"ref": ref},
                )

                file_data = response.json()

                # Decode content
                if file_data.get("encoding") == "base64":
                    content = base64.b64decode(file_data["content"]).decode("utf-8")
                else:
                    content = file_data.get("content", "")

                # Detect document type
                document_type = self.detect_document_type(path)

                # Process document
                processor = DocumentProcessorFactory.create(document_type)
                document_content = processor.process_content(content, path)
                extended_metadata = processor.extract_metadata(content, path)

                # Convert ExtendedDocumentMetadata to DocumentMetadata
                metadata = DocumentMetadata(
                    size=file_data.get("size", len(content)),
                    last_modified=datetime.utcnow(),  # Forgejo might not provide this
                    content_type=(
                        "text/markdown"
                        if document_type == DocumentType.MARKDOWN
                        else "text/plain"
                    ),
                    sha=file_data.get("sha"),
                    download_url=file_data.get("download_url"),
                    html_url=file_data.get("html_url"),
                    raw_url=file_data.get(
                        "download_url"
                    ),  # Use download_url as raw_url
                    extra=(
                        extended_metadata.dict()
                        if hasattr(extended_metadata, "dict")
                        else {}
                    ),
                )

                return DocumentResponse(
                    path=path,
                    name=file_data.get("name", path.split("/")[-1]),
                    type=document_type,
                    content=DocumentContent(content=content),
                    metadata=metadata,
                    repository=repo,
                    owner=owner,
                    service="forgejo",
                    ref=ref,
                    links=processor.extract_links(content, path),
                )

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting document from Forgejo: {str(e)}")
            raise GitServiceException(f"Failed to get document: {str(e)}")

    async def get_repository_structure(
        self, owner: str, repo: str, ref: str = "main", path: str = ""
    ) -> RepositoryStructureResponse:
        """Get repository structure from Forgejo."""
        try:
            # Check if repository exists
            if not await self.check_repository_exists(owner, repo):
                raise NotFoundException(f"Repository {owner}/{repo} not found")

            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                # Get repository contents
                response = await self._make_request(
                    client,
                    "GET",
                    f"{self.api_base_url}/repos/{owner}/{repo}/contents",
                    headers=headers,
                    params={"ref": ref, "path": path},
                )

                contents = response.json()

                # Convert to FileTreeItem format
                files = []
                for item in contents:
                    file_item = FileTreeItem(
                        name=item["name"],
                        path=item["path"],
                        type="file" if item["type"] == "file" else "directory",
                        size=item.get("size", 0),
                        sha=item.get("sha", ""),
                        download_url=item.get("download_url", ""),
                        html_url=item.get("html_url", ""),
                        git_url=item.get("git_url", ""),
                    )
                    files.append(file_item)

                return RepositoryStructureResponse(
                    service="forgejo",
                    owner=owner,
                    repo=repo,
                    ref=ref,
                    tree=files,
                    last_updated=datetime.utcnow(),
                )

        except NotFoundException:
            raise
        except Exception as e:
            logger.error(f"Error getting repository structure from Forgejo: {str(e)}")
            raise GitServiceException(f"Failed to get repository structure: {str(e)}")

    async def search_repository(
        self, owner: str, repo: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search repository in Forgejo.

        Note: Forgejo/Gitea search API may be different from GitHub.
        This implementation provides basic search functionality.
        """
        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                # Use repository search endpoint
                response = await self._make_request(
                    client,
                    "GET",
                    f"{self.api_base_url}/repos/search",
                    headers=headers,
                    params={"q": f"{query} repo:{owner}/{repo}", "limit": limit},
                )

                search_data = response.json()
                results = []

                for item in search_data.get("data", [])[:limit]:
                    results.append(
                        {
                            "name": item.get("name", ""),
                            "path": item.get("full_name", ""),
                            "description": item.get("description", ""),
                            "url": item.get("html_url", ""),
                        }
                    )

                return results

        except Exception as e:
            logger.error(f"Error searching repository in Forgejo: {str(e)}")
            raise GitServiceException(f"Failed to search repository: {str(e)}")

    def get_async_client(self) -> httpx.AsyncClient:
        """Get async HTTP client with authentication headers."""
        headers = self._get_default_headers()
        return httpx.AsyncClient(headers=headers, timeout=30.0)

    async def create_issue(
        self,
        repository: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create an issue in the specified repository.

        Args:
            repository: Repository name in format "owner/repo"
            title: Issue title
            body: Issue description/body
            labels: List of label names (optional)
            assignees: List of usernames to assign (optional)

        Returns:
            Dict containing issue information

        Raises:
            GitServiceException: If creation fails
            NotFoundException: If repository not found
            UnauthorizedException: If authentication fails
        """
        if "/" not in repository:
            raise ValueError(
                f"Repository must be in 'owner/repo' format, got: {repository}"
            )

        owner, repo = repository.split("/", 1)

        # Prepare issue data
        issue_data: Dict[str, Any] = {
            "title": title,
            "body": body,
        }

        if labels:
            issue_data["labels"] = labels

        if assignees:
            issue_data["assignees"] = assignees

        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                url = f"{self.api_base_url}/repos/{owner}/{repo}/issues"
                response = await self._make_request(
                    client, "POST", url, headers=headers, json=issue_data
                )

                if response.status_code == 201:
                    return response.json()
                elif response.status_code == 404:
                    raise NotFoundException(f"Repository {repository} not found")
                elif response.status_code == 401:
                    raise UnauthorizedException("Authentication failed")
                else:
                    raise GitServiceException(
                        f"Failed to create issue: HTTP {response.status_code} - {response.text}"
                    )

        except (NotFoundException, UnauthorizedException, GitServiceException):
            raise
        except Exception as e:
            raise GitServiceException(f"Error creating issue: {str(e)}")
