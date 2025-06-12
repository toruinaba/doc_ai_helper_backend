"""
Pydantic models for search functionality.
"""

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class SearchQuery(BaseModel):
    """Search query model."""

    query: str = Field(..., description="Search query")
    limit: int = Field(default=10, description="Maximum number of results")
    offset: int = Field(default=0, description="Results offset")
    file_extensions: Optional[List[str]] = Field(
        default=None, description="Filter by file extensions"
    )
    path_prefix: Optional[str] = Field(
        default=None, description="Filter by path prefix"
    )
    metadata_filters: Optional[Dict[str, Any]] = Field(
        default=None, description="Filter by metadata"
    )


class SearchResultItem(BaseModel):
    """Search result item model."""

    path: str = Field(..., description="Path to the file")
    name: str = Field(..., description="File name")
    type: str = Field(..., description="File type")
    repository: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner")
    service: str = Field(..., description="Git service")
    score: float = Field(..., description="Search score")
    highlight: Optional[str] = Field(None, description="Search highlight")
    metadata: Optional[Dict[str, Any]] = Field(default={}, description="File metadata")


class SearchResponse(BaseModel):
    """Search response model."""

    total: int = Field(..., description="Total number of results")
    offset: int = Field(..., description="Results offset")
    limit: int = Field(..., description="Maximum number of results")
    query: str = Field(..., description="Search query")
    results: List[SearchResultItem] = Field(..., description="Search results")
    execution_time_ms: float = Field(..., description="Search execution time in milliseconds")
