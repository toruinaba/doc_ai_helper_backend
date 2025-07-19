"""
Repository management API endpoints.

Provides CRUD operations for repository management with feature flag support
and delegation pattern for RepositoryContext creation.
"""

import logging
from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ...core.config import settings
from ...core.exceptions import RepositoryServiceException
from ...api.dependencies import get_repository_service
from ...models.repository import (
    RepositoryCreate,
    RepositoryResponse,
    RepositoryUpdate,
)
from ...models.repository_context import RepositoryContext
from ...services.repository_service import RepositoryService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/repositories", tags=["repositories"])


def _check_feature_enabled():
    """Check if repository management feature is enabled."""
    if not settings.enable_repository_management:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Repository management feature is not enabled"
        )


@router.get("/", response_model=List[RepositoryResponse])
async def list_repositories(
    skip: int = 0,
    limit: int = 100,
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """
    List repositories with pagination.
    
    Args:
        skip: Number of records to skip (default: 0)
        limit: Maximum number of records to return (default: 100, max: 1000)
        repository_service: Repository service dependency
        
    Returns:
        List of repository responses
        
    Raises:
        HTTPException: If feature is disabled or operation fails
    """
    _check_feature_enabled()
    
    # Validate pagination parameters
    if skip < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Skip parameter must be non-negative"
        )
    
    if limit <= 0 or limit > 1000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Limit parameter must be between 1 and 1000"
        )
    
    try:
        repositories = await repository_service.list_repositories(skip=skip, limit=limit)
        logger.info(f"Listed {len(repositories)} repositories (skip={skip}, limit={limit})")
        return repositories
        
    except RepositoryServiceException as e:
        logger.error(f"Failed to list repositories: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error listing repositories: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.post("/", response_model=RepositoryResponse, status_code=status.HTTP_201_CREATED)
async def create_repository(
    repository_data: RepositoryCreate,
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """
    Create a new repository.
    
    Args:
        repository_data: Repository creation data
        repository_service: Repository service dependency
        
    Returns:
        Created repository response
        
    Raises:
        HTTPException: If feature is disabled or creation fails
    """
    _check_feature_enabled()
    
    try:
        repository = await repository_service.create_repository(repository_data)
        logger.info(
            f"Created repository: {repository.service_type}/{repository.owner}/{repository.name} (ID: {repository.id})"
        )
        return repository
        
    except RepositoryServiceException as e:
        logger.error(f"Failed to create repository: {e}")
        if "already exists" in e.message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error creating repository: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{repository_id}", response_model=RepositoryResponse)
async def get_repository(
    repository_id: int,
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """
    Get repository by ID.
    
    The returned RepositoryResponse supports the delegation pattern via
    create_context() method for LLM integration.
    
    Args:
        repository_id: Repository ID
        repository_service: Repository service dependency
        
    Returns:
        Repository response with delegation pattern support
        
    Raises:
        HTTPException: If feature is disabled, repository not found, or operation fails
    """
    _check_feature_enabled()
    
    if repository_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository ID must be a positive integer"
        )
    
    try:
        repository = await repository_service.get_repository(repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with ID {repository_id} not found"
            )
        
        logger.info(f"Retrieved repository: ID {repository_id}")
        return repository
        
    except HTTPException:
        raise
    except RepositoryServiceException as e:
        logger.error(f"Failed to get repository {repository_id}: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error getting repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.put("/{repository_id}", response_model=RepositoryResponse)
async def update_repository(
    repository_id: int,
    updates: RepositoryUpdate,
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """
    Update repository.
    
    Args:
        repository_id: Repository ID
        updates: Repository update data
        repository_service: Repository service dependency
        
    Returns:
        Updated repository response
        
    Raises:
        HTTPException: If feature is disabled, repository not found, or update fails
    """
    _check_feature_enabled()
    
    if repository_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository ID must be a positive integer"
        )
    
    try:
        repository = await repository_service.update_repository(repository_id, updates)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with ID {repository_id} not found"
            )
        
        logger.info(f"Updated repository: ID {repository_id}")
        return repository
        
    except HTTPException:
        raise
    except RepositoryServiceException as e:
        logger.error(f"Failed to update repository {repository_id}: {e}")
        if "constraint violation" in e.message.lower():
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=e.message)
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error updating repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.delete("/{repository_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_repository(
    repository_id: int,
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """
    Delete repository.
    
    Args:
        repository_id: Repository ID
        repository_service: Repository service dependency
        
    Raises:
        HTTPException: If feature is disabled, repository not found, or deletion fails
    """
    _check_feature_enabled()
    
    if repository_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository ID must be a positive integer"
        )
    
    try:
        deleted = await repository_service.delete_repository(repository_id)
        
        if not deleted:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with ID {repository_id} not found"
            )
        
        logger.info(f"Deleted repository: ID {repository_id}")
        # 204 No Content - no return value
        
    except HTTPException:
        raise
    except RepositoryServiceException as e:
        logger.error(f"Failed to delete repository {repository_id}: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error deleting repository {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )


@router.get("/{repository_id}/context", response_model=RepositoryContext)
async def get_repository_context(
    repository_id: int,
    ref: str = None,
    current_path: str = None,
    repository_service: RepositoryService = Depends(get_repository_service),
):
    """
    Generate RepositoryContext from repository (convenience endpoint).
    
    This endpoint demonstrates the delegation pattern where a RepositoryResponse
    can create RepositoryContext instances for LLM integration.
    
    Args:
        repository_id: Repository ID
        ref: Branch/tag reference (optional, defaults to repository's default_branch)
        current_path: Current document path (optional)
        repository_service: Repository service dependency
        
    Returns:
        RepositoryContext instance ready for LLM queries
        
    Raises:
        HTTPException: If feature is disabled, repository not found, or operation fails
    """
    _check_feature_enabled()
    
    if repository_id <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Repository ID must be a positive integer"
        )
    
    try:
        repository = await repository_service.get_repository(repository_id)
        
        if not repository:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Repository with ID {repository_id} not found"
            )
        
        # Use delegation pattern to create context
        context = repository.create_context(ref=ref, current_path=current_path)
        
        logger.info(
            f"Generated context for repository {repository_id}: "
            f"{context.service}/{context.owner}/{context.repo}"
        )
        return context
        
    except HTTPException:
        raise
    except RepositoryServiceException as e:
        logger.error(f"Failed to get repository context {repository_id}: {e}")
        raise HTTPException(status_code=e.status_code, detail=e.message)
    except Exception as e:
        logger.error(f"Unexpected error generating repository context {repository_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )