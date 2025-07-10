"""
Unit tests for ConversationManager.
"""

import pytest
from unittest.mock import AsyncMock, Mock, patch
from doc_ai_helper_backend.services.llm.conversation_manager import ConversationManager
from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.models.document import DocumentMetadata, DocumentResponse, DocumentContent, DocumentType
from doc_ai_helper_backend.models.llm import MessageItem
from doc_ai_helper_backend.core.exceptions import GitServiceException


@pytest.fixture
def mock_git_service_factory():
    """Mock Git service factory."""
    factory = Mock()
    mock_git_service = AsyncMock()
    factory.create.return_value = mock_git_service
    return factory, mock_git_service


@pytest.fixture
def conversation_manager(mock_git_service_factory):
    """ConversationManager instance with mocked dependencies."""
    factory, _ = mock_git_service_factory
    return ConversationManager(factory)


@pytest.fixture
def sample_repository_context():
    """Sample repository context."""
    from doc_ai_helper_backend.models.repository_context import GitService
    return RepositoryContext(
        service=GitService.GITHUB,
        owner="microsoft",
        repo="vscode",
        current_path="README.md",
        ref="main"
    )


@pytest.fixture
def sample_document_metadata():
    """Sample document metadata."""
    from datetime import datetime
    return DocumentMetadata(
        size=1024,
        last_modified=datetime.fromisoformat("2024-01-01T00:00:00"),
        content_type="text/markdown",
        extra={"frontmatter": {"title": "VS Code README"}}
    )


@pytest.mark.asyncio
async def test_create_document_aware_conversation_success(
    conversation_manager, mock_git_service_factory, sample_repository_context, sample_document_metadata
):
    """Test successful creation of document-aware conversation."""
    factory, mock_git_service = mock_git_service_factory
    
    # Mock document response
    mock_document_content = DocumentContent(
        content="# VS Code\n\nVisual Studio Code is a lightweight code editor."
    )
    mock_document_response = DocumentResponse(
        path="README.md",
        name="README.md", 
        type=DocumentType.MARKDOWN,
        content=mock_document_content,
        metadata=sample_document_metadata,
        repository="vscode",
        owner="microsoft",
        service="github",
        ref="main",
        links=[]
    )
    mock_git_service.get_document.return_value = mock_document_response
    
    # Call method
    result = await conversation_manager.create_document_aware_conversation(
        repository_context=sample_repository_context,
        initial_prompt="Please summarize this document",
        document_metadata=sample_document_metadata
    )
    
    # Verify result
    assert len(result) == 3
    assert result[0].role == "system"
    assert result[1].role == "assistant"
    assert result[2].role == "user"
    
    # Verify system message content
    assert "microsoft/vscode" in result[0].content
    assert "README.md" in result[0].content
    assert "GitService.GITHUB" in result[0].content or "github" in result[0].content.lower()
    
    # Verify assistant message content
    assert "Document content from README.md" in result[1].content
    assert "VS Code" in result[1].content
    
    # Verify user message
    assert result[2].content == "Please summarize this document"
    
    # Verify Git service was called correctly
    factory.create.assert_called_once_with("github", access_token=None)
    mock_git_service.get_document.assert_called_once_with(
        owner="microsoft",
        repo="vscode", 
        path="README.md",
        ref="main"
    )


@pytest.mark.asyncio
async def test_create_document_aware_conversation_truncation(
    conversation_manager, mock_git_service_factory, sample_repository_context, sample_document_metadata
):
    """Test document content truncation when content is too long."""
    factory, mock_git_service = mock_git_service_factory
    
    # Create long content that exceeds MAX_DOCUMENT_LENGTH
    long_content = "A" * (ConversationManager.MAX_DOCUMENT_LENGTH + 1000)
    mock_document_content = DocumentContent(
        content=long_content
    )
    mock_document_response = DocumentResponse(
        path="README.md",
        name="README.md", 
        type=DocumentType.MARKDOWN,
        content=mock_document_content,
        metadata=sample_document_metadata,
        repository="vscode",
        owner="microsoft",
        service="github",
        ref="main",
        links=[]
    )
    mock_git_service.get_document.return_value = mock_document_response
    
    # Call method
    result = await conversation_manager.create_document_aware_conversation(
        repository_context=sample_repository_context,
        initial_prompt="Test prompt"
    )
    
    # Verify content was truncated
    assistant_content = result[1].content
    assert "[Content truncated" in assistant_content
    assert len(assistant_content) < len(long_content)


@pytest.mark.asyncio
async def test_create_document_aware_conversation_git_error(
    conversation_manager, mock_git_service_factory, sample_repository_context
):
    """Test fallback behavior when Git service fails."""
    factory, mock_git_service = mock_git_service_factory
    
    # Mock Git service to raise exception
    mock_git_service.get_document.side_effect = GitServiceException("Document not found")
    
    # Call method
    result = await conversation_manager.create_document_aware_conversation(
        repository_context=sample_repository_context,
        initial_prompt="Test prompt"
    )
    
    # Verify fallback conversation was created
    assert len(result) == 2  # System + User message (no assistant message)
    assert result[0].role == "system"
    assert result[1].role == "user"
    
    # Verify error message is included
    assert "Unable to load document content" in result[0].content
    assert "Document not found" in result[0].content


def test_is_initial_request_no_repository_context(conversation_manager):
    """Test is_initial_request returns False when no repository context."""
    result = conversation_manager.is_initial_request([], None)
    assert result is False


def test_is_initial_request_no_conversation_history(conversation_manager, sample_repository_context):
    """Test is_initial_request returns True when no conversation history."""
    result = conversation_manager.is_initial_request(None, sample_repository_context)
    assert result is True
    
    result = conversation_manager.is_initial_request([], sample_repository_context)
    assert result is True


def test_is_initial_request_existing_document_content(conversation_manager, sample_repository_context):
    """Test is_initial_request returns False when document content already exists."""
    conversation_history = [
        MessageItem(role="system", content="System message"),
        MessageItem(role="assistant", content="Document content: # Sample\nContent here"),
        MessageItem(role="user", content="Previous question")
    ]
    
    result = conversation_manager.is_initial_request(conversation_history, sample_repository_context)
    assert result is False


def test_is_initial_request_no_existing_document_content(conversation_manager, sample_repository_context):
    """Test is_initial_request returns True when no document content exists in history."""
    conversation_history = [
        MessageItem(role="user", content="Previous question"),
        MessageItem(role="assistant", content="Previous answer without document content")
    ]
    
    result = conversation_manager.is_initial_request(conversation_history, sample_repository_context)
    assert result is True


@pytest.mark.asyncio
async def test_fetch_document_content_success(
    conversation_manager, mock_git_service_factory, sample_repository_context, sample_document_metadata
):
    """Test successful document content fetch."""
    factory, mock_git_service = mock_git_service_factory
    
    mock_document_content = DocumentContent(
        content="Sample content"
    )
    mock_document_response = DocumentResponse(
        path="README.md",
        name="README.md", 
        type=DocumentType.MARKDOWN,
        content=mock_document_content,
        metadata=sample_document_metadata,
        repository="vscode",
        owner="microsoft",
        service="github",
        ref="main",
        links=[]
    )
    mock_git_service.get_document.return_value = mock_document_response
    
    # Call method
    result = await conversation_manager._fetch_document_content(sample_repository_context)
    
    # Verify result
    assert result == "Sample content"
    
    # Verify Git service call
    factory.create.assert_called_once_with("github", access_token=None)
    mock_git_service.get_document.assert_called_once_with(
        owner="microsoft",
        repo="vscode",
        path="README.md",
        ref="main"
    )


@pytest.mark.asyncio
async def test_fetch_document_content_git_exception(
    conversation_manager, mock_git_service_factory, sample_repository_context
):
    """Test document content fetch with Git service exception."""
    factory, mock_git_service = mock_git_service_factory
    
    mock_git_service.get_document.side_effect = Exception("Network error")
    
    # Call method and expect exception
    with pytest.raises(GitServiceException) as exc_info:
        await conversation_manager._fetch_document_content(sample_repository_context)
    
    assert "Document fetch failed" in str(exc_info.value)
    assert "Network error" in str(exc_info.value)


def test_create_system_message(conversation_manager, sample_repository_context, sample_document_metadata):
    """Test system message creation."""
    result = conversation_manager._create_system_message(sample_repository_context, sample_document_metadata)
    
    assert result.role == "system"
    assert "microsoft/vscode" in result.content
    assert "README.md" in result.content
    assert "main" in result.content
    assert "GitService.GITHUB" in result.content or "github" in result.content.lower()
    assert "text/markdown" in result.content
    assert "VS Code README" in result.content


def test_create_system_message_no_metadata(conversation_manager, sample_repository_context):
    """Test system message creation without metadata."""
    result = conversation_manager._create_system_message(sample_repository_context, None)
    
    assert result.role == "system"
    assert "microsoft/vscode" in result.content
    assert "Content Type:" not in result.content


def test_create_document_message(conversation_manager, sample_repository_context):
    """Test document message creation."""
    document_content = "# Sample Document\nThis is a test."
    
    result = conversation_manager._create_document_message(
        sample_repository_context, document_content, None
    )
    
    assert result.role == "assistant"
    assert "Document content from README.md" in result.content
    assert "# Sample Document" in result.content
    assert "This is a test." in result.content


def test_create_fallback_conversation(conversation_manager, sample_repository_context):
    """Test fallback conversation creation."""
    result = conversation_manager._create_fallback_conversation(
        sample_repository_context, "Test prompt", "Network error"
    )
    
    assert len(result) == 2
    assert result[0].role == "system"
    assert result[1].role == "user"
    
    assert "Unable to load document content" in result[0].content
    assert "Network error" in result[0].content
    assert result[1].content == "Test prompt"