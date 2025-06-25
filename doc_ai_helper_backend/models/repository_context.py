"""
Repository context models.

This module contains Pydantic models for repository and document context
used in LLM queries with document-aware functionality.
"""

from pydantic import BaseModel, Field, validator
from typing import Optional
from datetime import datetime
from enum import Enum


class GitService(str, Enum):
    """Supported Git services."""

    GITHUB = "github"
    GITLAB = "gitlab"
    BITBUCKET = "bitbucket"


class DocumentType(str, Enum):
    """Supported document types."""

    MARKDOWN = "markdown"
    HTML = "html"
    TEXT = "text"
    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    JSON = "json"
    YAML = "yaml"
    XML = "xml"
    OTHER = "other"


class RepositoryContext(BaseModel):
    """
    Repository context information from current document view.

    This model represents the repository and location context
    of the currently displayed document.
    """

    service: GitService = Field(
        ..., description="Git service type (github, gitlab, etc.)"
    )
    owner: str = Field(
        ..., description="Repository owner/organization name", min_length=1
    )
    repo: str = Field(..., description="Repository name", min_length=1)
    ref: str = Field(default="main", description="Branch/tag reference")
    current_path: Optional[str] = Field(
        default=None, description="Current document path relative to repository root"
    )
    base_url: Optional[str] = Field(
        default=None, description="Base URL for the repository"
    )

    @validator("owner", "repo")
    def validate_name_format(cls, v):
        """Validate owner and repo name format."""
        if not v or not isinstance(v, str):
            raise ValueError("Owner and repo must be non-empty strings")

        # Basic validation for common Git service naming rules
        import re

        if not re.match(r"^[a-zA-Z0-9][a-zA-Z0-9._-]*[a-zA-Z0-9]$|^[a-zA-Z0-9]$", v):
            raise ValueError(f"Invalid name format: {v}")

        return v

    @validator("current_path")
    def validate_path_format(cls, v):
        """Validate path format."""
        if v is not None:
            # Remove leading slash if present
            if v.startswith("/"):
                v = v[1:]
            # Basic path validation
            if ".." in v or v.startswith("."):
                raise ValueError("Invalid path format")
        return v

    @property
    def repository_full_name(self) -> str:
        """Get full repository name in 'owner/repo' format."""
        return f"{self.owner}/{self.repo}"

    @property
    def repository_url(self) -> str:
        """Get repository URL."""
        if self.base_url:
            return self.base_url

        # Generate default URL based on service
        if self.service == GitService.GITHUB:
            return f"https://github.com/{self.owner}/{self.repo}"
        elif self.service == GitService.GITLAB:
            return f"https://gitlab.com/{self.owner}/{self.repo}"
        elif self.service == GitService.BITBUCKET:
            return f"https://bitbucket.org/{self.owner}/{self.repo}"
        else:
            return f"https://{self.service}.com/{self.owner}/{self.repo}"

    @property
    def document_url(self) -> Optional[str]:
        """Get URL for the current document."""
        if not self.current_path:
            return None

        base_url = self.repository_url
        if self.service == GitService.GITHUB:
            return f"{base_url}/blob/{self.ref}/{self.current_path}"
        elif self.service == GitService.GITLAB:
            return f"{base_url}/-/blob/{self.ref}/{self.current_path}"
        elif self.service == GitService.BITBUCKET:
            return f"{base_url}/src/{self.ref}/{self.current_path}"
        else:
            return f"{base_url}/blob/{self.ref}/{self.current_path}"


class DocumentMetadata(BaseModel):
    """
    Metadata of currently displayed document.

    This model contains metadata information about the document
    being viewed, which helps in generating appropriate system prompts.
    """

    title: Optional[str] = Field(
        default=None, description="Document title extracted from content or filename"
    )
    type: DocumentType = Field(..., description="Document type/format")
    filename: Optional[str] = Field(default=None, description="Original filename")
    file_extension: Optional[str] = Field(default=None, description="File extension")
    last_modified: Optional[str] = Field(
        default=None, description="Last modification date (ISO format)"
    )
    file_size: Optional[int] = Field(
        default=None, description="File size in bytes", ge=0
    )
    encoding: str = Field(default="utf-8", description="File encoding")
    language: Optional[str] = Field(
        default=None, description="Primary language of the document (ja, en, etc.)"
    )

    @validator("type", pre=True)
    def normalize_document_type(cls, v):
        """Normalize document type from file extension or content type."""
        if isinstance(v, str):
            v_lower = v.lower()

            # Map common extensions to document types
            extension_map = {
                "md": DocumentType.MARKDOWN,
                "markdown": DocumentType.MARKDOWN,
                "html": DocumentType.HTML,
                "htm": DocumentType.HTML,
                "txt": DocumentType.TEXT,
                "py": DocumentType.PYTHON,
                "js": DocumentType.JAVASCRIPT,
                "ts": DocumentType.TYPESCRIPT,
                "json": DocumentType.JSON,
                "yml": DocumentType.YAML,
                "yaml": DocumentType.YAML,
                "xml": DocumentType.XML,
            }

            # Try to map extension
            if v_lower in extension_map:
                return extension_map[v_lower]

            # Try to find in enum values
            for doc_type in DocumentType:
                if v_lower == doc_type.value:
                    return doc_type

        return v if isinstance(v, DocumentType) else DocumentType.OTHER

    @classmethod
    def from_path(cls, file_path: str, **kwargs) -> "DocumentMetadata":
        """
        Create DocumentMetadata from file path.

        Args:
            file_path: File path to extract metadata from
            **kwargs: Additional metadata fields

        Returns:
            DocumentMetadata instance
        """
        import os

        filename = os.path.basename(file_path)
        name, ext = os.path.splitext(filename)

        # Extract title from filename
        title = name.replace("_", " ").replace("-", " ").title()

        # Determine document type from extension
        doc_type = ext[1:] if ext.startswith(".") else "other"

        return cls(
            title=title,
            type=doc_type,
            filename=filename,
            file_extension=ext[1:] if ext.startswith(".") else None,
            **kwargs,
        )

    @property
    def is_code_file(self) -> bool:
        """Check if this is a code file."""
        code_types = {
            DocumentType.PYTHON,
            DocumentType.JAVASCRIPT,
            DocumentType.TYPESCRIPT,
        }
        return self.type in code_types

    @property
    def is_documentation(self) -> bool:
        """Check if this is a documentation file."""
        doc_types = {DocumentType.MARKDOWN, DocumentType.HTML, DocumentType.TEXT}
        return self.type in doc_types

    @property
    def display_name(self) -> str:
        """Get display name for the document."""
        if self.title:
            return self.title
        elif self.filename:
            return self.filename
        else:
            return f"Document ({self.type.value})"


class RepositoryContextSummary(BaseModel):
    """
    Summary of repository context for logging and debugging.
    """

    repository: str = Field(..., description="Repository in 'owner/repo' format")
    service: str = Field(..., description="Git service")
    current_document: Optional[str] = Field(
        default=None, description="Current document path"
    )
    document_type: Optional[str] = Field(default=None, description="Document type")

    @classmethod
    def from_context(
        cls,
        repo_context: RepositoryContext,
        doc_metadata: Optional[DocumentMetadata] = None,
    ) -> "RepositoryContextSummary":
        """Create summary from full context objects."""
        return cls(
            repository=repo_context.repository_full_name,
            service=repo_context.service.value,
            current_document=repo_context.current_path,
            document_type=doc_metadata.type.value if doc_metadata else None,
        )
