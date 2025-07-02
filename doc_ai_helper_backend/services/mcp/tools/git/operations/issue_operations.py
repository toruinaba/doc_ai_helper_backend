"""
Issue operations for Git repositories.

This module provides high-level operations for managing issues across
different Git hosting services.
"""

from typing import Dict, Any, List, Optional, Union
import logging

from ..adapters import BaseGitAdapter, GitOperationResult
from ..context import RepositoryContext
from ..service_resolver import resolve_git_adapter

logger = logging.getLogger(__name__)


class IssueOperations:
    """
    High-level operations for managing issues across Git services.

    This class provides a service-agnostic interface for issue operations,
    automatically resolving the appropriate adapter based on repository context.
    """

    def __init__(self, repository_context: RepositoryContext):
        """
        Initialize issue operations.

        Args:
            repository_context: Repository context for determining service
        """
        self.repository_context = repository_context
        self.adapter: Optional[BaseGitAdapter] = None
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

    async def _get_adapter(self) -> BaseGitAdapter:
        """Get or create the appropriate Git service adapter."""
        if self.adapter is None:
            self.adapter = resolve_git_adapter(self.repository_context)
        return self.adapter

    async def create_issue(
        self,
        title: str,
        body: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> GitOperationResult:
        """
        Create a new issue in the repository.

        Args:
            title: Issue title
            body: Issue description/body
            labels: List of label names to apply
            assignees: List of usernames to assign
            milestone: Milestone name or identifier
            metadata: Additional metadata (service-specific)

        Returns:
            GitOperationResult with operation outcome
        """
        try:
            adapter = await self._get_adapter()

            self.logger.info(
                f"Creating issue '{title}' in {self.repository_context.full_name}"
            )

            result = await adapter.create_issue(
                title=title,
                body=body,
                labels=labels,
                assignees=assignees,
                milestone=milestone,
            )

            if result.success:
                self.logger.info(
                    f"Successfully created issue in {self.repository_context.full_name}: {result.url}"
                )
            else:
                self.logger.error(
                    f"Failed to create issue in {self.repository_context.full_name}: {result.error}"
                )

            return result

        except Exception as e:
            self.logger.error(f"Error creating issue: {str(e)}")
            return GitOperationResult(
                success=False,
                error=f"Failed to create issue: {str(e)}",
                operation="create_issue",
            )

    async def create_bug_report(
        self,
        bug_description: str,
        steps_to_reproduce: str,
        expected_behavior: str,
        actual_behavior: str,
        environment_info: Optional[str] = None,
        assignees: Optional[List[str]] = None,
    ) -> GitOperationResult:
        """
        Create a bug report issue with standardized format.

        Args:
            bug_description: Brief description of the bug
            steps_to_reproduce: Steps to reproduce the issue
            expected_behavior: What should happen
            actual_behavior: What actually happens
            environment_info: Environment details (OS, version, etc.)
            assignees: List of usernames to assign

        Returns:
            GitOperationResult with operation outcome
        """
        title = f"Bug: {bug_description}"

        body_parts = [
            "## Bug Description",
            bug_description,
            "",
            "## Steps to Reproduce",
            steps_to_reproduce,
            "",
            "## Expected Behavior",
            expected_behavior,
            "",
            "## Actual Behavior",
            actual_behavior,
        ]

        if environment_info:
            body_parts.extend(
                [
                    "",
                    "## Environment",
                    environment_info,
                ]
            )

        body = "\n".join(body_parts)

        return await self.create_issue(
            title=title, body=body, labels=["bug"], assignees=assignees
        )

    async def create_feature_request(
        self,
        feature_title: str,
        problem_description: str,
        proposed_solution: str,
        alternatives_considered: Optional[str] = None,
        additional_context: Optional[str] = None,
        assignees: Optional[List[str]] = None,
    ) -> GitOperationResult:
        """
        Create a feature request issue with standardized format.

        Args:
            feature_title: Title of the feature request
            problem_description: Description of the problem to solve
            proposed_solution: Proposed solution
            alternatives_considered: Alternative solutions considered
            additional_context: Additional context or information
            assignees: List of usernames to assign

        Returns:
            GitOperationResult with operation outcome
        """
        title = f"Feature: {feature_title}"

        body_parts = [
            "## Problem Description",
            problem_description,
            "",
            "## Proposed Solution",
            proposed_solution,
        ]

        if alternatives_considered:
            body_parts.extend(
                [
                    "",
                    "## Alternatives Considered",
                    alternatives_considered,
                ]
            )

        if additional_context:
            body_parts.extend(
                [
                    "",
                    "## Additional Context",
                    additional_context,
                ]
            )

        body = "\n".join(body_parts)

        return await self.create_issue(
            title=title, body=body, labels=["enhancement"], assignees=assignees
        )

    async def create_documentation_issue(
        self,
        doc_title: str,
        doc_description: str,
        doc_location: Optional[str] = None,
        priority: str = "normal",
        assignees: Optional[List[str]] = None,
    ) -> GitOperationResult:
        """
        Create a documentation improvement issue.

        Args:
            doc_title: Title of the documentation issue
            doc_description: Description of what needs to be documented
            doc_location: Location where documentation should be added
            priority: Priority level (low, normal, high)
            assignees: List of usernames to assign

        Returns:
            GitOperationResult with operation outcome
        """
        title = f"Docs: {doc_title}"

        body_parts = [
            "## Documentation Request",
            doc_description,
        ]

        if doc_location:
            body_parts.extend(
                [
                    "",
                    "## Suggested Location",
                    doc_location,
                ]
            )

        body = "\n".join(body_parts)

        labels = ["documentation"]
        if priority == "high":
            labels.append("high-priority")
        elif priority == "low":
            labels.append("low-priority")

        return await self.create_issue(
            title=title, body=body, labels=labels, assignees=assignees
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
