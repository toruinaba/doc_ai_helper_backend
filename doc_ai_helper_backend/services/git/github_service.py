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
)
from doc_ai_helper_backend.models.document import (
    DocumentResponse,
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
