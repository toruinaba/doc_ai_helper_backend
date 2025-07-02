"""
Forgejo adapter for MCP Git tools.

This module provides Forgejo-specific implementation of the MCP Git tools
abstraction, utilizing the ForgejoService for API operations.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from .base import MCPGitClientBase, MCPGitToolsBase
from ....git.forgejo_service import ForgejoService
from .....core.exceptions import (
    GitServiceException,
    NotFoundException,
    UnauthorizedException,
)

logger = logging.getLogger(__name__)


class MCPForgejoClient(MCPGitClientBase):
    """Forgejo API client for MCP tools."""
    
    def __init__(
        self, 
        base_url: str,
        access_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize Forgejo client."""
        super().__init__(**kwargs)
        self.forgejo_service = ForgejoService(
            base_url=base_url,
            access_token=access_token,
            username=username,
            password=password
        )
        self.base_url = base_url
    
    async def create_issue(
        self,
        repository: str,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Forgejo issue."""
        try:
            # Parse repository owner/repo
            if "/" not in repository:
                raise ValueError(f"Repository must be in 'owner/repo' format, got: {repository}")
            
            owner, repo = repository.split("/", 1)
            
            # Prepare issue data for Forgejo API
            issue_data = {
                "title": title,
                "body": description,
            }
            
            # Add labels if provided
            if labels:
                issue_data["labels"] = labels
            
            # Add assignees if provided  
            if assignees:
                issue_data["assignees"] = assignees
            
            # Create issue using Forgejo API
            async with self.forgejo_service.get_async_client() as client:
                url = f"{self.forgejo_service.base_url}/api/v1/repos/{owner}/{repo}/issues"
                
                response = await client.post(
                    url,
                    headers=self.forgejo_service._get_headers(),
                    json=issue_data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    return {
                        "issue_number": result.get("number"),
                        "issue_url": result.get("html_url"),
                        "title": result.get("title"),
                        "state": result.get("state"),
                        "created_at": result.get("created_at")
                    }
                elif response.status_code == 404:
                    raise NotFoundException(f"Repository {repository} not found")
                elif response.status_code == 401:
                    raise UnauthorizedException("Authentication failed")
                else:
                    raise GitServiceException(f"Failed to create issue: {response.text}")
                    
        except (NotFoundException, UnauthorizedException) as e:
            raise e
        except Exception as e:
            raise GitServiceException(f"Failed to create Forgejo issue: {str(e)}")
    
    async def create_pull_request(
        self,
        repository: str,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        **kwargs
    ) -> Dict[str, Any]:
        """Create a Forgejo pull request."""
        try:
            # Parse repository owner/repo
            if "/" not in repository:
                raise ValueError(f"Repository must be in 'owner/repo' format, got: {repository}")
            
            owner, repo = repository.split("/", 1)
            
            # Prepare PR data for Forgejo API
            pr_data = {
                "title": title,
                "body": description,
                "head": head_branch,
                "base": base_branch
            }
            
            # Create PR using Forgejo API
            async with self.forgejo_service.get_async_client() as client:
                url = f"{self.forgejo_service.base_url}/api/v1/repos/{owner}/{repo}/pulls"
                
                response = await client.post(
                    url,
                    headers=self.forgejo_service._get_headers(),
                    json=pr_data
                )
                
                if response.status_code == 201:
                    result = response.json()
                    return {
                        "pr_number": result.get("number"),
                        "pr_url": result.get("html_url"),
                        "title": result.get("title"),
                        "state": result.get("state"),
                        "head_branch": result.get("head", {}).get("ref"),
                        "base_branch": result.get("base", {}).get("ref"),
                        "created_at": result.get("created_at")
                    }
                elif response.status_code == 404:
                    raise NotFoundException(f"Repository {repository} not found")
                elif response.status_code == 401:
                    raise UnauthorizedException("Authentication failed")
                else:
                    raise GitServiceException(f"Failed to create pull request: {response.text}")
                    
        except (NotFoundException, UnauthorizedException) as e:
            raise e
        except Exception as e:
            raise GitServiceException(f"Failed to create Forgejo pull request: {str(e)}")
    
    async def check_repository_permissions(
        self,
        repository: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Check Forgejo repository permissions."""
        try:
            # Parse repository owner/repo
            if "/" not in repository:
                raise ValueError(f"Repository must be in 'owner/repo' format, got: {repository}")
            
            owner, repo = repository.split("/", 1)
            
            # Check permissions using Forgejo API
            async with self.forgejo_service.get_async_client() as client:
                url = f"{self.forgejo_service.base_url}/api/v1/repos/{owner}/{repo}"
                
                response = await client.get(
                    url,
                    headers=self.forgejo_service._get_headers()
                )
                
                if response.status_code == 200:
                    result = response.json()
                    permissions = result.get("permissions", {})
                    
                    return {
                        "repository": repository,
                        "permissions": permissions,
                        "can_read": permissions.get("pull", False),
                        "can_write": permissions.get("push", False),
                        "can_admin": permissions.get("admin", False)
                    }
                elif response.status_code == 404:
                    raise NotFoundException(f"Repository {repository} not found")
                elif response.status_code == 401:
                    raise UnauthorizedException("Authentication failed")
                else:
                    raise GitServiceException(f"Failed to check permissions: {response.text}")
                    
        except (NotFoundException, UnauthorizedException) as e:
            raise e
        except Exception as e:
            raise GitServiceException(f"Failed to check Forgejo repository permissions: {str(e)}")


class MCPForgejoAdapter(MCPGitToolsBase):
    """Forgejo-specific MCP Git tools adapter."""
    
    def __init__(
        self, 
        base_url: str,
        access_token: Optional[str] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs
    ):
        """Initialize Forgejo adapter."""
        client = MCPForgejoClient(
            base_url=base_url,
            access_token=access_token,
            username=username,
            password=password,
            **kwargs
        )
        super().__init__(client)
        self.base_url = base_url
        self.access_token = access_token
        self.username = username
    
    @property
    def service_name(self) -> str:
        """Return the service name."""
        return "forgejo"
    
    async def create_issue(
        self,
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        repository_context: Optional[Dict[str, Any]] = None,
        forgejo_token: Optional[str] = None,
        forgejo_username: Optional[str] = None,
        forgejo_password: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create a Forgejo issue with enhanced error handling.
        
        Args:
            title: Issue title
            description: Issue description
            labels: Issue labels
            assignees: Issue assignees
            repository_context: Current repository context
            forgejo_token: Forgejo access token (overrides instance token)
            forgejo_username: Forgejo username for basic auth
            forgejo_password: Forgejo password for basic auth
            **kwargs: Additional Forgejo-specific parameters
            
        Returns:
            JSON string with operation result
        """
        # Update client credentials if provided
        if (forgejo_token and forgejo_token != self.access_token) or forgejo_username:
            self.client = MCPForgejoClient(
                base_url=self.base_url,
                access_token=forgejo_token,
                username=forgejo_username,
                password=forgejo_password
            )
            self.access_token = forgejo_token
            self.username = forgejo_username
        
        try:
            return await super().create_issue(
                title=title,
                description=description,
                labels=labels,
                assignees=assignees,
                repository_context=repository_context,
                **kwargs
            )
        except NotFoundException:
            return json.dumps({
                "success": False,
                "error": "指定されたリポジトリが見つかりません。リポジトリ名とアクセス権限を確認してください。",
                "error_type": "repository_not_found"
            }, ensure_ascii=False, indent=2)
        except UnauthorizedException:
            return json.dumps({
                "success": False,
                "error": "認証に失敗しました。Forgejoトークンまたはユーザー名・パスワードを確認してください。",
                "error_type": "authentication_failed"
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Unexpected error in Forgejo issue creation: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"予期しないエラーが発生しました: {str(e)}",
                "error_type": "unexpected_error"
            }, ensure_ascii=False, indent=2)
    
    async def create_pull_request(
        self,
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",  
        repository_context: Optional[Dict[str, Any]] = None,
        forgejo_token: Optional[str] = None,
        forgejo_username: Optional[str] = None,
        forgejo_password: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Create a Forgejo pull request with enhanced error handling.
        
        Args:
            title: PR title
            description: PR description
            head_branch: Source branch
            base_branch: Target branch
            repository_context: Current repository context
            forgejo_token: Forgejo access token (overrides instance token)
            forgejo_username: Forgejo username for basic auth
            forgejo_password: Forgejo password for basic auth
            **kwargs: Additional Forgejo-specific parameters
            
        Returns:
            JSON string with operation result
        """
        # Update client credentials if provided
        if (forgejo_token and forgejo_token != self.access_token) or forgejo_username:
            self.client = MCPForgejoClient(
                base_url=self.base_url,
                access_token=forgejo_token,
                username=forgejo_username,
                password=forgejo_password
            )
            self.access_token = forgejo_token
            self.username = forgejo_username
        
        try:
            return await super().create_pull_request(
                title=title,
                description=description,
                head_branch=head_branch,
                base_branch=base_branch,
                repository_context=repository_context,
                **kwargs
            )
        except NotFoundException:
            return json.dumps({
                "success": False,
                "error": "指定されたリポジトリが見つかりません。リポジトリ名とアクセス権限を確認してください。",
                "error_type": "repository_not_found"
            }, ensure_ascii=False, indent=2)
        except UnauthorizedException:
            return json.dumps({
                "success": False,
                "error": "認証に失敗しました。Forgejoトークンまたはユーザー名・パスワードを確認してください。",
                "error_type": "authentication_failed"
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Unexpected error in Forgejo pull request creation: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"予期しないエラーが発生しました: {str(e)}",
                "error_type": "unexpected_error"
            }, ensure_ascii=False, indent=2)
    
    async def check_repository_permissions(
        self,
        repository_context: Optional[Dict[str, Any]] = None,
        forgejo_token: Optional[str] = None,
        forgejo_username: Optional[str] = None,
        forgejo_password: Optional[str] = None,
        **kwargs
    ) -> str:
        """
        Check Forgejo repository permissions with enhanced error handling.
        
        Args:
            repository_context: Current repository context
            forgejo_token: Forgejo access token (overrides instance token)
            forgejo_username: Forgejo username for basic auth
            forgejo_password: Forgejo password for basic auth
            **kwargs: Additional Forgejo-specific parameters
            
        Returns:
            JSON string with permission information
        """
        # Update client credentials if provided
        if (forgejo_token and forgejo_token != self.access_token) or forgejo_username:
            self.client = MCPForgejoClient(
                base_url=self.base_url,
                access_token=forgejo_token,
                username=forgejo_username,
                password=forgejo_password
            )
            self.access_token = forgejo_token
            self.username = forgejo_username
        
        try:
            return await super().check_repository_permissions(
                repository_context=repository_context,
                **kwargs
            )
        except NotFoundException:
            return json.dumps({
                "success": False,
                "error": "指定されたリポジトリが見つかりません。リポジトリ名とアクセス権限を確認してください。",
                "error_type": "repository_not_found"
            }, ensure_ascii=False, indent=2)
        except UnauthorizedException:
            return json.dumps({
                "success": False,
                "error": "認証に失敗しました。Forgejoトークンまたはユーザー名・パスワードを確認してください。",
                "error_type": "authentication_failed"
            }, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Unexpected error in Forgejo permission check: {str(e)}")
            return json.dumps({
                "success": False,
                "error": f"予期しないエラーが発生しました: {str(e)}",
                "error_type": "unexpected_error"
            }, ensure_ascii=False, indent=2)
