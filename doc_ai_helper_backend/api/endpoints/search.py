"""
Search-related API endpoints.
"""

import logging

from fastapi import APIRouter, Path

from doc_ai_helper_backend.models.search import SearchQuery, SearchResponse

# Logger
logger = logging.getLogger("doc_ai_helper")

# Router
router = APIRouter(tags=["search"])


@router.post(
    "/{service}/{owner}/{repo}",
    response_model=SearchResponse,
    summary="Search repository",
    description="Search for content in a repository",
)
async def search_repository(
    search_query: SearchQuery,
    service: str = Path(..., description="Git service (github, gitlab, etc.)"),
    owner: str = Path(..., description="Repository owner"),
    repo: str = Path(..., description="Repository name"),
):
    """
    Search for content in a repository.

    Args:
        search_query: Search query parameters
        service: Git service type (github, gitlab, etc.)
        owner: Repository owner
        repo: Repository name

    Returns:
        SearchResponse: Search results

    Raises:
        NotFoundException: If repository is not found
        GitServiceException: If there is an error with the Git service
    """
    # This is a placeholder for actual implementation
    logger.info(
        f"Searching in {service}/{owner}/{repo} for '{search_query.query}', "
        f"limit: {search_query.limit}, offset: {search_query.offset}"
    )

    # Mock response for now
    return SearchResponse(
        total=0,
        offset=search_query.offset,
        limit=search_query.limit,
        query=search_query.query,
        results=[],
        execution_time_ms=0.0,
    )
