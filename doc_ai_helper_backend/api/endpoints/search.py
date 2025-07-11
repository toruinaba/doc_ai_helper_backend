"""
Search-related API endpoints.
"""

import logging
import time
from typing import List

from fastapi import APIRouter, Depends, Path

from doc_ai_helper_backend.api.dependencies import get_document_service
from doc_ai_helper_backend.core.exceptions import NotFoundException
from doc_ai_helper_backend.models.search import (
    SearchQuery,
    SearchResponse,
    SearchResultItem,
)
from doc_ai_helper_backend.services.document import DocumentService

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
    document_service: DocumentService = Depends(get_document_service),
):
    """
    Search for content in a repository.

    Args:
        search_query: Search query parameters
        service: Git service type (github, gitlab, etc.)
        owner: Repository owner
        repo: Repository name
        document_service: Document service instance

    Returns:
        SearchResponse: Search results

    Raises:
        NotFoundException: If repository is not found
        GitServiceException: If there is an error with the Git service
    """
    # Only allow GitHub for now
    if service.lower() != "github":
        raise NotFoundException(f"Unsupported Git service: {service}")

    logger.info(
        f"Searching in {service}/{owner}/{repo} for '{search_query.query}', "
        f"limit: {search_query.limit}, offset: {search_query.offset}"
    )

    start_time = time.time()

    # Search repository
    search_results = await document_service.search_repository(
        service, owner, repo, search_query.query, search_query.limit
    )

    # Convert search results to SearchResultItem objects
    results: List[SearchResultItem] = []
    for item in search_results.get("results", []):
        result_item = SearchResultItem(
            path=item.get("path", ""),
            name=item.get("name", ""),
            type="file",  # Assume all search results are files
            repository=repo,
            owner=owner,
            service=service,
            score=item.get("score", 0.0),
            highlight=item.get("highlight", ""),
            metadata={"html_url": item.get("html_url", "")},
        )
        results.append(result_item)

    execution_time_ms = (time.time() - start_time) * 1000

    return SearchResponse(
        total=len(results),
        offset=search_query.offset,
        limit=search_query.limit,
        query=search_query.query,
        results=results,
        execution_time_ms=execution_time_ms,
    )
