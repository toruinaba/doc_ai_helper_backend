"""
Base adapter for Git operations.

This module defines the abstract base class that all Git service adapters
must implement. It provides the common interface for Git operations
regardless of the underlying service (GitHub, Forgejo, etc.).
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
import logging

from ..context import RepositoryContext

logger = logging.getLogger(__name__)


class GitOperationResult:
    """
    Result of a Git operation.
    
    This class standardizes the response format for all Git operations,
    providing consistent structure regardless of the underlying service.
    """
    
    def __init__(
        self,
        success: bool,
        data: Optional[Dict[str, Any]] = None,
        error: Optional[str] = None,
        url: Optional[str] = None,
        operation: Optional[str] = None
    ):
        """
        Initialize Git operation result.
        
        Args:
            success: Whether the operation was successful
            data: Operation result data (service-specific)
            error: Error message if operation failed
            url: URL to the created/modified resource (if applicable)
            operation: Name of the operation performed
        """
        self.success = success
        self.data = data or {}
        self.error = error
        self.url = url
        self.operation = operation
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert result to dictionary format."""
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "url": self.url,
            "operation": self.operation,
        }
    
    def __str__(self) -> str:
        """String representation of the result."""
        status = "SUCCESS" if self.success else "FAILED"
        operation_info = f" ({self.operation})" if self.operation else ""
        return f"GitOperationResult[{status}]{operation_info}: {self.data if self.success else self.error}"


class BaseGitAdapter(ABC):
    """
    Abstract base class for Git service adapters.
    
    This class defines the interface that all Git service adapters must implement.
    Each adapter is responsible for translating generic Git operations into
    service-specific API calls.
    """
    
    def __init__(self, repository_context: RepositoryContext):
        """
        Initialize the adapter with repository context.
        
        Args:
            repository_context: Repository context containing service information
        """
        self.repository_context = repository_context
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
        
        # Initialize credentials and client in subclasses
        self._initialize_client()
    
    @abstractmethod
    def _initialize_client(self) -> None:
        """
        Initialize the service-specific client.
        
        This method should set up authentication and create the necessary
        client instances for communicating with the Git service.
        """
        pass
    
    @abstractmethod
    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[str] = None
    ) -> GitOperationResult:
        """
        Create an issue in the repository.
        
        Args:
            title: Issue title
            body: Issue description/body
            labels: List of label names to apply
            assignees: List of usernames to assign
            milestone: Milestone name or number
            
        Returns:
            GitOperationResult with operation outcome
        """
        pass
    
    @abstractmethod
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None
    ) -> GitOperationResult:
        """
        Create a pull request in the repository.
        
        Args:
            title: PR title
            body: PR description/body
            head_branch: Source branch name
            base_branch: Target branch name
            draft: Whether to create as draft PR
            labels: List of label names to apply
            assignees: List of usernames to assign
            reviewers: List of usernames to request review from
            
        Returns:
            GitOperationResult with operation outcome
        """
        pass
    
    @abstractmethod
    async def get_repository_info(self) -> GitOperationResult:
        """
        Get repository information.
        
        Returns:
            GitOperationResult containing repository metadata
        """
        pass
    
    @abstractmethod
    async def list_branches(self) -> GitOperationResult:
        """
        List repository branches.
        
        Returns:
            GitOperationResult containing list of branch names
        """
        pass
    
    @abstractmethod
    async def get_file_content(
        self,
        file_path: str,
        branch: str = "main"
    ) -> GitOperationResult:
        """
        Get content of a file from the repository.
        
        Args:
            file_path: Path to the file in the repository
            branch: Branch name to read from
            
        Returns:
            GitOperationResult containing file content
        """
        pass
    
    @abstractmethod
    async def create_or_update_file(
        self,
        file_path: str,
        content: str,
        commit_message: str,
        branch: str = "main",
        create_branch_if_not_exists: bool = False
    ) -> GitOperationResult:
        """
        Create or update a file in the repository.
        
        Args:
            file_path: Path to the file in the repository
            content: New file content
            commit_message: Commit message
            branch: Branch to commit to
            create_branch_if_not_exists: Whether to create branch if it doesn't exist
            
        Returns:
            GitOperationResult with operation outcome
        """
        pass
    
    def get_service_info(self) -> Dict[str, Any]:
        """
        Get information about this adapter and the service it connects to.
        
        Returns:
            Dictionary containing adapter and service information
        """
        return {
            "adapter_class": self.__class__.__name__,
            "service_type": self.repository_context.service_type.value,
            "base_url": self.repository_context.base_url,
            "repository": self.repository_context.full_name,
        }
    
    def __str__(self) -> str:
        """String representation of the adapter."""
        return f"{self.__class__.__name__}({self.repository_context.full_name})"
