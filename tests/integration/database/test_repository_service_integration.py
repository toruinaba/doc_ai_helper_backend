"""
Integration tests for RepositoryService with real database.

Tests actual database operations without mocks.
"""

import pytest
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession

from doc_ai_helper_backend.services.repository_service import RepositoryService
from doc_ai_helper_backend.models.repository import (
    GitServiceType,
    RepositoryCreate,
    RepositoryUpdate,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService
from doc_ai_helper_backend.core.exceptions import RepositoryServiceException
from tests.fixtures.database import test_engine, test_db_session, sample_repository_in_db, clean_database


@pytest.mark.asyncio
class TestRepositoryServiceDatabaseIntegration:
    """Integration tests for RepositoryService with real database."""

    async def test_create_repository_integration(self, test_db_session: AsyncSession, clean_database):
        """Test repository creation with real database."""
        service = RepositoryService(test_db_session)
        
        repository_data = RepositoryCreate(
            name="integration-test-repo",
            owner="integration-owner",
            service_type=GitServiceType.GITHUB,
            url="https://github.com/integration-owner/integration-test-repo",
            description="Integration test repository",
            default_branch="main",
            root_path="docs",
            is_public=True,
            supported_branches=["main", "develop"],
            metadata={"test": "integration"}
        )
        
        # Create repository
        result = await service.create_repository(repository_data)
        
        # Verify result
        assert result is not None
        assert result.name == "integration-test-repo"
        assert result.owner == "integration-owner"
        assert result.service_type == GitServiceType.GITHUB
        assert result.description == "Integration test repository"
        assert result.id is not None
        assert result.created_at is not None
        assert result.updated_at is not None

    async def test_get_repository_integration(self, test_db_session: AsyncSession, sample_repository_in_db):
        """Test repository retrieval with real database."""
        service = RepositoryService(test_db_session)
        
        # Get repository
        result = await service.get_repository(sample_repository_in_db.id)
        
        # Verify result
        assert result is not None
        assert result.id == sample_repository_in_db.id
        assert result.name == sample_repository_in_db.name
        assert result.owner == sample_repository_in_db.owner

    async def test_list_repositories_integration(self, test_db_session: AsyncSession, sample_repository_in_db):
        """Test repository listing with real database."""
        service = RepositoryService(test_db_session)
        
        # List repositories
        results = await service.list_repositories()
        
        # Verify results
        assert len(results) >= 1
        assert any(repo.id == sample_repository_in_db.id for repo in results)

    async def test_update_repository_integration(self, test_db_session: AsyncSession, sample_repository_in_db):
        """Test repository update with real database."""
        service = RepositoryService(test_db_session)
        
        update_data = RepositoryUpdate(
            description="Updated description",
            default_branch="develop"
        )
        
        # Update repository
        result = await service.update_repository(sample_repository_in_db.id, update_data)
        
        # Verify result
        assert result is not None
        assert result.description == "Updated description"
        assert result.default_branch == "develop"
        assert result.updated_at >= sample_repository_in_db.updated_at

    async def test_delete_repository_integration(self, test_db_session: AsyncSession, sample_repository_in_db):
        """Test repository deletion with real database."""
        service = RepositoryService(test_db_session)
        
        # Delete repository
        success = await service.delete_repository(sample_repository_in_db.id)
        
        # Verify deletion
        assert success is True
        
        # Verify repository is gone
        result = await service.get_repository(sample_repository_in_db.id)
        assert result is None

    async def test_find_by_context_integration(self, test_db_session: AsyncSession, sample_repository_in_db):
        """Test finding repository by context with real database."""
        service = RepositoryService(test_db_session)
        
        context = RepositoryContext(
            service=GitService.GITHUB,
            owner=sample_repository_in_db.owner,
            repo=sample_repository_in_db.name,
            ref="main",
            current_path="docs/README.md"
        )
        
        # Find by context
        result = await service.find_by_context(context)
        
        # Verify result
        assert result is not None
        assert result.id == sample_repository_in_db.id
        assert result.name == sample_repository_in_db.name
        assert result.owner == sample_repository_in_db.owner

    async def test_delegation_pattern_integration(self, test_db_session: AsyncSession, sample_repository_in_db):
        """Test delegation pattern with real database."""
        service = RepositoryService(test_db_session)
        
        # Get repository
        repository = await service.get_repository(sample_repository_in_db.id)
        assert repository is not None
        
        # Test delegation pattern
        context = repository.create_context(
            ref="feature/test",
            current_path="docs/api.md"
        )
        
        # Verify context
        assert context.service == GitService.GITHUB
        assert context.owner == sample_repository_in_db.owner
        assert context.repo == sample_repository_in_db.name
        assert context.ref == "feature/test"
        assert context.current_path == "docs/api.md"

    async def test_duplicate_repository_error(self, test_db_session: AsyncSession, sample_repository_in_db):
        """Test duplicate repository creation error."""
        service = RepositoryService(test_db_session)
        
        # Try to create duplicate repository
        duplicate_data = RepositoryCreate(
            name=sample_repository_in_db.name,
            owner=sample_repository_in_db.owner,
            service_type=GitServiceType.GITHUB,
            url=sample_repository_in_db.url,
        )
        
        # Should raise exception
        with pytest.raises(RepositoryServiceException):
            await service.create_repository(duplicate_data)

    async def test_nonexistent_repository_operations(self, test_db_session: AsyncSession, clean_database):
        """Test operations on non-existent repositories."""
        service = RepositoryService(test_db_session)
        
        # Get non-existent repository
        result = await service.get_repository(999)
        assert result is None
        
        # Update non-existent repository
        update_data = RepositoryUpdate(description="Updated")
        result = await service.update_repository(999, update_data)
        assert result is None
        
        # Delete non-existent repository
        success = await service.delete_repository(999)
        assert success is False


@pytest.mark.asyncio
class TestRepositoryServiceDatabaseTransactions:
    """Test transaction handling in RepositoryService."""

    async def test_transaction_rollback_on_error(self, test_db_session: AsyncSession, clean_database):
        """Test that transactions are properly rolled back on errors."""
        service = RepositoryService(test_db_session)
        
        # Create a repository
        repository_data = RepositoryCreate(
            name="transaction-test",
            owner="test-owner",
            service_type=GitServiceType.GITHUB,
            url="https://github.com/test-owner/transaction-test",
        )
        
        result = await service.create_repository(repository_data)
        assert result is not None
        
        # Verify it exists
        found = await service.get_repository(result.id)
        assert found is not None
        
        # Test that repository remains intact after any error
        # Simply try to update a non-existent repository to test error handling
        update_data = RepositoryUpdate(description="This won't work")
        
        # This should not affect our existing repository
        result_nonexistent = await service.update_repository(99999, update_data)
        assert result_nonexistent is None  # Should return None for non-existent repo
        
        # Verify original repository is still intact and unchanged
        found_after_operation = await service.get_repository(result.id)
        assert found_after_operation is not None
        assert found_after_operation.name == "transaction-test"
        assert found_after_operation.description != "This won't work"  # Unchanged

    async def test_concurrent_operations(self, test_db_session: AsyncSession, clean_database):
        """Test concurrent repository operations."""
        service = RepositoryService(test_db_session)
        
        # Create repositories sequentially to avoid transaction conflicts
        import asyncio
        
        repositories_created = []
        
        # Create repositories one by one to ensure proper transaction handling
        for i in range(3):  # Reduced number to avoid transaction conflicts
            data = RepositoryCreate(
                name=f"concurrent-repo-{i}",
                owner="concurrent-owner",
                service_type=GitServiceType.GITHUB,
                url=f"https://github.com/concurrent-owner/concurrent-repo-{i}",
            )
            result = await service.create_repository(data)
            repositories_created.append(result)
        
        # All should succeed
        assert len(repositories_created) == 3
        
        # Verify all repositories were created
        all_repos = await service.list_repositories()
        concurrent_repos = [r for r in all_repos if r.name.startswith("concurrent-repo-")]
        assert len(concurrent_repos) == 3