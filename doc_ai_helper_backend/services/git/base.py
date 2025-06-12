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

    def __init__(self, access_token: Optional[str] = None):
        """Initialize Git service.

        Args:
            access_token: Access token for the Git service
        """
        self.access_token = access_token
        self.service_name = self._get_service_name()

    @abc.abstractmethod
    def _get_service_name(self) -> str:
        """Get service name.

        Returns:
            str: Service name
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

    def build_document_response(
        self,
        owner: str,
        repo: str,
        path: str,
        ref: str,
        content: str,
        metadata: Dict[str, Any],
    ) -> DocumentResponse:
        """Build document response.

        Args:
            owner: Repository owner
            repo: Repository name
            path: Document path
            ref: Branch or tag name
            content: Document content
            metadata: Document metadata

        Returns:
            DocumentResponse: Document response
        """
        # Extract file name from path
        name = path.split("/")[-1]

        # Detect document type
        doc_type = self.detect_document_type(path)

        # Build document metadata
        doc_metadata = DocumentMetadata(
            size=metadata.get("size", 0),
            last_modified=metadata.get("last_modified", datetime.utcnow()),
            content_type=metadata.get("content_type", "text/plain"),
            sha=metadata.get("sha"),
            download_url=metadata.get("download_url"),
            html_url=metadata.get("html_url"),
            raw_url=metadata.get("raw_url"),
            extra=metadata.get("extra", {}),
        )

        # Build document content
        doc_content = DocumentContent(
            content=content,
            encoding=metadata.get("encoding", "utf-8"),
        )

        # Build full document response
        return DocumentResponse(
            path=path,
            name=name,
            type=doc_type,
            metadata=doc_metadata,
            content=doc_content,
            repository=repo,
            owner=owner,
            service=self.service_name,
            ref=ref,
        )
