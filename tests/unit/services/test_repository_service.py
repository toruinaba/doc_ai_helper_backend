"""
Unit tests for RepositoryService.

Tests CRUD operations, delegation pattern, and error handling
for repository management service.
"""

import pytest
from unittest.mock import AsyncMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from doc_ai_helper_backend.services.repository_service import RepositoryService
from doc_ai_helper_backend.models.repository import (
    GitServiceType,
    RepositoryCreate,
    RepositoryUpdate,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService
from doc_ai_helper_backend.db.models import Repository as RepositoryModel
from doc_ai_helper_backend.core.exceptions import RepositoryServiceException


@pytest.fixture
def mock_db_session():
    """Mock database session."""
    session = AsyncMock(spec=AsyncSession)
    session.add = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    session.refresh = AsyncMock()
    session.delete = AsyncMock()
    session.execute = AsyncMock()
    return session


@pytest.fixture
def repository_service(mock_db_session):
    """Repository service with mocked database session."""
    return RepositoryService(mock_db_session)


@pytest.fixture
def sample_repository_create():
    """Sample repository creation data."""
    return RepositoryCreate(
        name="test-repo",
        owner="test-owner",
        service_type=GitServiceType.GITHUB,
        url="https://github.com/test-owner/test-repo",
        base_url=None,
        default_branch="main",
        root_path="docs",
        description="Test repository",
        is_public=True,
        access_token="test-token",
        metadata={"project_type": "documentation"},
    )


@pytest.fixture
def sample_db_repository():
    """Sample database repository model."""
    return RepositoryModel(
        id=1,
        name="test-repo",
        owner="test-owner",
        service_type="github",
        url="https://github.com/test-owner/test-repo",
        base_url=None,
        default_branch="main",
        root_path="docs",
        description="Test repository",
        is_public=True,
        access_token_encrypted="encrypted_test-token",
        supported_branches_json=["main", "develop"],
        repo_metadata={"project_type": "documentation"},
    )


class TestRepositoryServiceCreate:
    """Test repository creation operations."""

    @pytest.mark.asyncio
    async def test_create_repository_success(
        self, repository_service, mock_db_session, sample_repository_create
    ):
        """Test successful repository creation."""
        from datetime import datetime
        
        # Mock database operations
        mock_db_session.add = AsyncMock()
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()
        
        # Mock the refresh to set the required fields
        def mock_refresh(repo):
            repo.id = 1
            repo.created_at = datetime(2025, 1, 1)
            repo.updated_at = datetime(2025, 1, 1)
        
        mock_db_session.refresh.side_effect = mock_refresh

        # Execute
        result = await repository_service.create_repository(sample_repository_create)

        # Verify
        assert result.name == "test-repo"
        assert result.owner == "test-owner"
        assert result.service_type == GitServiceType.GITHUB
        assert result.root_path == "docs"
        assert result.metadata == {"project_type": "documentation"}
        
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()
        mock_db_session.refresh.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_repository_duplicate_error(
        self, repository_service, mock_db_session, sample_repository_create
    ):
        """Test repository creation with duplicate constraint violation."""
        # Mock integrity error
        mock_db_session.add = AsyncMock()
        mock_db_session.commit = AsyncMock(side_effect=IntegrityError("", "", ""))
        mock_db_session.rollback = AsyncMock()

        # Execute and verify
        with pytest.raises(RepositoryServiceException) as exc_info:
            await repository_service.create_repository(sample_repository_create)
        
        assert "already exists" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_repository_general_error(
        self, repository_service, mock_db_session, sample_repository_create
    ):
        """Test repository creation with general error."""
        # Mock general error
        mock_db_session.add = AsyncMock(side_effect=Exception("Database error"))
        mock_db_session.rollback = AsyncMock()

        # Execute and verify
        with pytest.raises(RepositoryServiceException) as exc_info:
            await repository_service.create_repository(sample_repository_create)
        
        assert "Failed to create repository" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()


class TestRepositoryServiceRead:
    """Test repository read operations."""

    @pytest.mark.asyncio
    async def test_get_repository_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository retrieval."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await repository_service.get_repository(1)

        # Verify
        assert result is not None
        assert result.id == 1
        assert result.name == "test-repo"
        assert result.owner == "test-owner"
        assert result.service_type == GitServiceType.GITHUB

    @pytest.mark.asyncio
    async def test_get_repository_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository retrieval when not found."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await repository_service.get_repository(999)

        # Verify
        assert result is None

    @pytest.mark.asyncio
    async def test_list_repositories_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository listing."""
        # Mock database query
        mock_result = AsyncMock()
        mock_scalars = AsyncMock()
        mock_scalars.all.return_value = [sample_db_repository]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await repository_service.list_repositories(skip=0, limit=10)

        # Verify
        assert len(result) == 1
        assert result[0].name == "test-repo"

    @pytest.mark.asyncio
    async def test_list_repositories_error(
        self, repository_service, mock_db_session
    ):
        """Test repository listing with database error."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")

        # Execute and verify
        with pytest.raises(RepositoryServiceException):
            await repository_service.list_repositories()


class TestRepositoryServiceUpdate:
    """Test repository update operations."""

    @pytest.mark.asyncio
    async def test_update_repository_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository update."""
        # Mock database query and update
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        # Create update data
        updates = RepositoryUpdate(description="Updated description")

        # Execute
        result = await repository_service.update_repository(1, updates)

        # Verify
        assert result is not None
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_repository_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository update when repository not found."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Create update data
        updates = RepositoryUpdate(description="Updated description")

        # Execute
        result = await repository_service.update_repository(999, updates)

        # Verify
        assert result is None


class TestRepositoryServiceDelete:
    """Test repository delete operations."""

    @pytest.mark.asyncio
    async def test_delete_repository_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository deletion."""
        # Mock database query and delete
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result
        mock_db_session.delete = AsyncMock()
        mock_db_session.commit = AsyncMock()

        # Execute
        result = await repository_service.delete_repository(1)

        # Verify
        assert result is True
        mock_db_session.delete.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_repository_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository deletion when repository not found."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await repository_service.delete_repository(999)

        # Verify
        assert result is False


class TestRepositoryServiceFindByContext:
    """Test find by RepositoryContext operations."""

    @pytest.mark.asyncio
    async def test_find_by_context_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository search by context."""
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result

        # Create repository context
        context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main",
        )

        # Execute
        result = await repository_service.find_by_context(context)

        # Verify
        assert result is not None
        assert result.name == "test-repo"
        assert result.owner == "test-owner"

    @pytest.mark.asyncio
    async def test_find_by_context_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository search by context when not found."""
        # Mock database query returning None
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Create repository context
        context = RepositoryContext(
            service=GitService.GITHUB,
            owner="nonexistent-owner",
            repo="nonexistent-repo",
            ref="main",
        )

        # Execute
        result = await repository_service.find_by_context(context)

        # Verify
        assert result is None


class TestRepositoryServiceDelegationPattern:
    """Test delegation pattern functionality."""

    @pytest.mark.asyncio
    async def test_repository_response_create_context(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test RepositoryResponse.create_context() delegation pattern."""
        from datetime import datetime
        
        # Add required timestamp fields
        sample_db_repository.created_at = datetime(2025, 1, 1)
        sample_db_repository.updated_at = datetime(2025, 1, 1)
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result

        # Get repository
        repository = await repository_service.get_repository(1)
        assert repository is not None

        # Test delegation pattern
        context = repository.create_context(
            ref="feature/test",
            current_path="docs/api.md"
        )

        # Verify context creation
        assert isinstance(context, RepositoryContext)
        assert context.service == GitService.GITHUB
        assert context.owner == "test-owner"
        assert context.repo == "test-repo"
        assert context.ref == "feature/test"
        assert context.current_path == "docs/api.md"

    @pytest.mark.asyncio
    async def test_repository_response_create_context_defaults(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test RepositoryResponse.create_context() with default values."""
        from datetime import datetime
        
        # Add required timestamp fields
        sample_db_repository.created_at = datetime(2025, 1, 1)
        sample_db_repository.updated_at = datetime(2025, 1, 1)
        
        # Mock database query
        mock_result = AsyncMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result

        # Get repository
        repository = await repository_service.get_repository(1)
        assert repository is not None

        # Test delegation pattern with defaults
        context = repository.create_context()

        # Verify context creation with defaults
        assert context.ref == "main"  # default_branch
        assert context.current_path is None


class TestRepositoryServiceHelpers:
    """Test helper methods."""

    def test_encrypt_decrypt_token(self, repository_service):
        """Test token encryption and decryption (placeholder implementation)."""
        original_token = "test-token-12345"
        
        # Test encryption
        encrypted = repository_service._encrypt_token(original_token)
        assert encrypted.startswith("encrypted_")
        assert encrypted != original_token
        
        # Test decryption
        decrypted = repository_service._decrypt_token(encrypted)
        assert decrypted == original_token

    def test_to_response_conversion(self, repository_service, sample_db_repository):
        """Test database model to response model conversion."""
        from datetime import datetime
        
        # Add required timestamp fields
        sample_db_repository.created_at = datetime(2025, 1, 1)
        sample_db_repository.updated_at = datetime(2025, 1, 1)
        
        # Convert
        response = repository_service._to_response(sample_db_repository)
        
        # Verify conversion
        assert response.id == 1
        assert response.name == "test-repo"
        assert response.owner == "test-owner"
        assert response.service_type == GitServiceType.GITHUB
        assert response.root_path == "docs"
        assert response.supported_branches == ["main", "develop"]
        assert response.metadata == {"project_type": "documentation"}