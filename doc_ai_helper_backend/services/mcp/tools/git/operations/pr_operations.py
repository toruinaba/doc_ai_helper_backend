"""
Pull Request operations for Git repositories.

This module provides high-level operations for managing pull requests across
different Git hosting services.
"""

from typing import Dict, Any, List, Optional, Union
import logging

from ..adapters import BaseGitAdapter, GitOperationResult
from ..context import RepositoryContext
from ..service_resolver import resolve_git_adapter

logger = logging.getLogger(__name__)


class PROperations:
    """
    High-level operations for managing pull requests across Git services.
    
    This class provides a service-agnostic interface for PR operations,
    automatically resolving the appropriate adapter based on repository context.
    """
    
    def __init__(self, repository_context: RepositoryContext):
        """
        Initialize pull request operations.
        
        Args:
            repository_context: Repository context for determining service
        """
        self.repository_context = repository_context
        self.adapter: Optional[BaseGitAdapter] = None
        self.logger = logging.getLogger(f"{self.__class__.__module__}.{self.__class__.__name__}")
    
    async def _get_adapter(self) -> BaseGitAdapter:
        """Get or create the appropriate Git service adapter."""
        if self.adapter is None:
            self.adapter = resolve_git_adapter(self.repository_context)
        return self.adapter
    
    async def create_pull_request(
        self,
        title: str,
        body: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> GitOperationResult:
        """
        Create a new pull request in the repository.
        
        Args:
            title: PR title
            body: PR description/body
            head_branch: Source branch name
            base_branch: Target branch name
            draft: Whether to create as draft PR
            labels: List of label names to apply
            assignees: List of usernames to assign
            reviewers: List of usernames to request review from
            metadata: Additional metadata (service-specific)
            
        Returns:
            GitOperationResult with operation outcome
        """
        try:
            adapter = await self._get_adapter()
            
            self.logger.info(
                f"Creating PR '{title}' from {head_branch} to {base_branch} "
                f"in {self.repository_context.full_name}"
            )
            
            result = await adapter.create_pull_request(
                title=title,
                body=body,
                head_branch=head_branch,
                base_branch=base_branch,
                draft=draft,
                labels=labels,
                assignees=assignees,
                reviewers=reviewers
            )
            
            if result.success:
                self.logger.info(
                    f"Successfully created PR in {self.repository_context.full_name}: {result.url}"
                )
            else:
                self.logger.error(
                    f"Failed to create PR in {self.repository_context.full_name}: {result.error}"
                )
            
            return result
            
        except Exception as e:
            self.logger.error(f"Error creating pull request: {str(e)}")
            return GitOperationResult(
                success=False,
                error=f"Failed to create pull request: {str(e)}",
                operation="create_pull_request"
            )
    
    async def create_feature_pr(
        self,
        feature_name: str,
        description: str,
        changes_summary: str,
        head_branch: str,
        base_branch: str = "main",
        breaking_changes: Optional[str] = None,
        testing_notes: Optional[str] = None,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> GitOperationResult:
        """
        Create a feature pull request with standardized format.
        
        Args:
            feature_name: Name of the feature being added
            description: Description of the feature
            changes_summary: Summary of changes made
            head_branch: Source branch name
            base_branch: Target branch name
            breaking_changes: Description of any breaking changes
            testing_notes: Notes about testing performed
            reviewers: List of usernames to request review from
            assignees: List of usernames to assign
            
        Returns:
            GitOperationResult with operation outcome
        """
        title = f"feat: {feature_name}"
        
        body_parts = [
            "## Description",
            description,
            "",
            "## Changes",
            changes_summary,
        ]
        
        if breaking_changes:
            body_parts.extend([
                "",
                "## ⚠️ Breaking Changes",
                breaking_changes,
            ])
        
        if testing_notes:
            body_parts.extend([
                "",
                "## Testing",
                testing_notes,
            ])
        
        body = "\n".join(body_parts)
        
        labels = ["feature"]
        if breaking_changes:
            labels.append("breaking-change")
        
        return await self.create_pull_request(
            title=title,
            body=body,
            head_branch=head_branch,
            base_branch=base_branch,
            labels=labels,
            reviewers=reviewers,
            assignees=assignees
        )
    
    async def create_bugfix_pr(
        self,
        bug_description: str,
        fix_description: str,
        head_branch: str,
        base_branch: str = "main",
        issue_number: Optional[int] = None,
        testing_notes: Optional[str] = None,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> GitOperationResult:
        """
        Create a bug fix pull request with standardized format.
        
        Args:
            bug_description: Description of the bug being fixed
            fix_description: Description of the fix applied
            head_branch: Source branch name
            base_branch: Target branch name
            issue_number: Related issue number
            testing_notes: Notes about testing performed
            reviewers: List of usernames to request review from
            assignees: List of usernames to assign
            
        Returns:
            GitOperationResult with operation outcome
        """
        title = f"fix: {bug_description}"
        
        body_parts = [
            "## Bug Description",
            bug_description,
            "",
            "## Fix Applied",
            fix_description,
        ]
        
        if issue_number:
            body_parts.extend([
                "",
                f"Fixes #{issue_number}",
            ])
        
        if testing_notes:
            body_parts.extend([
                "",
                "## Testing",
                testing_notes,
            ])
        
        body = "\n".join(body_parts)
        
        return await self.create_pull_request(
            title=title,
            body=body,
            head_branch=head_branch,
            base_branch=base_branch,
            labels=["bugfix"],
            reviewers=reviewers,
            assignees=assignees
        )
    
    async def create_docs_pr(
        self,
        docs_description: str,
        changes_summary: str,
        head_branch: str,
        base_branch: str = "main",
        affected_sections: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> GitOperationResult:
        """
        Create a documentation pull request with standardized format.
        
        Args:
            docs_description: Description of documentation changes
            changes_summary: Summary of changes made
            head_branch: Source branch name
            base_branch: Target branch name
            affected_sections: List of documentation sections affected
            reviewers: List of usernames to request review from
            assignees: List of usernames to assign
            
        Returns:
            GitOperationResult with operation outcome
        """
        title = f"docs: {docs_description}"
        
        body_parts = [
            "## Documentation Changes",
            changes_summary,
        ]
        
        if affected_sections:
            body_parts.extend([
                "",
                "## Affected Sections",
                "\n".join(f"- {section}" for section in affected_sections),
            ])
        
        body = "\n".join(body_parts)
        
        return await self.create_pull_request(
            title=title,
            body=body,
            head_branch=head_branch,
            base_branch=base_branch,
            labels=["documentation"],
            reviewers=reviewers,
            assignees=assignees
        )
    
    async def create_refactor_pr(
        self,
        refactor_description: str,
        rationale: str,
        changes_summary: str,
        head_branch: str,
        base_branch: str = "main",
        performance_impact: Optional[str] = None,
        testing_notes: Optional[str] = None,
        reviewers: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None
    ) -> GitOperationResult:
        """
        Create a refactoring pull request with standardized format.
        
        Args:
            refactor_description: Description of the refactoring
            rationale: Rationale for the refactoring
            changes_summary: Summary of changes made
            head_branch: Source branch name
            base_branch: Target branch name
            performance_impact: Description of performance impact
            testing_notes: Notes about testing performed
            reviewers: List of usernames to request review from
            assignees: List of usernames to assign
            
        Returns:
            GitOperationResult with operation outcome
        """
        title = f"refactor: {refactor_description}"
        
        body_parts = [
            "## Refactoring Description",
            refactor_description,
            "",
            "## Rationale",
            rationale,
            "",
            "## Changes",
            changes_summary,
        ]
        
        if performance_impact:
            body_parts.extend([
                "",
                "## Performance Impact",
                performance_impact,
            ])
        
        if testing_notes:
            body_parts.extend([
                "",
                "## Testing",
                testing_notes,
            ])
        
        body = "\n".join(body_parts)
        
        return await self.create_pull_request(
            title=title,
            body=body,
            head_branch=head_branch,
            base_branch=base_branch,
            labels=["refactor"],
            reviewers=reviewers,
            assignees=assignees
        )
    
    async def close(self) -> None:
        """Close the adapter connection."""
        if self.adapter:
            await self.adapter.close()
    
    async def __aenter__(self):
        """Async context manager entry."""
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
