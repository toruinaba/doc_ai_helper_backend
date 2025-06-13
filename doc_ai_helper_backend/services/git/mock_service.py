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
from doc_ai_helper_backend.models.document import (
    DocumentResponse,
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
        self.documents = documents or DEFAULT_DOCUMENTS
        self.structures = structures or DEFAULT_STRUCTURES
        self.search_results = search_results or DEFAULT_SEARCH_RESULTS
        self.existing_repos = existing_repos or DEFAULT_EXISTING_REPOS
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


# Default mock data
DEFAULT_DOCUMENTS = {
    "octocat/Hello-World/README.md@main": {
        "content": "# Hello World\n\nThis is a sample repository.",
        "metadata": {
            "size": 42,
            "last_modified": datetime(2023, 1, 1, 12, 0, 0),
            "content_type": "text/markdown",
            "sha": "abcdef1234567890",
            "download_url": "https://raw.githubusercontent.com/octocat/Hello-World/main/README.md",
            "html_url": "https://github.com/octocat/Hello-World/blob/main/README.md",
            "raw_url": "https://raw.githubusercontent.com/octocat/Hello-World/main/README.md",
            "encoding": "utf-8",
        },
    },
    "octocat/Hello-World/docs/index.md@main": {
        "content": "# Documentation\n\nThis is the main documentation page.",
        "metadata": {
            "size": 47,
            "last_modified": datetime(2023, 1, 2, 12, 0, 0),
            "content_type": "text/markdown",
            "sha": "1234567890abcdef",
            "download_url": "https://raw.githubusercontent.com/octocat/Hello-World/main/docs/index.md",
            "html_url": "https://github.com/octocat/Hello-World/blob/main/docs/index.md",
            "raw_url": "https://raw.githubusercontent.com/octocat/Hello-World/main/docs/index.md",
            "encoding": "utf-8",
        },
    },
}

DEFAULT_STRUCTURES = {
    "octocat/Hello-World@main": {
        "tree": [
            {
                "path": "README.md",
                "name": "README.md",
                "type": "file",
                "size": 42,
                "sha": "abcdef1234567890",
                "download_url": "https://raw.githubusercontent.com/octocat/Hello-World/main/README.md",
                "html_url": "https://github.com/octocat/Hello-World/blob/main/README.md",
                "git_url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/abcdef1234567890",
            },
            {
                "path": "docs",
                "name": "docs",
                "type": "directory",
                "size": None,
                "sha": "0987654321fedcba",
                "download_url": None,
                "html_url": "https://github.com/octocat/Hello-World/tree/main/docs",
                "git_url": None,
            },
            {
                "path": "docs/index.md",
                "name": "index.md",
                "type": "file",
                "size": 47,
                "sha": "1234567890abcdef",
                "download_url": "https://raw.githubusercontent.com/octocat/Hello-World/main/docs/index.md",
                "html_url": "https://github.com/octocat/Hello-World/blob/main/docs/index.md",
                "git_url": "https://api.github.com/repos/octocat/Hello-World/git/blobs/1234567890abcdef",
            },
        ],
        "last_updated": datetime(2023, 1, 3, 12, 0, 0),
    }
}

DEFAULT_SEARCH_RESULTS = {
    "octocat/Hello-World:documentation": {
        "results": [
            {
                "path": "docs/index.md",
                "name": "index.md",
                "html_url": "https://github.com/octocat/Hello-World/blob/main/docs/index.md",
                "score": 0.9,
                "highlight": "This is the main <em>documentation</em> page.",
                "repository": {
                    "name": "Hello-World",
                    "owner": "octocat",
                },
            },
            {
                "path": "README.md",
                "name": "README.md",
                "html_url": "https://github.com/octocat/Hello-World/blob/main/README.md",
                "score": 0.5,
                "highlight": "This is a sample repository with <em>documentation</em>.",
                "repository": {
                    "name": "Hello-World",
                    "owner": "octocat",
                },
            },
        ]
    }
}

DEFAULT_EXISTING_REPOS = ["octocat/Hello-World"]
