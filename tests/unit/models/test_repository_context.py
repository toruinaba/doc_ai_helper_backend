"""
Tests for repository context models.

This module contains unit tests for the RepositoryContext and DocumentMetadata models.
"""

import pytest
from pydantic import ValidationError
from datetime import datetime

from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    GitService,
    DocumentType,
    RepositoryContextSummary,
)


class TestGitService:
    """Test GitService enum."""

    def test_git_service_values(self):
        """Test GitService enum values."""
        assert GitService.GITHUB == "github"
        assert GitService.GITLAB == "gitlab"
        assert GitService.BITBUCKET == "bitbucket"

    def test_git_service_iteration(self):
        """Test GitService can be iterated."""
        services = list(GitService)
        assert len(services) == 4  # GitHub, GitLab, Bitbucket, Forgejo
        assert GitService.GITHUB in services


class TestDocumentType:
    """Test DocumentType enum."""

    def test_document_type_values(self):
        """Test DocumentType enum values."""
        assert DocumentType.MARKDOWN == "markdown"
        assert DocumentType.HTML == "html"
        assert DocumentType.PYTHON == "python"
        assert DocumentType.JAVASCRIPT == "javascript"
        assert DocumentType.TYPESCRIPT == "typescript"

    def test_document_type_from_extension(self):
        """Test document type detection from extension."""
        # This tests the validator in DocumentMetadata
        pass  # Implemented in DocumentMetadata tests


class TestRepositoryContext:
    """Test RepositoryContext model."""

    def test_basic_creation(self):
        """Test basic RepositoryContext creation."""
        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="microsoft", repo="vscode", ref="main"
        )

        assert repo_context.service == GitService.GITHUB
        assert repo_context.owner == "microsoft"
        assert repo_context.repo == "vscode"
        assert repo_context.ref == "main"
        assert repo_context.current_path is None
        assert repo_context.base_url is None

    def test_creation_with_optional_fields(self):
        """Test RepositoryContext creation with optional fields."""
        repo_context = RepositoryContext(
            service=GitService.GITLAB,
            owner="group",
            repo="project",
            ref="develop",
            current_path="docs/api.md",
            base_url="https://custom-gitlab.com",
        )

        assert repo_context.service == GitService.GITLAB
        assert repo_context.owner == "group"
        assert repo_context.repo == "project"
        assert repo_context.ref == "develop"
        assert repo_context.current_path == "docs/api.md"
        assert repo_context.base_url == "https://custom-gitlab.com"

    def test_validation_errors(self):
        """Test validation errors for invalid data."""
        # Missing required fields
        with pytest.raises(ValidationError):
            RepositoryContext()

        # Empty owner
        with pytest.raises(ValidationError):
            RepositoryContext(service=GitService.GITHUB, owner="", repo="vscode")

        # Empty repo
        with pytest.raises(ValidationError):
            RepositoryContext(service=GitService.GITHUB, owner="microsoft", repo="")

    def test_owner_repo_validation(self):
        """Test owner and repo name validation."""
        # Valid names
        valid_names = [
            "microsoft",
            "user123",
            "org-name",
            "project.name",
            "a",
            "test_repo",
        ]

        for name in valid_names:
            repo_context = RepositoryContext(
                service=GitService.GITHUB, owner=name, repo=name, ref="main"
            )
            assert repo_context.owner == name
            assert repo_context.repo == name

    def test_repository_url_property(self):
        """Test repository_url property for different services."""
        # GitHub
        github_context = RepositoryContext(
            service=GitService.GITHUB, owner="microsoft", repo="vscode", ref="main"
        )
        assert github_context.repository_url == "https://github.com/microsoft/vscode"

        # GitLab
        gitlab_context = RepositoryContext(
            service=GitService.GITLAB, owner="group", repo="project", ref="main"
        )
        assert gitlab_context.repository_url == "https://gitlab.com/group/project"

        # Bitbucket
        bitbucket_context = RepositoryContext(
            service=GitService.BITBUCKET, owner="team", repo="repo", ref="main"
        )
        assert bitbucket_context.repository_url == "https://bitbucket.org/team/repo"

    def test_document_url_property(self):
        """Test document_url property for different services."""
        # No current_path
        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="microsoft", repo="vscode", ref="main"
        )
        assert repo_context.document_url is None

        # GitHub with path
        github_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            current_path="README.md",
        )
        assert (
            github_context.document_url
            == "https://github.com/microsoft/vscode/blob/main/README.md"
        )

        # GitLab with path
        gitlab_context = RepositoryContext(
            service=GitService.GITLAB,
            owner="group",
            repo="project",
            ref="develop",
            current_path="docs/api.md",
        )
        assert (
            gitlab_context.document_url
            == "https://gitlab.com/group/project/-/blob/develop/docs/api.md"
        )

        # Bitbucket with path
        bitbucket_context = RepositoryContext(
            service=GitService.BITBUCKET,
            owner="team",
            repo="repo",
            ref="feature",
            current_path="src/main.py",
        )
        assert (
            bitbucket_context.document_url
            == "https://bitbucket.org/team/repo/src/feature/src/main.py"
        )

    def test_dict_conversion(self):
        """Test conversion to and from dict."""
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            current_path="README.md",
        )

        # Convert to dict
        data = repo_context.model_dump()
        assert data["service"] == "github"
        assert data["owner"] == "microsoft"
        assert data["repo"] == "vscode"
        assert data["ref"] == "main"
        assert data["current_path"] == "README.md"

        # Create from dict
        new_context = RepositoryContext(**data)
        assert new_context == repo_context

    def test_json_serialization(self):
        """Test JSON serialization."""
        repo_context = RepositoryContext(
            service=GitService.GITHUB, owner="microsoft", repo="vscode", ref="main"
        )

        json_str = repo_context.model_dump_json()
        assert "microsoft" in json_str
        assert "vscode" in json_str
        assert "github" in json_str


class TestDocumentMetadata:
    """Test DocumentMetadata model."""

    def test_basic_creation(self):
        """Test basic DocumentMetadata creation."""
        doc_metadata = DocumentMetadata(
            title="Test Document", type=DocumentType.MARKDOWN, filename="test.md"
        )

        assert doc_metadata.title == "Test Document"
        assert doc_metadata.type == DocumentType.MARKDOWN
        assert doc_metadata.filename == "test.md"
        assert doc_metadata.encoding == "utf-8"  # Default value

    def test_creation_with_all_fields(self):
        """Test DocumentMetadata creation with all fields."""
        doc_metadata = DocumentMetadata(
            title="API Documentation",
            type=DocumentType.MARKDOWN,
            filename="api.md",
            file_extension=".md",
            last_modified="2025-06-25T12:00:00Z",
            file_size=1024,
            encoding="utf-8",
            language="ja",
        )

        assert doc_metadata.title == "API Documentation"
        assert doc_metadata.type == DocumentType.MARKDOWN
        assert doc_metadata.filename == "api.md"
        assert doc_metadata.file_extension == ".md"
        assert doc_metadata.last_modified == "2025-06-25T12:00:00Z"
        assert doc_metadata.file_size == 1024
        assert doc_metadata.encoding == "utf-8"
        assert doc_metadata.language == "ja"

    def test_validation_errors(self):
        """Test validation errors for invalid data."""
        # Missing required type field
        with pytest.raises(ValidationError):
            DocumentMetadata(title="Test")

        # Invalid file size (negative)
        with pytest.raises(ValidationError):
            DocumentMetadata(type=DocumentType.MARKDOWN, file_size=-1)

    def test_type_normalization(self):
        """Test document type normalization from file extensions."""
        # Test the validator if it exists
        # This would test the normalize_document_type validator
        pass  # Implementation depends on the actual validator logic

    def test_defaults(self):
        """Test default values."""
        doc_metadata = DocumentMetadata(type=DocumentType.PYTHON)

        assert doc_metadata.title is None
        assert doc_metadata.filename is None
        assert doc_metadata.file_extension is None
        assert doc_metadata.last_modified is None
        assert doc_metadata.file_size is None
        assert doc_metadata.encoding == "utf-8"
        assert doc_metadata.language is None

    def test_dict_conversion(self):
        """Test conversion to and from dict."""
        doc_metadata = DocumentMetadata(
            title="Test",
            type=DocumentType.JAVASCRIPT,
            filename="script.js",
            file_size=512,
        )

        # Convert to dict
        data = doc_metadata.model_dump()
        assert data["title"] == "Test"
        assert data["type"] == "javascript"
        assert data["filename"] == "script.js"
        assert data["file_size"] == 512

        # Create from dict
        new_metadata = DocumentMetadata(**data)
        assert new_metadata == doc_metadata


class TestRepositoryContextSummary:
    """Test RepositoryContextSummary model."""

    def test_basic_creation(self):
        """Test basic RepositoryContextSummary creation."""
        summary = RepositoryContextSummary(
            repository="microsoft/vscode",
            service="github",
            current_document="README.md",
            document_type="markdown",
        )

        assert summary.repository == "microsoft/vscode"
        assert summary.service == "github"
        assert summary.current_document == "README.md"
        assert summary.document_type == "markdown"

    def test_creation_with_optional_fields(self):
        """Test creation with optional fields."""
        summary = RepositoryContextSummary(
            repository="org/project",
            service="gitlab",
            current_document="docs/api.md",
            document_type="markdown",
        )

        assert summary.repository == "org/project"
        assert summary.service == "gitlab"
        assert summary.current_document == "docs/api.md"
        assert summary.document_type == "markdown"

    def test_creation_minimal(self):
        """Test creation with minimal required fields."""
        summary = RepositoryContextSummary(repository="test/repo", service="github")

        assert summary.repository == "test/repo"
        assert summary.service == "github"
        assert summary.current_document is None
        assert summary.document_type is None

    def test_validation_errors(self):
        """Test validation errors."""
        # Missing required fields
        with pytest.raises(ValidationError):
            RepositoryContextSummary()

        # Missing service field
        with pytest.raises(ValidationError):
            RepositoryContextSummary(repository="test/repo")

    def test_from_context_method(self):
        """Test creating summary from context objects."""
        # Create repository context
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            current_path="README.md",
        )

        # Create document metadata
        doc_metadata = DocumentMetadata(
            title="Visual Studio Code", type=DocumentType.MARKDOWN, filename="README.md"
        )

        # Create summary using from_context
        summary = RepositoryContextSummary.from_context(repo_context, doc_metadata)

        assert summary.repository == "microsoft/vscode"
        assert summary.service == "github"
        assert summary.current_document == "README.md"
        assert summary.document_type == "markdown"

    def test_from_context_without_document(self):
        """Test creating summary from context without document metadata."""
        repo_context = RepositoryContext(
            service=GitService.GITLAB, owner="group", repo="project", ref="develop"
        )

        summary = RepositoryContextSummary.from_context(repo_context)

        assert summary.repository == "group/project"
        assert summary.service == "gitlab"
        assert summary.current_document is None
        assert summary.document_type is None


class TestIntegrationScenarios:
    """Test integration scenarios with multiple models."""

    def test_complete_context_creation(self):
        """Test creating complete context with all models."""
        # Create repository context
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="microsoft",
            repo="vscode",
            ref="main",
            current_path="README.md",
        )

        # Create document metadata
        doc_metadata = DocumentMetadata(
            title="Visual Studio Code",
            type=DocumentType.MARKDOWN,
            filename="README.md",
            file_extension="md",
            file_size=2048,
            language="en",
        )

        # Create summary using from_context
        summary = RepositoryContextSummary.from_context(repo_context, doc_metadata)

        # Verify integration
        assert repo_context.owner in summary.repository
        assert repo_context.repo in summary.repository
        assert repo_context.current_path == summary.current_document
        assert doc_metadata.type.value == summary.document_type
        assert summary.service == repo_context.service.value

    def test_url_generation_edge_cases(self):
        """Test URL generation with edge cases."""
        # Special characters in paths
        repo_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test",
            repo="repo",
            ref="feature/new-api",
            current_path="docs/API Reference.md",
        )

        expected_url = (
            "https://github.com/test/repo/blob/feature/new-api/docs/API Reference.md"
        )
        assert repo_context.document_url == expected_url

    def test_serialization_roundtrip(self):
        """Test serialization and deserialization roundtrip."""
        # Create original objects
        repo_context = RepositoryContext(
            service=GitService.GITLAB,
            owner="group",
            repo="project",
            ref="develop",
            current_path="src/main.py",
        )

        doc_metadata = DocumentMetadata(
            title="Main Module",
            type=DocumentType.PYTHON,
            filename="main.py",
            file_size=1024,
        )

        # Serialize to JSON
        repo_json = repo_context.model_dump_json()
        doc_json = doc_metadata.model_dump_json()

        # Deserialize from JSON
        repo_restored = RepositoryContext.model_validate_json(repo_json)
        doc_restored = DocumentMetadata.model_validate_json(doc_json)

        # Verify equality
        assert repo_restored == repo_context
        assert doc_restored == doc_metadata
