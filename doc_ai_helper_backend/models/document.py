"""
Pydantic models for documents.
"""

from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, HttpUrl

from doc_ai_helper_backend.models.link_info import LinkInfo


class DocumentType(str, Enum):
    """Document type enum."""

    MARKDOWN = "markdown"
    QUARTO = "quarto"
    HTML = "html"
    OTHER = "other"


class DocumentBase(BaseModel):
    """Base model for document."""

    path: str = Field(..., description="Path to the document in the repository")
    name: str = Field(..., description="Document name")
    type: DocumentType = Field(..., description="Document type")


class DocumentMetadata(BaseModel):
    """Document metadata model."""

    size: int = Field(..., description="Document size in bytes")
    last_modified: datetime = Field(..., description="Last modified datetime")
    content_type: str = Field(..., description="Content type")
    sha: Optional[str] = Field(None, description="SHA hash of the document")
    download_url: Optional[HttpUrl] = Field(None, description="Download URL")
    html_url: Optional[HttpUrl] = Field(None, description="HTML URL")
    raw_url: Optional[HttpUrl] = Field(None, description="Raw URL")
    extra: Optional[Dict[str, Any]] = Field(default={}, description="Extra metadata")


class DocumentContent(BaseModel):
    """Document content model."""

    content: str = Field(..., description="Document content")
    encoding: str = Field(default="utf-8", description="Document encoding")


class DocumentResponse(DocumentBase):
    """Document response model."""

    metadata: DocumentMetadata = Field(..., description="Document metadata")
    content: DocumentContent = Field(..., description="Document content")
    repository: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner")
    service: str = Field(..., description="Git service")
    ref: str = Field(default="main", description="Branch or tag name")
    # 拡張フィールド
    links: Optional[List[LinkInfo]] = Field(default=None, description="Document links")
    transformed_content: Optional[str] = Field(
        default=None, description="Content with transformed links"
    )


class FileTreeItem(BaseModel):
    """File tree item model."""

    path: str = Field(..., description="Path to the item")
    name: str = Field(..., description="Item name")
    type: str = Field(..., description="Item type (file or directory)")
    size: Optional[int] = Field(None, description="Item size in bytes")
    sha: Optional[str] = Field(None, description="SHA hash of the item")
    download_url: Optional[HttpUrl] = Field(None, description="Download URL")
    html_url: Optional[HttpUrl] = Field(None, description="HTML URL")
    git_url: Optional[HttpUrl] = Field(None, description="Git URL")


class RepositoryStructureResponse(BaseModel):
    """Repository structure response model."""

    service: str = Field(..., description="Git service")
    owner: str = Field(..., description="Repository owner")
    repo: str = Field(..., description="Repository name")
    ref: str = Field(default="main", description="Branch or tag name")
    tree: List[FileTreeItem] = Field(..., description="Repository tree")
    last_updated: datetime = Field(..., description="Last updated datetime")


class HTMLMetadata(BaseModel):
    """HTML固有のメタデータモデル"""

    title: Optional[str] = Field(None, description="HTML document title")
    description: Optional[str] = Field(None, description="HTML document description")
    author: Optional[str] = Field(None, description="HTML document author")
    generator: Optional[str] = Field(
        None, description="Generator tool (Quarto, Hugo, etc.)"
    )
    source_file: Optional[str] = Field(None, description="Source file path (.md/.qmd)")
    build_info: Optional[Dict[str, Any]] = Field(
        default={}, description="Build information"
    )
    headings: List[Dict[str, Any]] = Field(
        default=[], description="Document heading structure"
    )
    lang: Optional[str] = Field(None, description="Document language")
    charset: Optional[str] = Field(None, description="Document character encoding")
