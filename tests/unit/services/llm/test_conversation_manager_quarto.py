"""
Test suite for ConversationManager Quarto integration.

Tests the Quarto HTML→QMD path resolution functionality within
the ConversationManager's document fetching workflow.
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch

from doc_ai_helper_backend.services.llm.conversation_manager import ConversationManager
from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.services.git.factory import GitServiceFactory
from doc_ai_helper_backend.core.exceptions import GitServiceException


class TestConversationManagerQuarto:
    """Test cases for ConversationManager Quarto integration"""

    @pytest.fixture
    def mock_git_service_factory(self):
        """Create mock GitServiceFactory"""
        factory = Mock(spec=GitServiceFactory)
        git_service = AsyncMock()
        factory.create.return_value = git_service
        return factory, git_service

    @pytest.fixture
    def conversation_manager(self, mock_git_service_factory):
        """Create ConversationManager instance with mocked dependencies"""
        factory, _ = mock_git_service_factory
        return ConversationManager(factory)

    @pytest.fixture
    def quarto_repository_context(self):
        """Create repository context for Quarto HTML file"""
        return RepositoryContext(
            service="github",
            owner="test-owner",
            repo="test-repo",
            current_path="_site/docs/guide.html",
            ref="main",
            access_token="test-token"
        )

    @pytest.fixture
    def regular_repository_context(self):
        """Create repository context for regular markdown file"""
        return RepositoryContext(
            service="github",
            owner="test-owner",
            repo="test-repo",
            current_path="docs/guide.md",
            ref="main",
            access_token="test-token"
        )

    @pytest.mark.asyncio
    async def test_resolve_optimal_path_quarto_html_with_comment(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test optimal path resolution for Quarto HTML with source comment"""
        factory, git_service = mock_git_service_factory
        
        # Mock HTML content with Quarto source comment
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
            <!-- source: docs/guide.qmd -->
        </head>
        <body><h1>Test</h1></body>
        </html>
        """
        
        # Mock QMD content
        qmd_content = """
        ---
        title: "Test Guide"
        ---
        
        # Test Guide
        This is the source QMD content.
        """
        
        # Setup git service mocks
        git_service.get_file_content.side_effect = [
            html_content,  # First call: HTML content for analysis
            qmd_content,   # Second call: QMD existence check
        ]
        
        # Test optimal path resolution
        result = await conversation_manager._resolve_optimal_document_path(quarto_repository_context)
        
        assert result == "docs/guide.qmd"
        assert git_service.get_file_content.call_count == 2

    @pytest.mark.asyncio
    async def test_resolve_optimal_path_quarto_html_with_config(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test optimal path resolution using _quarto.yml configuration"""
        factory, git_service = mock_git_service_factory
        
        # Mock HTML content without source metadata
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
        </head>
        <body><h1>Test</h1></body>
        </html>
        """
        
        # Mock _quarto.yml content
        config_content = """
        project:
          type: website
          output-dir: _site
        """
        
        # Mock QMD content
        qmd_content = "# Test Guide"
        
        # Setup git service mocks
        git_service.get_file_content.side_effect = [
            html_content,   # HTML content for analysis
            config_content, # _quarto.yml content
            qmd_content,    # QMD existence check
        ]
        
        # Test optimal path resolution
        result = await conversation_manager._resolve_optimal_document_path(quarto_repository_context)
        
        assert result == "docs/guide.qmd"
        assert git_service.get_file_content.call_count == 3

    @pytest.mark.asyncio
    async def test_resolve_optimal_path_quarto_html_standard_patterns(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test optimal path resolution using standard patterns"""
        factory, git_service = mock_git_service_factory
        
        # Mock HTML content without source metadata
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
        </head>
        <body><h1>Test</h1></body>
        </html>
        """
        
        # Mock QMD content
        qmd_content = "# Test Guide"
        
        # Setup git service mocks - config file not found, but QMD exists
        def mock_get_file_content(owner, repo, path, ref):
            if path == "_site/docs/guide.html":
                return html_content
            elif path == "_quarto.yml":
                raise Exception("File not found")
            elif path == "docs/guide.qmd":
                return qmd_content
            else:
                raise Exception("File not found")
        
        git_service.get_file_content.side_effect = mock_get_file_content
        
        # Test optimal path resolution
        result = await conversation_manager._resolve_optimal_document_path(quarto_repository_context)
        
        assert result == "docs/guide.qmd"

    @pytest.mark.asyncio
    async def test_resolve_optimal_path_non_html_file(
        self, conversation_manager, regular_repository_context
    ):
        """Test that non-HTML files are returned unchanged"""
        result = await conversation_manager._resolve_optimal_document_path(regular_repository_context)
        assert result == "docs/guide.md"

    @pytest.mark.asyncio
    async def test_resolve_optimal_path_non_quarto_html(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test optimal path resolution for non-Quarto HTML"""
        factory, git_service = mock_git_service_factory
        
        # Mock regular HTML content (not Quarto)
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Hugo">
            <title>Regular HTML</title>
        </head>
        <body><h1>Not Quarto</h1></body>
        </html>
        """
        
        git_service.get_file_content.return_value = html_content
        
        result = await conversation_manager._resolve_optimal_document_path(quarto_repository_context)
        
        # Should return original path since it's not Quarto HTML
        assert result == "_site/docs/guide.html"

    @pytest.mark.asyncio
    async def test_resolve_optimal_path_qmd_not_found(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test fallback when QMD source file doesn't exist"""
        factory, git_service = mock_git_service_factory
        
        # Mock HTML content with source comment
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
            <!-- source: docs/guide.qmd -->
        </head>
        <body><h1>Test</h1></body>
        </html>
        """
        
        # Setup git service mocks - HTML exists, QMD doesn't
        def mock_get_file_content(owner, repo, path, ref):
            if path == "_site/docs/guide.html":
                return html_content
            elif path == "docs/guide.qmd":
                raise Exception("File not found")
            else:
                raise Exception("File not found")
        
        git_service.get_file_content.side_effect = mock_get_file_content
        
        result = await conversation_manager._resolve_optimal_document_path(quarto_repository_context)
        
        # Should return original HTML path since QMD doesn't exist
        assert result == "_site/docs/guide.html"

    @pytest.mark.asyncio
    async def test_file_exists_true(self, conversation_manager, mock_git_service_factory):
        """Test _file_exists method when file exists"""
        factory, git_service = mock_git_service_factory
        git_service.get_file_content.return_value = "file content"
        
        context = RepositoryContext(
            service="github",
            owner="test-owner",
            repo="test-repo",
            current_path="test.md",
            ref="main"
        )
        
        result = await conversation_manager._file_exists(git_service, context, "test.md")
        assert result is True

    @pytest.mark.asyncio
    async def test_file_exists_false(self, conversation_manager, mock_git_service_factory):
        """Test _file_exists method when file doesn't exist"""
        factory, git_service = mock_git_service_factory
        git_service.get_file_content.side_effect = Exception("File not found")
        
        context = RepositoryContext(
            service="github",
            owner="test-owner",
            repo="test-repo",
            current_path="test.md",
            ref="main"
        )
        
        result = await conversation_manager._file_exists(git_service, context, "test.md")
        assert result is False

    @pytest.mark.asyncio
    async def test_fetch_document_content_with_quarto_resolution(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test _fetch_document_content with Quarto path resolution"""
        factory, git_service = mock_git_service_factory
        
        # Mock HTML content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
            <!-- source: docs/guide.qmd -->
        </head>
        <body><h1>Test</h1></body>
        </html>
        """
        
        # Mock QMD content
        qmd_content = """---
title: "Test Guide"
---

# Test Guide
This is the QMD source content for LLM.
"""
        
        # Mock document response
        mock_document_response = Mock()
        mock_document_response.content.content = qmd_content
        
        # Setup git service mocks
        git_service.get_file_content.side_effect = [
            html_content,  # HTML content for analysis
            qmd_content,   # QMD existence check
        ]
        git_service.get_document.return_value = mock_document_response
        
        # Test document content fetching
        result = await conversation_manager._fetch_document_content(quarto_repository_context)
        
        assert result == qmd_content
        # Verify that get_document was called with the resolved QMD path
        git_service.get_document.assert_called_once_with(
            owner="test-owner",
            repo="test-repo", 
            path="docs/guide.qmd",
            ref="main"
        )

    @pytest.mark.asyncio
    async def test_fetch_document_content_error_handling(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test error handling in _fetch_document_content"""
        factory, git_service = mock_git_service_factory
        
        # Mock document response が必要
        mock_document_response = Mock()
        mock_document_response.content.content = "content"
        
        # get_file_content でエラー、get_document は成功
        git_service.get_file_content.side_effect = Exception("Network error")
        git_service.get_document.return_value = mock_document_response
        
        # エラーが発生しても HTMLパスで処理を続行
        result = await conversation_manager._fetch_document_content(quarto_repository_context)
        assert result == "content"

    @pytest.mark.asyncio
    async def test_create_document_aware_conversation_with_quarto(
        self, conversation_manager, mock_git_service_factory, quarto_repository_context
    ):
        """Test full conversation creation with Quarto path resolution"""
        factory, git_service = mock_git_service_factory
        
        # Mock HTML and QMD content
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <meta name="generator" content="Quarto 1.3.450">
            <!-- source: docs/guide.qmd -->
        </head>
        <body><h1>Test</h1></body>
        </html>
        """
        
        qmd_content = """---
title: "Test Guide"
---

# Test Guide
This is QMD content for the LLM.
"""
        
        # Mock document response
        mock_document_response = Mock()
        mock_document_response.content.content = qmd_content
        
        # Setup git service mocks for path resolution
        def mock_get_file_content(owner, repo, path, ref):
            if path == "_site/docs/guide.html":
                return html_content
            elif path == "docs/guide.qmd":
                return qmd_content
            else:
                raise Exception("File not found")
        
        git_service.get_file_content.side_effect = mock_get_file_content
        git_service.get_document.return_value = mock_document_response
        
        # Test conversation creation
        conversation = await conversation_manager.create_document_aware_conversation(
            repository_context=quarto_repository_context,
            initial_prompt="Explain this document"
        )
        
        assert len(conversation) == 3
        assert conversation[0].role == "system"
        assert conversation[1].role == "assistant"
        assert conversation[2].role == "user"
        
        # Verify that the assistant message contains QMD content
        assert qmd_content in conversation[1].content
        assert "docs/guide.qmd" in conversation[1].content