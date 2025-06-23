"""
GitHub function calling integration.

This module provides function definitions and utilities for integrating
GitHub operations with LLM function calling.
"""

import logging
from typing import Dict, Any, List, Optional

from doc_ai_helper_backend.models.llm import FunctionDefinition
from doc_ai_helper_backend.services.llm.function_manager import FunctionRegistry
from doc_ai_helper_backend.services.mcp.tools.github_tools import (
    create_github_issue,
    create_github_pull_request,
    check_github_repository_permissions,
)

logger = logging.getLogger(__name__)


def get_github_function_definitions() -> List[FunctionDefinition]:
    """
    Get GitHub tool function definitions for LLM function calling.

    Returns:
        List of function definitions for GitHub operations.
    """
    return [
        FunctionDefinition(
            name="create_github_issue",
            description="Create a new issue in a GitHub repository. Use this when users want to report bugs, request features, or document improvements to a repository.",
            parameters={
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in 'owner/repo' format (e.g., 'microsoft/vscode')",
                    },
                    "title": {
                        "type": "string",
                        "description": "Clear and descriptive title for the issue",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the issue, including steps to reproduce, expected behavior, etc.",
                    },
                    "labels": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional labels to categorize the issue (e.g., ['bug', 'documentation'])",
                    },
                    "assignees": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional GitHub usernames to assign to the issue",
                    },
                },
                "required": ["repository", "title", "description"],
            },
        ),
        FunctionDefinition(
            name="create_github_pull_request",
            description="Create a pull request in a GitHub repository. Use this when proposing changes to code or documentation.",
            parameters={
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in 'owner/repo' format",
                    },
                    "title": {
                        "type": "string",
                        "description": "Clear title describing the changes",
                    },
                    "description": {
                        "type": "string",
                        "description": "Detailed description of the changes and their purpose",
                    },
                    "head_branch": {
                        "type": "string",
                        "description": "Source branch containing the changes",
                    },
                    "base_branch": {
                        "type": "string",
                        "description": "Target branch to merge into (default: 'main')",
                        "default": "main",
                    },
                },
                "required": ["repository", "title", "description", "head_branch"],
            },
        ),
        FunctionDefinition(
            name="check_github_repository_permissions",
            description="Check what permissions the user has on a GitHub repository. Use this before attempting other GitHub operations.",
            parameters={
                "type": "object",
                "properties": {
                    "repository": {
                        "type": "string",
                        "description": "Repository in 'owner/repo' format",
                    },
                },
                "required": ["repository"],
            },
        ),
    ]


def register_github_functions(registry: FunctionRegistry) -> None:
    """
    Register GitHub functions with a function registry.

    Args:
        registry: Function registry to register GitHub functions with.
    """
    # Get function definitions
    function_defs = get_github_function_definitions()

    # Register create_github_issue
    registry.register_function(
        name="create_github_issue",
        function=create_github_issue,
        description=function_defs[0].description,
        parameters=function_defs[0].parameters,
    )

    # Register create_github_pull_request
    registry.register_function(
        name="create_github_pull_request",
        function=create_github_pull_request,
        description=function_defs[1].description,
        parameters=function_defs[1].parameters,
    )

    # Register check_github_repository_permissions
    registry.register_function(
        name="check_github_repository_permissions",
        function=check_github_repository_permissions,
        description=function_defs[2].description,
        parameters=function_defs[2].parameters,
    )

    logger.info("Registered 3 GitHub functions with function registry")


def create_github_function_registry() -> FunctionRegistry:
    """
    Create a function registry with GitHub functions pre-registered.

    Returns:
        Function registry with GitHub functions.
    """
    registry = FunctionRegistry()
    register_github_functions(registry)
    return registry


# Example usage patterns for common GitHub operations
GITHUB_FUNCTION_EXAMPLES = {
    "create_issue_for_bug": {
        "function": "create_github_issue",
        "example": {
            "repository": "owner/repo",
            "title": "Bug: Application crashes when loading large files",
            "description": "## Bug Description\nThe application crashes when trying to load files larger than 100MB.\n\n## Steps to Reproduce\n1. Open the application\n2. Try to load a file > 100MB\n3. Application crashes\n\n## Expected Behavior\nFile should load successfully or show appropriate error message.",
            "labels": ["bug", "high-priority"],
        },
    },
    "create_issue_for_documentation": {
        "function": "create_github_issue",
        "example": {
            "repository": "owner/repo",
            "title": "Documentation: Improve setup instructions",
            "description": "## Issue\nThe current setup instructions are unclear and missing steps for Windows users.\n\n## Suggested Improvements\n- Add Windows-specific installation steps\n- Include troubleshooting section\n- Add screenshots for key steps",
            "labels": ["documentation", "enhancement"],
        },
    },
    "create_pr_for_fix": {
        "function": "create_github_pull_request",
        "example": {
            "repository": "owner/repo",
            "title": "Fix: Resolve memory leak in file processor",
            "description": "## Changes\n- Fixed memory leak in FileProcessor class\n- Added proper resource cleanup\n- Added unit tests for memory management\n\n## Testing\n- All existing tests pass\n- Added new memory leak test\n- Tested with large files",
            "head_branch": "fix/memory-leak",
            "base_branch": "main",
        },
    },
}
