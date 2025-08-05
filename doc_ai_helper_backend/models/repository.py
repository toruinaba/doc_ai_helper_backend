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
    BITBUCKET = "bitbucket"
    FORGEJO = "forgejo"


class RepositoryBase(BaseModel):
    """Base model for repository."""

    name: str = Field(..., description="Repository name")
    owner: str = Field(..., description="Repository owner")
    service_type: GitServiceType = Field(..., description="Git service type")
    url: HttpUrl = Field(..., description="Repository URL")
    
    # RepositoryContext generation fields
    base_url: Optional[str] = Field(None, description="Custom git service base URL")
    default_branch: str = Field("main", description="Default branch")
    
    # Document path resolution fields
    repository_root: str = Field("/", description="Repository base directory")
    document_root_directory: str = Field("/", description="Document root directory path from repository root (e.g., '/docs', default: '/')")
    root_document_path: Optional[str] = Field(None, description="Main document file path relative to document root directory (e.g., 'README.md')")
    
    # Legacy field (deprecated but maintained for compatibility)
    root_path: Optional[str] = Field(None, description="DEPRECATED: Use root_document_path instead")
    
    description: Optional[str] = Field(None, description="Repository description")
    is_public: bool = Field(default=True, description="Is repository public")

    @field_validator('repository_root')
    @classmethod
    def validate_repository_root(cls, v: Optional[str]) -> str:
        """Ensure repository_root ends with / unless it's just /, handle NULL values from DB"""
        # Handle NULL values from database by setting default
        if v is None or v == '':
            return '/'
        
        # Normalize directory separators (Windows compatibility)
        v = v.replace('\\', '/')
        
        # Normalize path (remove redundant separators, resolve . and ..)
        import os.path
        v = os.path.normpath(v).replace('\\', '/')
        
        # Handle leading double slashes after normpath (Unix keeps them)
        import re
        v = re.sub(r'^/+', '/', v)
        
        # Ensure it starts with / (absolute path)
        if not v.startswith('/'):
            v = '/' + v
        
        # Ensure it ends with / unless it's just /
        if v != '/' and not v.endswith('/'):
            v = v + '/'
        
        return v
    
    @field_validator('document_root_directory')
    @classmethod
    def validate_document_root_directory(cls, v: Optional[str]) -> str:
        """Ensure document_root_directory is absolute path, handle NULL values from DB"""
        # Handle NULL values from database by setting default
        if v is None or v == '':
            return '/'
        
        # Normalize directory separators (Windows compatibility)
        v = v.replace('\\', '/')
        
        # Normalize path (remove redundant separators, resolve . and ..)
        import os.path
        v = os.path.normpath(v).replace('\\', '/')
        
        # Handle leading double slashes after normpath (Unix keeps them)
        import re
        v = re.sub(r'^/+', '/', v)
        
        # Ensure it starts with / (absolute path)
        if not v.startswith('/'):
            v = '/' + v
        
        # Ensure it ends with / unless it's just /
        if v != '/' and not v.endswith('/'):
            v = v + '/'
        
        return v


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
    
    # RepositoryContext generation fields
    base_url: Optional[str] = Field(None, description="Custom git service base URL")
    default_branch: Optional[str] = Field(None, description="Default branch")
    
    # Document path resolution fields
    repository_root: Optional[str] = Field(None, description="Repository base directory")
    document_root_directory: Optional[str] = Field(None, description="Document root directory path from repository root (e.g., '/docs', default: '/')")
    root_document_path: Optional[str] = Field(None, description="Main document file path relative to document root directory (e.g., 'README.md')")
    
    # Legacy field (deprecated but maintained for compatibility)
    root_path: Optional[str] = Field(None, description="DEPRECATED: Use root_document_path instead")
    
    description: Optional[str] = Field(None, description="Repository description")
    is_public: Optional[bool] = Field(None, description="Is repository public")
    access_token: Optional[str] = Field(
        None, description="Access token for private repositories"
    )
    metadata: Optional[Dict[str, Any]] = Field(None, description="Repository metadata")

    @field_validator('repository_root')
    @classmethod
    def validate_repository_root(cls, v: Optional[str]) -> Optional[str]:
        """Ensure repository_root ends with / unless it's just /"""
        if v is not None:
            # Normalize directory separators (Windows compatibility)
            v = v.replace('\\', '/')
            
            # Normalize path (remove redundant separators, resolve . and ..)
            import os.path
            v = os.path.normpath(v).replace('\\', '/')
            
            # Handle leading double slashes after normpath (Unix keeps them)
            import re
            v = re.sub(r'^/+', '/', v)
            
            # Ensure it starts with / (absolute path)
            if not v.startswith('/'):
                v = '/' + v
                
            # Ensure it ends with / unless it's just /
            if v != '/' and not v.endswith('/'):
                v = v + '/'
        return v
    
    @field_validator('document_root_directory')
    @classmethod
    def validate_document_root_directory(cls, v: Optional[str]) -> Optional[str]:
        """Ensure document_root_directory is absolute path"""
        if v is not None:
            # Normalize directory separators (Windows compatibility)
            v = v.replace('\\', '/')
            
            # Normalize path (remove redundant separators, resolve . and ..)
            import os.path
            v = os.path.normpath(v).replace('\\', '/')
            
            # Handle leading double slashes after normpath (Unix keeps them)
            import re
            v = re.sub(r'^/+', '/', v)
            
            # Ensure it starts with / (absolute path)
            if not v.startswith('/'):
                v = '/' + v
            
            # Ensure it ends with / unless it's just /
            if v != '/' and not v.endswith('/'):
                v = v + '/'
        return v


class RepositoryResponse(RepositoryBase):
    """Repository response model with delegation pattern for RepositoryContext creation."""

    id: int = Field(..., description="Repository ID")
    supported_branches: List[str] = Field(["main"], description="List of supported branches")
    metadata: Dict[str, Any] = Field({}, description="Repository metadata")
    created_at: datetime = Field(..., description="Created datetime")
    updated_at: datetime = Field(..., description="Updated datetime")

    def create_context(
        self, 
        ref: Optional[str] = None,
        current_path: Optional[str] = None
    ) -> "RepositoryContext":
        """
        Create RepositoryContext from repository information (delegation pattern).
        
        Args:
            ref: Branch/tag reference (defaults to default_branch)
            current_path: Current document path (set by frontend)
            
        Returns:
            RepositoryContext instance for use in LLM queries
        """
        from .repository_context import RepositoryContext, GitService
        
        # Convert GitServiceType to GitService (temporary compatibility)
        service_mapping = {
            GitServiceType.GITHUB: GitService.GITHUB,
            GitServiceType.GITLAB: GitService.GITLAB,
            GitServiceType.BITBUCKET: GitService.BITBUCKET,
            GitServiceType.FORGEJO: GitService.FORGEJO,
        }
        
        return RepositoryContext(
            service=service_mapping[self.service_type],
            owner=self.owner,
            repo=self.name,
            ref=ref or self.default_branch,
            current_path=current_path,
            base_url=self.base_url
        )

    class Config:
        """Pydantic model config."""

        from_attributes = True
