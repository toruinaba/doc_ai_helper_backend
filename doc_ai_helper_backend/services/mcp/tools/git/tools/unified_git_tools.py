"""
Unified Git tools interface for MCP registration.

This module provides the unified interface for Git operations that can be
registered with the MCP (Model Context Protocol) system. It handles repository
context-driven operations across different Git services.
"""

from typing import Dict, Any, List, Optional, Union
import logging
import json

from ..context import RepositoryContext, GitServiceType
from ..operations import IssueOperations, PROperations, RepositoryOperations
from ..service_resolver import GitServiceResolver
from ..adapters import GitHubAdapter, ForgejoAdapter

logger = logging.getLogger(__name__)


class UnifiedGitTools:
    """
    Unified interface for Git operations across different services.

    This class provides a single entry point for all Git operations,
    automatically resolving the appropriate service based on repository context.
    """

    def __init__(self):
        """Initialize unified Git tools."""
        self.logger = logging.getLogger(
            f"{self.__class__.__module__}.{self.__class__.__name__}"
        )

        # Register available adapters
        self._register_adapters()

        self.logger.info("Initialized UnifiedGitTools")

    def _register_adapters(self) -> None:
        """Register all available Git service adapters."""
        GitServiceResolver.register_adapter(GitServiceType.GITHUB, GitHubAdapter)
        GitServiceResolver.register_adapter(GitServiceType.FORGEJO, ForgejoAdapter)

        self.logger.debug("Registered Git service adapters")

    def _parse_repository_context(
        self, repository_context: Union[str, Dict[str, Any]]
    ) -> RepositoryContext:
        """
        Parse repository context from various input formats.

        Args:
            repository_context: Repository context as string or dict

        Returns:
            Parsed RepositoryContext object

        Raises:
            ValueError: If context cannot be parsed
        """
        try:
            if isinstance(repository_context, str):
                # Try to parse as JSON string first
                try:
                    context_dict = json.loads(repository_context)
                    return RepositoryContext(**context_dict)
                except json.JSONDecodeError:
                    # If not JSON, treat as repository name and try to infer
                    if "/" in repository_context:
                        owner, repo = repository_context.split("/", 1)
                        # Default to GitHub for simple owner/repo format
                        return RepositoryContext(
                            service_type=GitServiceType.GITHUB,
                            base_url="https://github.com",
                            owner=owner,
                            repo=repo,
                        )
                    else:
                        raise ValueError(
                            f"Cannot parse repository context: {repository_context}"
                        )

            elif isinstance(repository_context, dict):
                return RepositoryContext(**repository_context)

            else:
                raise ValueError(
                    f"Unsupported repository context type: {type(repository_context)}"
                )

        except Exception as e:
            self.logger.error(f"Failed to parse repository context: {str(e)}")
            raise ValueError(f"Invalid repository context: {str(e)}")

    async def create_issue(
        self,
        repository_context: Union[str, Dict[str, Any]],
        title: str,
        description: str,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        milestone: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create an issue in the specified repository.

        Args:
            repository_context: Repository context (string or dict)
            title: Issue title
            description: Issue description/body
            labels: List of label names to apply
            assignees: List of usernames to assign
            milestone: Milestone name or identifier
            metadata: Additional metadata

        Returns:
            Dictionary containing operation result
        """
        try:
            repo_context = self._parse_repository_context(repository_context)

            self.logger.info(f"Creating issue '{title}' in {repo_context.full_name}")

            async with IssueOperations(repo_context) as issue_ops:
                result = await issue_ops.create_issue(
                    title=title,
                    body=description,
                    labels=labels,
                    assignees=assignees,
                    milestone=milestone,
                    metadata=metadata,
                )

                return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error creating issue: {str(e)}")
            return {"success": False, "error": str(e), "operation": "create_issue"}

    async def create_bug_report(
        self,
        repository_context: Union[str, Dict[str, Any]],
        bug_description: str,
        steps_to_reproduce: str,
        expected_behavior: str,
        actual_behavior: str,
        environment_info: Optional[str] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a bug report issue with standardized format.

        Args:
            repository_context: Repository context (string or dict)
            bug_description: Brief description of the bug
            steps_to_reproduce: Steps to reproduce the issue
            expected_behavior: What should happen
            actual_behavior: What actually happens
            environment_info: Environment details
            assignees: List of usernames to assign

        Returns:
            Dictionary containing operation result
        """
        try:
            repo_context = self._parse_repository_context(repository_context)

            self.logger.info(f"Creating bug report in {repo_context.full_name}")

            async with IssueOperations(repo_context) as issue_ops:
                result = await issue_ops.create_bug_report(
                    bug_description=bug_description,
                    steps_to_reproduce=steps_to_reproduce,
                    expected_behavior=expected_behavior,
                    actual_behavior=actual_behavior,
                    environment_info=environment_info,
                    assignees=assignees,
                )

                return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error creating bug report: {str(e)}")
            return {"success": False, "error": str(e), "operation": "create_bug_report"}

    async def create_feature_request(
        self,
        repository_context: Union[str, Dict[str, Any]],
        feature_title: str,
        problem_description: str,
        proposed_solution: str,
        alternatives_considered: Optional[str] = None,
        additional_context: Optional[str] = None,
        assignees: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """
        Create a feature request issue with standardized format.

        Args:
            repository_context: Repository context (string or dict)
            feature_title: Title of the feature request
            problem_description: Description of the problem to solve
            proposed_solution: Proposed solution
            alternatives_considered: Alternative solutions considered
            additional_context: Additional context or information
            assignees: List of usernames to assign

        Returns:
            Dictionary containing operation result
        """
        try:
            repo_context = self._parse_repository_context(repository_context)

            self.logger.info(
                f"Creating feature request '{feature_title}' in {repo_context.full_name}"
            )

            async with IssueOperations(repo_context) as issue_ops:
                result = await issue_ops.create_feature_request(
                    feature_title=feature_title,
                    problem_description=problem_description,
                    proposed_solution=proposed_solution,
                    alternatives_considered=alternatives_considered,
                    additional_context=additional_context,
                    assignees=assignees,
                )

                return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error creating feature request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "operation": "create_feature_request",
            }

    async def create_pull_request(
        self,
        repository_context: Union[str, Dict[str, Any]],
        title: str,
        description: str,
        head_branch: str,
        base_branch: str = "main",
        draft: bool = False,
        labels: Optional[List[str]] = None,
        assignees: Optional[List[str]] = None,
        reviewers: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Create a pull request in the specified repository.

        Args:
            repository_context: Repository context (string or dict)
            title: PR title
            description: PR description/body
            head_branch: Source branch name
            base_branch: Target branch name
            draft: Whether to create as draft PR
            labels: List of label names to apply
            assignees: List of usernames to assign
            reviewers: List of usernames to request review from
            metadata: Additional metadata

        Returns:
            Dictionary containing operation result
        """
        try:
            repo_context = self._parse_repository_context(repository_context)

            self.logger.info(f"Creating PR '{title}' in {repo_context.full_name}")

            async with PROperations(repo_context) as pr_ops:
                result = await pr_ops.create_pull_request(
                    title=title,
                    body=description,
                    head_branch=head_branch,
                    base_branch=base_branch,
                    draft=draft,
                    labels=labels,
                    assignees=assignees,
                    reviewers=reviewers,
                    metadata=metadata,
                )

                return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error creating pull request: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "operation": "create_pull_request",
            }

    async def get_repository_info(
        self, repository_context: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get repository information.

        Args:
            repository_context: Repository context (string or dict)

        Returns:
            Dictionary containing repository information
        """
        try:
            repo_context = self._parse_repository_context(repository_context)

            self.logger.debug(f"Getting repository info for {repo_context.full_name}")

            async with RepositoryOperations(repo_context) as repo_ops:
                result = await repo_ops.get_repository_info()

                return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error getting repository info: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "operation": "get_repository_info",
            }

    async def get_repository_summary(
        self, repository_context: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Get comprehensive repository summary.

        Args:
            repository_context: Repository context (string or dict)

        Returns:
            Dictionary containing repository summary
        """
        try:
            repo_context = self._parse_repository_context(repository_context)

            self.logger.debug(
                f"Getting repository summary for {repo_context.full_name}"
            )

            async with RepositoryOperations(repo_context) as repo_ops:
                result = await repo_ops.get_repository_summary()

                return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error getting repository summary: {str(e)}")
            return {
                "success": False,
                "error": str(e),
                "operation": "get_repository_summary",
            }

    async def get_file_content(
        self,
        repository_context: Union[str, Dict[str, Any]],
        file_path: str,
        branch: str = "main",
    ) -> Dict[str, Any]:
        """
        Get content of a file from the repository.

        Args:
            repository_context: Repository context (string or dict)
            file_path: Path to the file in the repository
            branch: Branch name to read from

        Returns:
            Dictionary containing file content
        """
        try:
            repo_context = self._parse_repository_context(repository_context)

            self.logger.debug(f"Getting file {file_path} from {repo_context.full_name}")

            async with RepositoryOperations(repo_context) as repo_ops:
                result = await repo_ops.get_file_content(file_path, branch)

                return result.to_dict()

        except Exception as e:
            self.logger.error(f"Error getting file content: {str(e)}")
            return {"success": False, "error": str(e), "operation": "get_file_content"}

    def get_supported_services(self) -> Dict[str, str]:
        """
        Get list of supported Git services.

        Returns:
            Dictionary mapping service types to adapter names
        """
        return GitServiceResolver.list_supported_services()

    def validate_repository_context(
        self, repository_context: Union[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Validate repository context format and service support.

        Args:
            repository_context: Repository context to validate

        Returns:
            Dictionary containing validation result
        """
        try:
            repo_context = self._parse_repository_context(repository_context)
            is_supported = GitServiceResolver.validate_repository_context(repo_context)

            return {
                "valid": True,
                "supported": is_supported,
                "parsed_context": {
                    "service_type": repo_context.service_type.value,
                    "base_url": repo_context.base_url,
                    "owner": repo_context.owner,
                    "repo": repo_context.repo,
                    "full_name": repo_context.full_name,
                },
            }

        except Exception as e:
            return {"valid": False, "supported": False, "error": str(e)}


# Global instance for MCP registration
unified_git_tools = UnifiedGitTools()
