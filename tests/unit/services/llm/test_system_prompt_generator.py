"""
Test cases for system prompt generation functionality.

システムプロンプト生成機能のテストケース群。
"""

import pytest
from unittest.mock import patch, MagicMock

from doc_ai_helper_backend.services.llm.system_prompt_generator import (
    generate_system_prompt,
    _build_bilingual_tool_system_prompt,
)
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    GitService,
    DocumentType,
)


class TestGenerateSystemPrompt:
    """Test system prompt generation functionality."""

    def test_generate_system_prompt_with_full_context(self):
        """Test system prompt generation with full context."""
        # Setup
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main",
            current_path="docs/README.md",
            base_url="https://api.github.com"
        )
        
        document_metadata = DocumentMetadata(
            type=DocumentType.MARKDOWN,
            filename="README.md",
            file_size=1024,
            last_modified=None
        )
        
        document_content = "# Test Document\n\nThis is a test document content."
        
        # Execute
        result = generate_system_prompt(
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert result is not None
        assert "BILINGUAL TOOL EXECUTION SYSTEM" in result
        assert "リポジトリ: test-owner/test-repo" in result
        assert "現在のファイル: docs/README.md" in result
        assert "このファイルはドキュメントファイルです。" in result
        assert "ファイルサイズ: 1024 bytes" in result
        assert "=== 現在のドキュメント内容 ===" in result
        assert "# Test Document" in result
        assert "=== ドキュメント内容ここまで ===" in result

    def test_generate_system_prompt_disabled(self):
        """Test system prompt generation when disabled."""
        # Setup
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main",
            current_path="test.py",
            base_url="https://api.github.com"
        )
        
        # Execute
        result = generate_system_prompt(
            repository_context=repository_context,
            include_document_in_system_prompt=False
        )
        
        # Assert
        assert result is None

    def test_generate_system_prompt_minimal_context(self):
        """Test system prompt generation with minimal context."""
        # Execute
        result = generate_system_prompt(
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert result is not None
        assert "BILINGUAL TOOL EXECUTION SYSTEM" in result
        # Should not contain repository or document specific information
        assert "リポジトリ:" not in result
        assert "現在のファイル:" not in result
        assert "=== 現在のドキュメント内容 ===" not in result

    def test_generate_system_prompt_with_repository_only(self):
        """Test system prompt generation with repository context only."""
        # Setup
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main",
            current_path="src/main.py",
            base_url="https://api.github.com"
        )
        
        # Execute
        result = generate_system_prompt(
            repository_context=repository_context,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert result is not None
        assert "BILINGUAL TOOL EXECUTION SYSTEM" in result
        assert "リポジトリ: test-owner/test-repo" in result
        assert "現在のファイル: src/main.py" in result
        assert "=== 現在のドキュメント内容 ===" not in result

    def test_generate_system_prompt_with_document_metadata_code_file(self):
        """Test system prompt generation with code file metadata."""
        # Setup
        document_metadata = DocumentMetadata(
            type=DocumentType.PYTHON,
            filename="main.py",
            file_size=2048,
            last_modified=None
        )
        
        # Execute
        result = generate_system_prompt(
            document_metadata=document_metadata,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert result is not None
        assert "このファイルはコードファイルです。" in result
        assert "ファイルサイズ: 2048 bytes" in result

    def test_generate_system_prompt_with_document_metadata_various_types(self):
        """Test system prompt generation with various document types."""
        test_cases = [
            (DocumentType.JAVASCRIPT, "このファイルはコードファイルです。"),
            (DocumentType.JSON, "このファイルはコードファイルです。"),
            (DocumentType.YAML, "このファイルはコードファイルです。"),
            (DocumentType.HTML, "このファイルはドキュメントファイルです。"),
            (DocumentType.TEXT, "このファイルはドキュメントファイルです。"),
            (DocumentType.OTHER, "ファイルタイプ: other"),
        ]
        
        for doc_type, expected_text in test_cases:
            document_metadata = DocumentMetadata(
                type=doc_type,
                filename="test.file",
                file_size=1024,
                last_modified=None
            )
            
            result = generate_system_prompt(
                document_metadata=document_metadata,
                include_document_in_system_prompt=True
            )
            
            assert result is not None
            assert expected_text in result

    def test_generate_system_prompt_with_long_document_content(self):
        """Test system prompt generation with long document content (truncation)."""
        # Setup
        long_content = "A" * 10000  # Content longer than max_content_length (8000)
        
        with patch('doc_ai_helper_backend.services.llm.system_prompt_generator.logger') as mock_logger:
            # Execute
            result = generate_system_prompt(
                document_content=long_content,
                include_document_in_system_prompt=True
            )
            
            # Assert
            assert result is not None
            assert "=== 現在のドキュメント内容 ===" in result
            assert "...(内容が長いため省略されました)" in result
            assert len(result) < len(long_content) + 1000  # Should be significantly shorter
            mock_logger.info.assert_called()
            assert "Document content truncated" in str(mock_logger.info.call_args)

    def test_generate_system_prompt_with_normal_document_content(self):
        """Test system prompt generation with normal length document content."""
        # Setup
        normal_content = "Normal length content"
        
        with patch('doc_ai_helper_backend.services.llm.system_prompt_generator.logger') as mock_logger:
            # Execute
            result = generate_system_prompt(
                document_content=normal_content,
                include_document_in_system_prompt=True
            )
            
            # Assert
            assert result is not None
            assert "=== 現在のドキュメント内容 ===" in result
            assert normal_content in result
            assert "...(内容が長いため省略されました)" not in result
            mock_logger.info.assert_called()
            assert "Full document content included" in str(mock_logger.info.call_args)

    def test_generate_system_prompt_exception_handling(self):
        """Test system prompt generation with exception handling."""
        # Setup - create an actual exception by passing an invalid argument
        with patch('doc_ai_helper_backend.services.llm.system_prompt_generator.logger') as mock_logger:
            # Force an exception by manipulating the function directly
            with patch('doc_ai_helper_backend.services.llm.system_prompt_generator._build_bilingual_tool_system_prompt') as mock_bilingual:
                mock_bilingual.side_effect = Exception("Test exception")
                
                # Execute
                result = generate_system_prompt(
                    include_document_in_system_prompt=True
                )
                
                # Assert
                assert result is None
                mock_logger.warning.assert_called()
                assert "Failed to generate system prompt" in str(mock_logger.warning.call_args)

    def test_generate_system_prompt_without_current_path(self):
        """Test system prompt generation with repository context but no current path."""
        # Setup
        repository_context = RepositoryContext(
            service=GitService.GITHUB,
            owner="test-owner",
            repo="test-repo",
            ref="main",
            current_path=None,  # No current path
            base_url="https://api.github.com"
        )
        
        # Execute
        result = generate_system_prompt(
            repository_context=repository_context,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert result is not None
        assert "リポジトリ: test-owner/test-repo" in result
        assert "現在のファイル:" not in result


class TestBuildBilingualToolSystemPrompt:
    """Test bilingual tool system prompt building."""

    def test_build_bilingual_tool_system_prompt(self):
        """Test bilingual tool system prompt building."""
        # Execute
        result = _build_bilingual_tool_system_prompt()
        
        # Assert
        assert result is not None
        assert isinstance(result, str)
        assert "BILINGUAL TOOL EXECUTION SYSTEM" in result
        assert "TOOL SELECTION" in result
        assert "TOOL EXECUTION" in result
        assert "RESPONSE LANGUAGE" in result
        assert "PRIORITY" in result
        
        # Check for specific tool examples
        assert "summarize_document_with_llm" in result
        assert "create_improvement_recommendations_with_llm" in result
        assert "create_git_issue" in result
        
        # Check for bilingual instructions
        assert "日本語" in result
        assert "Execute ALL requested tools" in result
        assert "auto_include_document=True" in result


class TestSystemPromptGeneratorIntegration:
    """Integration tests for system prompt generator."""

    def test_complete_workflow_with_all_components(self):
        """Test complete workflow with all components present."""
        # Setup
        repository_context = RepositoryContext(
            service=GitService.FORGEJO,
            owner="example-org",
            repo="example-project",
            ref="feature-branch",
            current_path="src/utils/helper.js",
            base_url="https://git.example.com"
        )
        
        document_metadata = DocumentMetadata(
            type=DocumentType.JAVASCRIPT,
            filename="helper.js",
            file_size=3456,
            last_modified=None
        )
        
        document_content = """
function calculateSum(a, b) {
    return a + b;
}

module.exports = { calculateSum };
        """.strip()
        
        # Execute
        result = generate_system_prompt(
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            include_document_in_system_prompt=True
        )
        
        # Assert
        assert result is not None
        
        # Check all components are included
        assert "BILINGUAL TOOL EXECUTION SYSTEM" in result
        assert "リポジトリ: example-org/example-project" in result
        assert "現在のファイル: src/utils/helper.js" in result
        assert "このファイルはコードファイルです。" in result
        assert "ファイルサイズ: 3456 bytes" in result
        assert "=== 現在のドキュメント内容 ===" in result
        assert "function calculateSum" in result
        assert "=== ドキュメント内容ここまで ===" in result
        assert "上記のドキュメント内容を参考にして" in result
        
        # Verify the order of components
        lines = result.split('\n')
        bilingual_index = next(i for i, line in enumerate(lines) if "BILINGUAL TOOL EXECUTION SYSTEM" in line)
        repo_index = next(i for i, line in enumerate(lines) if "リポジトリ:" in line)
        content_start_index = next(i for i, line in enumerate(lines) if "=== 現在のドキュメント内容 ===" in line)
        
        assert bilingual_index < repo_index < content_start_index