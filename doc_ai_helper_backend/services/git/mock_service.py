"""
Mock Git service for regular use.

This module provides a mock implementation of the GitServiceBase
that can be used for development, testing, and demos without
requiring actual Git service credentials.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from doc_ai_helper_backend.core.exceptions import (
    GitServiceException,
    NotFoundException,
)
from doc_ai_helper_backend.services.git.mock_data import (
    EXTENDED_DOCUMENTS,
    EXTENDED_STRUCTURES,
    EXTENDED_SEARCH_RESULTS,
    EXTENDED_EXISTING_REPOS,
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


class MockGitService(GitServiceBase):
    """Mock Git service implementation.

    This service provides mock data for development, testing and demos
    without requiring actual Git service credentials.
    """

    def __init__(
        self,
        access_token: Optional[str] = None,
        documents: Optional[Dict[str, Dict[str, Any]]] = None,
        structures: Optional[Dict[str, Dict[str, Any]]] = None,
        search_results: Optional[Dict[str, List[Dict[str, Any]]]] = None,
        existing_repos: Optional[List[str]] = None,
    ):
        """Initialize mock Git service.

        Args:
            access_token: Access token for the Git service (not used in mock)
            documents: Pre-defined documents to return, keyed by {owner}/{repo}/{path}@{ref}
            structures: Pre-defined repository structures to return, keyed by {owner}/{repo}@{ref}
            search_results: Pre-defined search results to return, keyed by {owner}/{repo}:{query}
            existing_repos: List of existing repositories in format "{owner}/{repo}"
        """
        self.documents = documents or EXTENDED_DOCUMENTS
        self.structures = structures or EXTENDED_STRUCTURES
        self.search_results = search_results or EXTENDED_SEARCH_RESULTS
        self.existing_repos = existing_repos or EXTENDED_EXISTING_REPOS
        super().__init__(access_token=access_token)

    def _get_service_name(self) -> str:
        """Get service name.

        Returns:
            str: Service name
        """
        return "mock"

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
        """
        # Check if repository exists
        repo_path = f"{owner}/{repo}"
        if repo_path not in self.existing_repos and self.existing_repos:
            raise NotFoundException(f"Repository not found: {repo_path}")

        # Build document key
        doc_key = f"{owner}/{repo}/{path}@{ref}"

        # Check if document exists in mock data
        if doc_key not in self.documents:
            # If no specific document found, try fallback to any document with matching path
            fallback_key = None
            for key in self.documents:
                if key.startswith(f"{owner}/{repo}/{path}@"):
                    fallback_key = key
                    break

            if fallback_key:
                doc_key = fallback_key
            else:
                raise NotFoundException(f"Document not found: {path}")

        # Get document data
        doc_data = self.documents[doc_key]

        # Extract content and metadata
        content = doc_data.get("content", f"Mock content for {path}")
        metadata = doc_data.get(
            "metadata",
            {
                "size": 100,
                "last_modified": datetime.utcnow(),
                "content_type": "text/markdown",
                "sha": "abcdef1234567890",
                "download_url": f"https://example.com/{owner}/{repo}/{path}",
                "html_url": f"https://example.com/{owner}/{repo}/blob/{ref}/{path}",
                "raw_url": f"https://example.com/{owner}/{repo}/raw/{ref}/{path}",
                "encoding": "utf-8",
            },
        )
        # Build and return document response
        return self.build_document_response(
            owner=owner,
            repo=repo,
            path=path,
            ref=ref,
            content=content,
            metadata=metadata,
        )

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
        """
        # Check if repository exists
        repo_path = f"{owner}/{repo}"
        if repo_path not in self.existing_repos and self.existing_repos:
            raise NotFoundException(f"Repository not found: {repo_path}")

        # Build structure key
        structure_key = f"{owner}/{repo}@{ref}"
        if path:
            structure_key = f"{structure_key}:{path}"

        # Check if structure exists in mock data
        if structure_key not in self.structures:
            # If no specific structure found, try fallback to any structure for the repo
            fallback_key = None
            for key in self.structures:
                if key.startswith(f"{owner}/{repo}@"):
                    fallback_key = key
                    break

            if fallback_key:
                structure_key = fallback_key
            else:
                # Generate a default structure if none found
                tree_items = [
                    FileTreeItem(
                        path="README.md",
                        name="README.md",
                        type="file",
                        size=100,
                        sha="abcdef1234567890",
                        download_url=f"https://example.com/{owner}/{repo}/raw/{ref}/README.md",
                        html_url=f"https://example.com/{owner}/{repo}/blob/{ref}/README.md",
                        git_url=f"https://example.com/api/v3/repos/{owner}/{repo}/git/blobs/abcdef1234567890",
                    ),
                    FileTreeItem(
                        path="docs",
                        name="docs",
                        type="directory",
                        size=None,
                        sha="1234567890abcdef",
                        download_url=None,
                        html_url=f"https://example.com/{owner}/{repo}/tree/{ref}/docs",
                        git_url=None,
                    ),
                    FileTreeItem(
                        path="docs/index.md",
                        name="index.md",
                        type="file",
                        size=200,
                        sha="0987654321abcdef",
                        download_url=f"https://example.com/{owner}/{repo}/raw/{ref}/docs/index.md",
                        html_url=f"https://example.com/{owner}/{repo}/blob/{ref}/docs/index.md",
                        git_url=f"https://example.com/api/v3/repos/{owner}/{repo}/git/blobs/0987654321abcdef",
                    ),
                ]

                # Filter by path if provided
                if path:
                    tree_items = [
                        item for item in tree_items if item.path.startswith(path)
                    ]

                return RepositoryStructureResponse(
                    service=self.service_name,
                    owner=owner,
                    repo=repo,
                    ref=ref,
                    tree=tree_items,
                    last_updated=datetime.utcnow(),
                )

        # Get structure data
        structure_data = self.structures[structure_key]

        # Get tree items
        tree_items = structure_data.get("tree", [])
        if (
            isinstance(tree_items, list)
            and tree_items
            and not isinstance(tree_items[0], FileTreeItem)
        ):
            # Convert dict items to FileTreeItem objects if needed
            tree_items = [
                FileTreeItem(**item) if isinstance(item, dict) else item
                for item in tree_items
            ]

        # Build and return repository structure response
        return RepositoryStructureResponse(
            service=self.service_name,
            owner=owner,
            repo=repo,
            ref=ref,
            tree=tree_items,
            last_updated=structure_data.get("last_updated", datetime.utcnow()),
        )

    async def search_repository(
        self, owner: str, repo: str, query: str, limit: int = 10
    ) -> Dict[str, Any]:
        """Search repository.

        Args:
            owner: Repository owner
            repo: Repository name
            query: Search query
            limit: Maximum number of results. Default is 10

        Returns:
            Dict[str, Any]: Search results

        Raises:
            NotFoundException: If repository is not found
            GitServiceException: If there is an error with the Git service
        """
        # Check if repository exists
        repo_path = f"{owner}/{repo}"
        if repo_path not in self.existing_repos and self.existing_repos:
            raise NotFoundException(f"Repository not found: {repo_path}")

        # Build search key
        search_key = f"{owner}/{repo}:{query}"

        # Check if search results exist in mock data
        if search_key not in self.search_results:
            # If no specific results found, try fallback to any results for the repo
            fallback_key = None
            for key in self.search_results:
                if key.startswith(f"{owner}/{repo}:"):
                    fallback_key = key
                    break

            if fallback_key:
                search_key = fallback_key
            else:
                # Return empty results if none found
                return {"results": []}

        # Get search results
        search_data = self.search_results.get(search_key, {"results": []})

        # Get results list and apply limit
        results_list = search_data["results"][:limit]

        return {"results": results_list}

    async def check_repository_exists(self, owner: str, repo: str) -> bool:
        """Check if repository exists.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            bool: True if repository exists, False otherwise
        """
        repo_path = f"{owner}/{repo}"
        if not self.existing_repos:
            # If no existing repos are defined, assume all repos exist
            return True
        return repo_path in self.existing_repos

    def get_supported_auth_methods(self) -> List[str]:
        """Get supported authentication methods for Mock service.

        Returns:
            List[str]: List of supported authentication methods
        """
        return ["token", "none"]

    async def authenticate(self) -> bool:
        """Test authentication with Mock service.

        Returns:
            bool: Always returns True for mock service

        Raises:
            UnauthorizedException: Never raised in mock service
            GitServiceException: Never raised in mock service
        """
        return True

    async def get_rate_limit_info(self) -> Dict[str, Any]:
        """Get Mock service rate limit information.

        Returns:
            Dict[str, Any]: Mock rate limit information

        Raises:
            GitServiceException: Never raised in mock service
            UnauthorizedException: Never raised in mock service
        """
        return {
            "service": "mock",
            "rate_limit": {
                "limit": 5000,
                "used": 100,
                "remaining": 4900,
            },
            "remaining": 4900,
            "reset_time": 3600,
        }

    async def test_connection(self) -> Dict[str, Any]:
        """Test connection to Mock service.

        Returns:
            Dict[str, Any]: Connection test results - always successful

        Raises:
            GitServiceException: Never raised in mock service
        """
        return {
            "service": "mock",
            "status": "success",
            "authenticated": True,
            "rate_limit": await self.get_rate_limit_info(),
            "api_url": "mock://localhost",
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
        """Build a DocumentResponse from mock data."""
        from doc_ai_helper_backend.services.document_processors.factory import (
            DocumentProcessorFactory,
        )

        # Detect document type
        document_type = self.detect_document_type(path)

        # Process document
        processor = DocumentProcessorFactory.create(document_type)

        # Convert metadata to DocumentMetadata
        document_metadata = DocumentMetadata(
            size=metadata.get("size", len(content)),
            last_modified=metadata.get("last_modified", datetime.utcnow()),
            content_type=metadata.get(
                "content_type",
                (
                    "text/markdown"
                    if document_type == DocumentType.MARKDOWN
                    else "text/plain"
                ),
            ),
            sha=metadata.get("sha"),
            download_url=metadata.get("download_url"),
            html_url=metadata.get("html_url"),
            raw_url=metadata.get("raw_url"),
            extra=metadata.get("extra", {}),
        )

        return DocumentResponse(
            path=path,
            name=path.split("/")[-1],
            type=document_type,
            content=DocumentContent(content=content),
            metadata=document_metadata,
            repository=repo,
            owner=owner,
            service="mock",
            ref=ref,
            links=processor.extract_links(content, path),
        )

    async def create_issue(
        self,
        owner: str,
        repo: str,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Create a mock issue.

        Args:
            owner: Repository owner
            repo: Repository name
            title: Issue title
            body: Issue body/description
            labels: List of label names
            assignees: List of usernames to assign

        Returns:
            Mock issue information
        """
        # Check if repository exists
        repo_key = f"{owner}/{repo}"
        if repo_key not in self.existing_repos:
            raise NotFoundException(f"Repository {repo_key} not found")

        issue_id = 123  # Mock issue ID
        return {
            "id": issue_id,
            "number": issue_id,
            "title": title,
            "body": body,
            "state": "open",
            "html_url": f"https://github.com/{owner}/{repo}/issues/{issue_id}",
            "labels": [{"name": label} for label in (labels or [])],
            "assignees": [{"login": assignee} for assignee in (assignees or [])],
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

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
        """Create a mock pull request.

        Args:
            owner: Repository owner
            repo: Repository name
            title: PR title
            body: PR description
            head_branch: Source branch name
            base_branch: Target branch name
            draft: Whether to create as draft PR

        Returns:
            Mock pull request information
        """
        # Check if repository exists
        repo_key = f"{owner}/{repo}"
        if repo_key not in self.existing_repos:
            raise NotFoundException(f"Repository {repo_key} not found")

        pr_id = 456  # Mock PR ID
        return {
            "id": pr_id,
            "number": pr_id,
            "title": title,
            "body": body,
            "state": "open",
            "draft": draft,
            "head": {"ref": head_branch},
            "base": {"ref": base_branch},
            "html_url": f"https://github.com/{owner}/{repo}/pull/{pr_id}",
            "diff_url": f"https://github.com/{owner}/{repo}/pull/{pr_id}.diff",
            "patch_url": f"https://github.com/{owner}/{repo}/pull/{pr_id}.patch",
            "created_at": datetime.utcnow().isoformat(),
            "updated_at": datetime.utcnow().isoformat(),
        }

    async def check_repository_permissions(
        self, owner: str, repo: str
    ) -> Dict[str, Any]:
        """Check mock repository permissions.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Mock permission information
        """
        repo_key = f"{owner}/{repo}"
        if repo_key not in self.existing_repos:
            raise NotFoundException(f"Repository {repo_key} not found")

        return {
            "admin": True,
            "push": True,
            "pull": True,
            "write": True,
            "read": True,
            "issues": True,
            "pull_requests": True,
        }

    async def get_repository_info(self, owner: str, repo: str) -> Dict[str, Any]:
        """Get mock repository information.

        Args:
            owner: Repository owner
            repo: Repository name

        Returns:
            Mock repository information
        """
        repo_key = f"{owner}/{repo}"
        if repo_key not in self.existing_repos:
            raise NotFoundException(f"Repository {repo_key} not found")

        return {
            "id": 12345,
            "name": repo,
            "full_name": repo_key,
            "owner": {"login": owner},
            "description": f"Mock repository for {repo_key}",
            "private": False,
            "html_url": f"https://github.com/{repo_key}",
            "clone_url": f"https://github.com/{repo_key}.git",
            "default_branch": "main",
            "created_at": "2023-01-01T00:00:00Z",
            "updated_at": datetime.utcnow().isoformat(),
            "stargazers_count": 42,
            "watchers_count": 10,
            "forks_count": 5,
            "open_issues_count": 3,
        }
