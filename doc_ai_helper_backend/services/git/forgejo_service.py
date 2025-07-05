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
                # Import here to avoid circular import
                from doc_ai_helper_backend.services.document.processors.factory import (
                    DocumentProcessorFactory,
                )
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
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create an issue in the specified repository.

        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue description/body
            labels: List of label names (optional)
            assignees: List of usernames to assign (optional)

        Returns:
            Dict containing issue information

        Raises:
            GitServiceException: If creation fails
            UnauthorizedException: If access is unauthorized
            NotFoundException: If repository is not found
        """
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
                    raise NotFoundException(f"Repository {owner}/{repo} not found")
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

    async def create_pull_request(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a pull request in the repository.

        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head_branch: Source branch name
            base_branch: Target branch name

        Returns:
            Created pull request information.

        Raises:
            GitServiceException: If there is an error creating the PR
            UnauthorizedException: If access is unauthorized
            NotFoundException: If repository is not found
        """
        pr_data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
        }

        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                url = f"{self.api_base_url}/repos/{owner}/{repo}/pulls"
                response = await self._make_request(
                    client, "POST", url, headers=headers, json=pr_data
                )

                if response.status_code == 201:
                    return response.json()
                elif response.status_code == 404:
                    raise NotFoundException(f"Repository {owner}/{repo} not found")
                elif response.status_code == 401:
                    raise UnauthorizedException("Authentication failed")
                else:
                    raise GitServiceException(
                        f"Failed to create pull request: HTTP {response.status_code} - {response.text}"
                    )

        except (NotFoundException, UnauthorizedException, GitServiceException):
            raise
        except Exception as e:
            raise GitServiceException(f"Error creating pull request: {str(e)}")

    def _parse_repository(self, repository: str) -> Tuple[str, str]:
        """
        Parse repository string into owner and repo name.

        Args:
            repository: Repository in "owner/repo" format.

        Returns:
            Tuple of (owner, repo).

        Raises:
            ValueError: If repository format is invalid.
        """
        if "/" not in repository:
            raise ValueError(
                f"Invalid repository format: {repository}. Expected 'owner/repo'"
            )

        parts = repository.split("/")
        if len(parts) != 2 or not all(parts):
            raise ValueError(
                f"Invalid repository format: {repository}. Expected 'owner/repo'"
            )

        return parts[0], parts[1]

    # Convenience methods that take repository string
    async def create_issue_from_repository_string(
        self,
        repository: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an issue using repository string.

        Args:
            repository: Repository in "owner/repo" format
            title: Issue title
            body: Issue body/description
            labels: List of label names
            assignees: List of GitHub usernames to assign

        Returns:
            Created issue information.
        """
        owner, repo = self._parse_repository(repository)
        return await self.create_issue(owner, repo, title, body, labels, assignees)

    async def create_pull_request_from_repository_string(
        self,
        repository: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a pull request using repository string.

        Args:
            repository: Repository in "owner/repo" format
            title: PR title
            body: PR description
            head_branch: Source branch name
            base_branch: Target branch name
            draft: Whether to create as draft PR

        Returns:
            Created pull request information.
        """

    async def create_pull_request_from_repository_string(
        self,
        repository: str,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
    ) -> Dict[str, Any]:
        """
        Create a pull request using repository string.

        Args:
            repository: Repository in "owner/repo" format
            title: PR title
            body: PR description
            head_branch: Source branch name
            base_branch: Target branch name
            draft: Whether to create as draft PR

        Returns:
            Created pull request information.
        """
        owner, repo = self._parse_repository(repository)
        return await self.create_pull_request(
            owner, repo, title, body, head_branch, base_branch, draft
        )

    async def check_repository_permissions(
        self, owner: str, repo: str
    ) -> Dict[str, Any]:
        """Check repository permissions.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with permission flags

        Raises:
            GitServiceException: If there is an error checking permissions
            UnauthorizedException: If access is unauthorized
            NotFoundException: If repository is not found
        """
        try:
            repo_info = await self.get_repository_info(owner, repo)
            permissions = repo_info.get("permissions", {})

            return {
                "read": permissions.get(
                    "pull", True
                ),  # Forgejo typically allows reading
                "write": permissions.get("push", False),
                "admin": permissions.get("admin", False),
                "issues": repo_info.get("has_issues", True),
                "pull_requests": True,  # Most repos allow PRs
            }
        except NotFoundException:
            return {
                "read": False,
                "write": False,
                "admin": False,
                "issues": False,
                "pull_requests": False,
            }

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information

        Raises:
            GitServiceException: If there is an error getting repository info
            UnauthorizedException: If access is unauthorized
            NotFoundException: If repository is not found
        """
        try:
            headers = self._get_default_headers()
            async with httpx.AsyncClient() as client:
                url = f"{self.api_base_url}/repos/{owner}/{repo}"
                response = await self._make_request(client, "GET", url, headers=headers)

                if response.status_code == 200:
                    return response.json()
                elif response.status_code == 404:
                    raise NotFoundException(f"Repository {owner}/{repo} not found")
                elif response.status_code == 401:
                    raise UnauthorizedException("Authentication failed")
                else:
                    raise GitServiceException(
                        f"Failed to get repository info: HTTP {response.status_code} - {response.text}"
                    )

        except (NotFoundException, UnauthorizedException, GitServiceException):
            raise
        except Exception as e:
            raise GitServiceException(f"Error getting repository info: {str(e)}")
