"""
Pydantic models for repositories.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl, field_validator


class GitServiceType(str, Enum):
    """Git service type enum."""

    GITHUB = "github"
    GITLAB = "gitlab"
    # Add more service types as needed


class RepositoryBase(BaseModel):
    """Base model for repository."""

    name: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner")
    service_type: GitServiceType = Field(..., description="Git service type")
    url: HttpUrl = Field(..., description="Repository URL")
    branch: str = Field(default="main", description="Default branch")
    description: Optional[str] = Field(None, description="Repository description")
    is_public: bool = Field(default=True, description="Is repository public")


class RepositoryCreate(RepositoryBase):
    """Repository create model."""

    access_token: Optional[str] = Field(
        None, description="Access token for private repositories"
    )
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Repository metadata"
    )


class RepositoryUpdate(BaseModel):
    """Repository update model."""

    name: Optional[str] = Field(None, description="Repository name")
    owner: Optional[str] = Field(None, description="Repository owner")
    service_type: Optional[GitServiceType] = Field(None, description="Git service type")
    url: Optional[HttpUrl] = Field(None, description="Repository URL")
    branch: Optional[str] = Field(None, description="Default branch")
    description: Optional[str] = Field(None, description="Repository description")
    is_public: Optional[bool] = Field(None, description="Is repository public")
    access_token: Optional[str] = Field(
        None, description="Access token for private repositories"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Repository metadata")


class RepositoryResponse(RepositoryBase):
    """Repository response model."""

    id: int = Field(..., description="Repository ID")
    created_at: datetime = Field(..., description="Created datetime")
    updated_at: datetime = Field(..., description="Updated datetime")
    metadata: Optional[Dict[str, Any]] = Field(
        default={}, description="Repository metadata"
    )

    class Config:
        """Pydantic model config."""

        from_attributes = True
