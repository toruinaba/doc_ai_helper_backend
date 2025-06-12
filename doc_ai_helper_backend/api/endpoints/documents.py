"""
Document-related API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query

from doc_ai_helper_backend.core.exceptions import NotFoundException
from doc_ai_helper_backend.models.document import DocumentResponse, RepositoryStructureResponse

# Logger
logger = logging.getLogger("doc_ai_helper")

# Router
router = APIRouter(tags=["documents"])


@router.get(
    "/{service}/{owner}/{repo}/{path:path}",
    response_model=DocumentResponse,
    summary="Get document",
    description="Get document from a Git repository",
)
async def get_document(
    service: str = Path(..., description="Git service (github, gitlab, etc.)"),
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    path: str = Path(..., description="Document path"),
    ref: Optional[str] = Query(default="main", description="Branch or tag name"),
):
    """
    Get document from a Git repository.

    Args:
        service: Git service type (github, gitlab, etc.)
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
    # This is a placeholder for actual implementation
    # In a real implementation, this would call a document service
    # which would interact with the appropriate Git service
    logger.info(f"Getting document from {service}/{owner}/{repo}/{path} at {ref}")

    # For now, we'll just raise a NotFoundException as a placeholder
    raise NotFoundException(f"Document not found: {path}")


@router.get(
    "/structure/{service}/{owner}/{repo}",
    response_model=RepositoryStructureResponse,
    summary="Get repository structure",
    description="Get structure of a Git repository",
)
async def get_repository_structure(
    service: str = Path(..., description="Git service (github, gitlab, etc.)"),
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
    ref: Optional[str] = Query(default="main", description="Branch or tag name"),
    path: Optional[str] = Query(default="", description="Path prefix to filter by"),
):
    """
    Get structure of a Git repository.

    Args:
        service: Git service type (github, gitlab, etc.)
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
    # This is a placeholder for actual implementation
    logger.info(f"Getting structure of {service}/{owner}/{repo} at {ref}, path: {path}")

    # For now, we'll just raise a NotFoundException as a placeholder
    raise NotFoundException(f"Repository not found: {owner}/{repo}")
