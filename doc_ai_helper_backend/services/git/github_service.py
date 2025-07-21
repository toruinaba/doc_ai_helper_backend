"""
GitHub service implementation.
"""

import base64
from datetime import datetime
import logging
from typing import Any, Dict, List, Optional, Tuple

import httpx
from pydantic import HttpUrl

from doc_ai_helper_backend.core.exceptions import (
    GitServiceException,
    NotFoundException,
    RateLimitException,
    UnauthorizedException,
    GitHubAPIError,
    GitHubAuthError,
    GitHubRateLimitError,
    GitHubRepositoryNotFoundError,
    GitHubPermissionError,
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

# GitHub API base URL
GITHUB_API_BASE_URL = "https://api.github.com"


class GitHubService(GitServiceBase):
    """GitHub service implementation."""

    def __init__(self, access_token: Optional[str] = None):
        """Initialize GitHub service.

        Args:
            access_token: GitHub access token
        """
        super().__init__(access_token=access_token)
        self.headers = self._build_headers()

    def _get_service_name(self) -> str:
        """Get service name.

        Returns:
            str: Service name
        """
        return "github"

    def _build_headers(self) -> Dict[str, str]:
        """Build HTTP headers for GitHub API requests.

        Returns:
            Dict[str, str]: HTTP headers
        """
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "DocAIHelperBackend",
        }

        if self.access_token:
            headers["Authorization"] = f"token {self.access_token}"

        return headers

    async def _make_request(
        self, method: str, url: str, **kwargs
    ) -> Tuple[Dict[str, Any], Dict[str, str]]:
        """Make HTTP request to GitHub API.

        Args:
            method: HTTP method
            url: URL
            **kwargs: Additional arguments for httpx client

        Returns:
            Tuple[Dict[str, Any], Dict[str, str]]: Response data and headers

        Raises:
            GitServiceException: If there is an error with the GitHub API
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
            NotFoundException: If resource is not found
        """
        async with httpx.AsyncClient() as client:
            try:
                # Merge headers with any provided in kwargs
                headers = kwargs.pop("headers", {})
                all_headers = {**self.headers, **headers}

                # Make the request
                response = await client.request(
                    method, url, headers=all_headers, **kwargs
                )

                # Check for rate limit
                remaining = int(response.headers.get("X-RateLimit-Remaining", "1"))
                if remaining == 0:
                    reset_time = int(response.headers.get("X-RateLimit-Reset", "0"))
                    reset_datetime = datetime.fromtimestamp(reset_time)
                    raise RateLimitException(
                        f"GitHub API rate limit exceeded. Resets at {reset_datetime}."
                    )

                # Handle response status
                if response.status_code == 404:
                    # Extract repository name from URL for better error reporting
                    if "/repos/" in url:
                        repo_path = url.split('/repos/')[1].split('/')[0:2]
                        if len(repo_path) >= 2:
                            repo_name = f"{repo_path[0]}/{repo_path[1]}"
                            # Check if response indicates repo not found
                            response_text = response.text.lower()
                            if "not found" in response_text or response.status_code == 404:
                                raise GitHubRepositoryNotFoundError(repo_name)
                    # Default to generic not found
                    raise NotFoundException("Resource not found on GitHub.")
                elif response.status_code == 401:
                    raise UnauthorizedException("Unauthorized access to GitHub API.")
                elif response.status_code == 403:
                    # Could be rate limit or other access issue
                    if "rate limit" in response.text.lower():
                        raise RateLimitException("GitHub API rate limit exceeded.")
                    else:
                        raise UnauthorizedException("Forbidden access to GitHub API.")
                elif response.status_code >= 400:
                    raise GitServiceException(
                        f"GitHub API error: {response.status_code} - {response.text}"
                    )

                # Return response data and headers
                return response.json(), response.headers

            except (GitHubRepositoryNotFoundError, GitHubAPIError, GitHubAuthError, 
                    GitHubRateLimitError, GitHubPermissionError, NotFoundException, 
                    UnauthorizedException, RateLimitException) as e:
                # Re-raise GitHub-specific exceptions without wrapping
                raise
            except httpx.HTTPStatusError as e:
                raise GitServiceException(f"HTTP error: {str(e)}")
            except httpx.RequestError as e:
                raise GitServiceException(f"Request error: {str(e)}")
            except Exception as e:
                raise GitServiceException(f"Unexpected error: {str(e)}")

    async def get_document(
        self, owner: str, repo: str, path: str, ref: str = "main"
    ) -> DocumentResponse:
        """Get document from a GitHub repository.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Document path
            ref: Branch or tag name. Default is "main"

        Returns:
            DocumentResponse: Document data

        Raises:
            NotFoundException: If document is not found
            GitServiceException: If there is an error with the GitHub API
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/contents/{path}"
        params = {"ref": ref}

        try:
            # Get file data from GitHub
            data, headers = await self._make_request("GET", url, params=params)

            # If data is a list, it means the path is a directory
            if isinstance(data, list):
                raise NotFoundException(f"Path {path} is a directory, not a file.")

            # Get file content
            content = ""
            if data.get("encoding") == "base64" and data.get("content"):
                # Decode content from base64
                content = base64.b64decode(data["content"]).decode("utf-8")
            else:
                # Handle other encodings or empty content
                logger.warning(f"Unexpected content encoding: {data.get('encoding')}")
                content = data.get("content", "")

            # Build metadata
            metadata = {
                "size": data.get("size", 0),
                "last_modified": (
                    datetime.strptime(
                        headers.get("Last-Modified", ""), "%a, %d %b %Y %H:%M:%S %Z"
                    )
                    if "Last-Modified" in headers
                    else datetime.utcnow()
                ),
                "content_type": headers.get("Content-Type", "application/octet-stream"),
                "sha": data.get("sha"),
                "download_url": data.get("download_url"),
                "html_url": data.get("html_url"),
                "raw_url": data.get(
                    "download_url"
                ),  # GitHub uses download_url for raw content
                "encoding": data.get("encoding", "utf-8"),
                "extra": {
                    "git_url": data.get("git_url"),
                    "url": data.get("url"),
                    "type": data.get("type"),
                },
            }

            # Build and return document response
            return self.build_document_response(
                owner=owner,
                repo=repo,
                path=path,
                ref=ref,
                content=content,
                metadata=metadata,
            )

        except GitHubRepositoryNotFoundError as e:
            raise e
        except NotFoundException as e:
            raise NotFoundException(f"Document not found: {path}")
        except (UnauthorizedException, RateLimitException) as e:
            raise e
        except Exception as e:
            raise GitServiceException(f"Error getting document from GitHub: {str(e)}")

    async def get_repository_structure(
        self, owner: str, repo: str, ref: str = "main", path: str = ""
    ) -> RepositoryStructureResponse:
        """Get GitHub repository structure.

        Args:
            owner: Repository owner
            repo: Repository name
            ref: Branch or tag name. Default is "main"
            path: Path prefix to filter by. Default is ""

        Returns:
            RepositoryStructureResponse: Repository structure data

        Raises:
            NotFoundException: If repository is not found
            GitServiceException: If there is an error with the GitHub API
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        # Use the recursive tree API to get the repository structure
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/git/trees/{ref}"
        params = {"recursive": "1"}  # Get the full tree recursively

        try:
            # Get repository tree from GitHub
            data, headers = await self._make_request("GET", url, params=params)

            # Extract tree items
            tree_items = []
            for item in data.get("tree", []):
                # Skip items that don't match the path prefix if provided
                if path and not item["path"].startswith(path):
                    continue

                # Create FileTreeItem
                tree_items.append(
                    FileTreeItem(
                        path=item["path"],
                        name=item["path"].split("/")[-1],
                        type="file" if item["type"] == "blob" else "directory",
                        size=item.get("size"),
                        sha=item.get("sha"),
                        download_url=(
                            f"https://raw.githubusercontent.com/{owner}/{repo}/{ref}/{item['path']}"
                            if item["type"] == "blob"
                            else None
                        ),
                        html_url=(
                            f"https://github.com/{owner}/{repo}/blob/{ref}/{item['path']}"
                            if item["type"] == "blob"
                            else f"https://github.com/{owner}/{repo}/tree/{ref}/{item['path']}"
                        ),
                        git_url=item.get("url"),
                    )
                )

            # Build response
            return RepositoryStructureResponse(
                service=self.service_name,
                owner=owner,
                repo=repo,
                ref=ref,
                tree=tree_items,
                last_updated=datetime.utcnow(),
            )

        except GitHubRepositoryNotFoundError as e:
            raise e
        except NotFoundException as e:
            raise NotFoundException(f"Repository not found: {owner}/{repo}")
        except (UnauthorizedException, RateLimitException) as e:
            raise e
        except Exception as e:
            raise GitServiceException(
                f"Error getting repository structure from GitHub: {str(e)}"
            )

    async def search_repository(
        self, owner: str, repo: str, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Search GitHub repository.

        Args:
            owner: Repository owner
            repo: Repository name
            query: Search query
            limit: Maximum number of results. Default is 10

        Returns:
            List[Dict[str, Any]]: Search results

        Raises:
            NotFoundException: If repository is not found
            GitServiceException: If there is an error with the GitHub API
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        # Use GitHub's code search API
        url = f"{GITHUB_API_BASE_URL}/search/code"

        # Build query string: search in the specific repo
        query_string = f"{query} repo:{owner}/{repo}"

        params = {
            "q": query_string,
            "per_page": min(limit, 100),  # GitHub has a max of 100 per page
        }

        try:
            # Get search results from GitHub
            data, _ = await self._make_request("GET", url, params=params)

            # Extract search results
            results = []
            for item in data.get("items", [])[:limit]:
                result = {
                    "path": item.get("path", ""),
                    "name": item.get("name", ""),
                    "html_url": item.get("html_url", ""),
                    "repository": {
                        "name": item.get("repository", {}).get("name", ""),
                        "owner": item.get("repository", {})
                        .get("owner", {})
                        .get("login", ""),
                    },
                    "score": item.get("score", 0),
                }
                results.append(result)

            return results

        except NotFoundException as e:
            raise NotFoundException(f"Repository not found: {owner}/{repo}")
        except (UnauthorizedException, RateLimitException) as e:
            raise e
        except Exception as e:
            raise GitServiceException(f"Error searching GitHub repository: {str(e)}")

    async def check_repository_exists(self, owner: str, repo: str) -> bool:
        """Check if GitHub repository exists.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            bool: True if repository exists, False otherwise

        Raises:
            GitServiceException: If there is an error with the GitHub API
            UnauthorizedException: If access is unauthorized
            RateLimitException: If rate limit is exceeded
        """
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"

        try:
            # Try to get repository info
            await self._make_request("GET", url)
            return True
        except NotFoundException:
            return False
        except (UnauthorizedException, RateLimitException) as e:
            raise e
        except Exception as e:
            raise GitServiceException(
                f"Error checking if GitHub repository exists: {str(e)}"
            )

    def get_supported_auth_methods(self) -> List[str]:
        """Get supported authentication methods for GitHub.

        Returns:
            List[str]: List of supported authentication methods
        """
        return ["token", "oauth"]

    async def authenticate(self) -> bool:
        """Test authentication with GitHub API.

        Returns:
            bool: True if authentication is successful, False otherwise

        Raises:
            UnauthorizedException: If authentication fails
            GitServiceException: If there is an error with the GitHub API
        """
        if not self.access_token:
            return False

        url = f"{GITHUB_API_BASE_URL}/user"

        try:
            await self._make_request("GET", url)
            return True
        except UnauthorizedException:
            return False
        except Exception as e:
            raise GitServiceException(f"Error testing GitHub authentication: {str(e)}")

    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get GitHub API rate limit information.

        Returns:
            Dict[str, Any]: Rate limit information including current usage and limits

        Raises:
            GitServiceException: If there is an error with the GitHub API
            UnauthorizedException: If access is unauthorized
        """
        url = f"{GITHUB_API_BASE_URL}/rate_limit"

        try:
            data, headers = await self._make_request("GET", url)
            return {
                "service": "github",
                "rate_limit": data.get("rate", {}),
                "remaining": int(headers.get("X-RateLimit-Remaining", "0")),
                "reset_time": int(headers.get("X-RateLimit-Reset", "0")),
            }
        except Exception as e:
            raise GitServiceException(f"Error getting GitHub rate limit: {str(e)}")

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to GitHub API.

        Returns:
            Dict[str, Any]: Connection test results including status and service info

        Raises:
            GitServiceException: If connection test fails
        """
        try:
            auth_success = await self.authenticate()
            rate_limit_info = await self.get_rate_limit_info()

            return {
                "service": "github",
                "status": "success",
                "authenticated": auth_success,
                "rate_limit": rate_limit_info,
                "api_url": GITHUB_API_BASE_URL,
            }
        except Exception as e:
            return {
                "service": "github",
                "status": "error",
                "error": str(e),
                "authenticated": False,
            }

    def build_document_response(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> DocumentResponse:
        """Build a DocumentResponse from GitHub API data."""
        from doc_ai_helper_backend.services.document.processors.factory import (
            DocumentProcessorFactory,
        )

        # Detect document type
        document_type = self.detect_document_type(path)

        # Process document
        processor = DocumentProcessorFactory.create(document_type)
        document_content = processor.process_content(content, path)

        # Convert metadata to DocumentMetadata
        document_metadata = DocumentMetadata(
            size=metadata.get("size", len(content)),
            last_modified=datetime.utcnow(),
            content_type=(
                "text/markdown"
                if document_type == DocumentType.MARKDOWN
                else "text/plain"
            ),
            sha=metadata.get("sha"),
            download_url=metadata.get("download_url"),
            html_url=metadata.get("html_url"),
            raw_url=metadata.get("download_url"),
            extra=metadata.get("extra", {}),
        )

        return DocumentResponse(
            path=path,
            name=path.split("/")[-1],
            type=document_type,
            content=document_content,
            metadata=document_metadata,
            repository=repo,
            owner=owner,
            service="github",
            ref=ref,
            links=processor.extract_links(content, path),
        )

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

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """
        Get repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Repository information.
        """
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"
        data, _ = await self._make_request("GET", url)
        return data

    async def check_repository_permissions(
        self, owner: str, repo: str
    ) -> Dict[str, bool]:
        """
        Check permissions for a repository.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Dictionary with permission flags.
        """
        try:
            repo_info = await self.get_repository_info(owner, repo)
            permissions = repo_info.get("permissions", {})

            return {
                "read": permissions.get("pull", False),
                "write": permissions.get("push", False),
                "admin": permissions.get("admin", False),
                "issues": repo_info.get("has_issues", False),
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

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create an issue in the repository.

        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body/description
            labels: List of label names
            assignees: List of GitHub usernames to assign

        Returns:
            Created issue information.

        Raises:
            GitServiceException: If there is an error creating the issue
            UnauthorizedException: If access is unauthorized
            NotFoundException: If repository is not found
        """
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/issues"

        issue_data = {
            "title": title,
            "body": body,
        }

        if labels:
            issue_data["labels"] = labels
        if assignees:
            issue_data["assignees"] = assignees

        logger.info(f"Creating issue in {owner}/{repo}: {title}")
        logger.debug(f"Issue data payload: {issue_data}")
        logger.debug(f"GitHub API URL: {url}")

        try:
            data, headers = await self._make_request("POST", url, json=issue_data)
            logger.info(f"GitHub API response status: SUCCESS")
            logger.info(f"Created issue #{data.get('number', 'N/A')}: {data.get('html_url', 'N/A')}")
            logger.debug(f"Full GitHub API response: {data}")
            logger.debug(f"Response headers: {dict(headers)}")
            return data
        except Exception as e:
            logger.error(f"Failed to create issue in {owner}/{repo}: {str(e)}")
            logger.error(f"Error type: {type(e).__name__}")
            raise

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
            draft: Whether to create as draft PR

        Returns:
            Created pull request information.

        Raises:
            GitServiceException: If there is an error creating the PR
            UnauthorizedException: If access is unauthorized
            NotFoundException: If repository is not found
        """
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/pulls"

        pr_data = {
            "title": title,
            "body": body,
            "head": head_branch,
            "base": base_branch,
            "draft": draft,
        }

        logger.info(f"Creating pull request in {owner}/{repo}: {title}")

        try:
            data, _ = await self._make_request("POST", url, json=pr_data)
            return data
        except Exception as e:
            logger.error(f"Failed to create pull request in {owner}/{repo}: {str(e)}")
            raise

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
        owner, repo = self._parse_repository(repository)
        return await self.create_pull_request(
            owner, repo, title, body, head_branch, base_branch, draft
        )
