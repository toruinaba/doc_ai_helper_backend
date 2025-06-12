"""
Document-related API endpoints.
"""

import logging
from typing import Optional

from fastapi import APIRouter, Depends, Path, Query

from doc_ai_helper_backend.api.dependencies import get_document_service
from doc_ai_helper_backend.core.exceptions import NotFoundException
from doc_ai_helper_backend.models.document import (
    DocumentResponse,
    RepositoryStructureResponse,
)
from doc_ai_helper_backend.services.document_service import DocumentService

# Logger
logger = logging.getLogger("doc_ai_helper")

# Router
router = APIRouter(tags=["documents"])


@router.get(
    "/contents/{service}/{owner}/{repo}/{path:path}",
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
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get document from a Git repository.

    Args:
        service: Git service type (github, gitlab, etc.)
        owner: Repository owner
        repo: Repository name
        path: Document path
        ref: Branch or tag name. Default is "main"
        document_service: Document service instance

    Returns:
        DocumentResponse: Document data

    Raises:
        NotFoundException: If document is not found
        GitServiceException: If there is an error with the Git service
    """
    # Allow GitHub and Mock services only
    if service.lower() not in ["github", "mock"]:
        raise NotFoundException(f"Unsupported Git service: {service}")

    return await document_service.get_document(service, owner, repo, path, ref)


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
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Get structure of a Git repository.

    Args:
        service: Git service type (github, gitlab, etc.)
        owner: Repository owner
        repo: Repository name
        ref: Branch or tag name. Default is "main"
        path: Path prefix to filter by. Default is ""
        document_service: Document service instance

    Returns:
        RepositoryStructureResponse: Repository structure data

    Raises:
        NotFoundException: If repository is not found
        GitServiceException: If there is an error with the Git service
    """
    # Allow GitHub and Mock services only
    if service.lower() not in ["github", "mock"]:
        raise NotFoundException(f"Unsupported Git service: {service}")

    return await document_service.get_repository_structure(
        service, owner, repo, ref, path
    )
