"""
Unit tests for RepositoryService with proper AsyncMock configuration.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from doc_ai_helper_backend.services.repository_service import RepositoryService
from doc_ai_helper_backend.models.repository import (
    GitServiceType,
    RepositoryCreate,
    RepositoryUpdate,
)
from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService
from doc_ai_helper_backend.db.models import Repository as RepositoryModel
from doc_ai_helper_backend.core.exceptions import RepositoryServiceException


class TestRepositoryService:
    """Unit tests for RepositoryService with proper mocking."""

    @pytest.fixture
    def mock_db_session(self):
        """Create properly configured mock database session."""
        session = AsyncMock(spec=AsyncSession)
        session.add = MagicMock()  # Synchronous method
        session.commit = AsyncMock()
        session.rollback = AsyncMock()
        session.refresh = AsyncMock()
        session.delete = AsyncMock()  # Asynchronous method in SQLAlchemy 2.0
        session.execute = AsyncMock()
        return session

    @pytest.fixture
    def repository_service(self, mock_db_session):
        """Repository service with mocked database session."""
        return RepositoryService(mock_db_session)

    @pytest.fixture
    def sample_db_repository(self):
        """Sample database repository model with correct field names."""
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
            supported_branches_json=["main", "develop"],
            repo_metadata={"project_type": "documentation"},
            created_at=datetime(2025, 1, 1),
            updated_at=datetime(2025, 1, 1),
        )

    @pytest.fixture
    def sample_repository_create(self):
        """Sample repository creation data."""
        return RepositoryCreate(
            name="test-repo",
            owner="test-owner",
            service_type=GitServiceType.GITHUB,
            url="https://github.com/test-owner/test-repo",
            description="Test repository",
        )

    # CREATE TESTS
    @pytest.mark.asyncio
    async def test_create_repository_success(
        self, repository_service, mock_db_session, sample_repository_create
    ):
        """Test successful repository creation."""
        # Configure refresh to simulate database auto-generation
        def mock_refresh(obj):
            obj.id = 1
            obj.created_at = datetime(2025, 1, 1)
            obj.updated_at = datetime(2025, 1, 1)
        
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock(side_effect=mock_refresh)
        
        # Execute
        result = await repository_service.create_repository(sample_repository_create)
        
        # Verify
        assert result is not None
        assert result.name == sample_repository_create.name
        assert result.owner == sample_repository_create.owner
        assert result.id == 1
        mock_db_session.add.assert_called_once()
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_repository_duplicate_error(
        self, repository_service, mock_db_session, sample_repository_create
    ):
        """Test repository creation with duplicate error."""
        # Mock integrity error
        mock_db_session.commit.side_effect = IntegrityError("Duplicate", None, None)
        mock_db_session.rollback = AsyncMock()

        # Execute and verify exception
        with pytest.raises(RepositoryServiceException) as exc_info:
            await repository_service.create_repository(sample_repository_create)
        
        assert "Repository already exists" in str(exc_info.value)
        mock_db_session.rollback.assert_called_once()

    # READ TESTS
    @pytest.mark.asyncio
    async def test_get_repository_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository retrieval."""
        # Setup mock with proper async configuration
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await repository_service.get_repository(1)

        # Verify
        assert result is not None
        assert result.id == 1
        assert result.name == "test-repo"
        assert result.owner == "test-owner"
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_repository_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository retrieval when not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await repository_service.get_repository(999)

        # Verify
        assert result is None
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_repositories_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository listing."""
        # Setup mock with proper chaining
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [sample_db_repository]
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Execute
        results = await repository_service.list_repositories()

        # Verify
        assert len(results) == 1
        assert results[0].id == 1
        assert results[0].name == "test-repo"
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_repositories_empty(
        self, repository_service, mock_db_session
    ):
        """Test repository listing with no results."""
        # Setup mock
        mock_result = MagicMock()
        mock_scalars = MagicMock()
        mock_scalars.all.return_value = []
        mock_result.scalars.return_value = mock_scalars
        mock_db_session.execute.return_value = mock_result

        # Execute
        results = await repository_service.list_repositories()

        # Verify
        assert len(results) == 0
        mock_db_session.execute.assert_called_once()

    # UPDATE TESTS
    @pytest.mark.asyncio
    async def test_update_repository_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository update."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()
        mock_db_session.refresh = AsyncMock()

        update_data = RepositoryUpdate(description="Updated description")

        # Execute
        result = await repository_service.update_repository(1, update_data)

        # Verify
        assert result is not None
        assert result.description == "Updated description"
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_repository_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository update when repository not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        update_data = RepositoryUpdate(description="Updated description")

        # Execute
        result = await repository_service.update_repository(999, update_data)

        # Verify
        assert result is None
        mock_db_session.execute.assert_called_once()

    # DELETE TESTS
    @pytest.mark.asyncio
    async def test_delete_repository_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository deletion."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result
        mock_db_session.commit = AsyncMock()

        # Execute
        result = await repository_service.delete_repository(1)

        # Verify
        assert result is True
        mock_db_session.delete.assert_called_once_with(sample_db_repository)
        mock_db_session.commit.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_repository_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository deletion when repository not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        # Execute
        result = await repository_service.delete_repository(999)

        # Verify
        assert result is False
        mock_db_session.execute.assert_called_once()

    # FIND BY CONTEXT TESTS
    @pytest.mark.asyncio
    async def test_find_by_context_success(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test successful repository search by context."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result

        context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main"
        )

        # Execute
        result = await repository_service.find_by_context(context)

        # Verify
        assert result is not None
        assert result.name == "test-repo"
        assert result.owner == "test-owner"
        mock_db_session.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_find_by_context_not_found(
        self, repository_service, mock_db_session
    ):
        """Test repository search by context when not found."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db_session.execute.return_value = mock_result

        context = RepositoryContext(
            service=GitService.GITHUB,
            owner="nonexistent-owner",
            repo="nonexistent-repo",
            ref="main"
        )

        # Execute
        result = await repository_service.find_by_context(context)

        # Verify
        assert result is None
        mock_db_session.execute.assert_called_once()

    # DELEGATION PATTERN TESTS
    @pytest.mark.asyncio
    async def test_delegation_pattern(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test delegation pattern functionality."""
        # Setup mock
        mock_result = MagicMock()
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

        # Verify context
        assert context.service == GitService.GITHUB
        assert context.owner == "test-owner"
        assert context.repo == "test-repo"
        assert context.ref == "feature/test"
        assert context.current_path == "docs/api.md"

    @pytest.mark.asyncio
    async def test_delegation_pattern_defaults(
        self, repository_service, mock_db_session, sample_db_repository
    ):
        """Test delegation pattern with default values."""
        # Setup mock
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_db_repository
        mock_db_session.execute.return_value = mock_result

        # Get repository
        repository = await repository_service.get_repository(1)
        assert repository is not None

        # Test delegation pattern with defaults
        context = repository.create_context()

        # Verify context with defaults
        assert context.service == GitService.GITHUB
        assert context.owner == "test-owner"
        assert context.repo == "test-repo"
        assert context.ref == "main"  # default from repository
        assert context.current_path is None

    # ERROR HANDLING TESTS
    @pytest.mark.asyncio
    async def test_database_error_handling(
        self, repository_service, mock_db_session
    ):
        """Test general database error handling."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database connection failed")

        # Execute and verify exception
        with pytest.raises(RepositoryServiceException) as exc_info:
            await repository_service.get_repository(1)
        
        assert "Failed to get repository" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_create_repository_general_error(
        self, repository_service, mock_db_session, sample_repository_create
    ):
        """Test repository creation with general error."""
        # Mock general error
        mock_db_session.commit.side_effect = Exception("General database error")
        mock_db_session.rollback = AsyncMock()

        # Execute and verify exception
        with pytest.raises(RepositoryServiceException):
            await repository_service.create_repository(sample_repository_create)
        
        mock_db_session.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_list_repositories_error(
        self, repository_service, mock_db_session
    ):
        """Test repository listing with database error."""
        # Mock database error
        mock_db_session.execute.side_effect = Exception("Database error")

        # Execute and verify exception
        with pytest.raises(RepositoryServiceException):
            await repository_service.list_repositories()