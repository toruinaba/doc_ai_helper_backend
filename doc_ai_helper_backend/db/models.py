"""
SQLAlchemy database models.
"""

from datetime import datetime
from typing import Any, Dict, List

from sqlalchemy import Boolean, Column, DateTime, Index, Integer, JSON, String, Text, UniqueConstraint
from sqlalchemy.sql import func

from .database import Base


class Repository(Base):
    """Repository SQLAlchemy model."""

    __tablename__ = "repositories"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Basic repository information
    name = Column(String, nullable=False, comment="Repository name")
    owner = Column(String, nullable=False, comment="Repository owner/organization")
    service_type = Column(String, nullable=False, comment="Git service type (github, gitlab, etc.)")
    url = Column(String, nullable=False, comment="Repository URL")

    # RepositoryContext generation fields
    base_url = Column(String, nullable=True, comment="Custom git service base URL")
    default_branch = Column(String, default="main", comment="Default branch")
    root_path = Column(String, nullable=True, comment="Documentation root directory path")

    # Repository management fields
    description = Column(Text, nullable=True, comment="Repository description")
    is_public = Column(Boolean, default=True, comment="Is repository publicly accessible")
    access_token_encrypted = Column(String, nullable=True, comment="Encrypted access token")
    supported_branches_json = Column(JSON, default=lambda: ["main"], comment="List of supported branches")
    repo_metadata = Column(JSON, default=lambda: {}, comment="Additional repository metadata")

    # Timestamps
    created_at = Column(DateTime, default=func.now(), comment="Creation timestamp")
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now(), comment="Last update timestamp")

    # Constraints and indexes
    __table_args__ = (
        # Unique constraint: one entry per service+owner+name combination
        UniqueConstraint(
            "service_type", 
            "owner", 
            "name", 
            name="uq_repository_service_owner_name"
        ),
        # Index for fast lookup by service+owner+name
        Index(
            "idx_repository_service_owner_name", 
            "service_type", 
            "owner", 
            "name"
        ),
        # Index for owner-based queries
        Index("idx_repository_owner", "owner"),
        # Index for service-based queries
        Index("idx_repository_service", "service_type"),
    )

    def __repr__(self) -> str:
        """String representation of Repository."""
        return f"<Repository(id={self.id}, service={self.service_type}, owner={self.owner}, name={self.name})>"