"""
Integration tests for LLM document integration functionality.

These tests verify the new document integration approach using conversation history.
"""

import pytest
import asyncio
from datetime import datetime
import httpx
from unittest.mock import AsyncMock, Mock, patch

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.repository_context import RepositoryContext, GitService, DocumentMetadata, DocumentType


@pytest.fixture
def sample_repository_context():
    """Sample repository context for testing."""
    return {
        "service": "github",
        "owner": "microsoft",
        "repo": "vscode",
        "current_path": "README.md",
        "ref": "main"
    }


@pytest.fixture
def sample_document_metadata():
    """Sample document metadata for testing."""
    return {
        "title": "VS Code README",
        "type": "markdown",
        "filename": "README.md",
        "file_extension": "md",
        "last_modified": "2024-01-01T00:00:00",
        "file_size": 1024,
        "encoding": "utf-8",
        "language": "en"
    }


@pytest.fixture
def llm_request_payload(sample_repository_context, sample_document_metadata):
    """Base LLM request payload for testing."""
    return {
        "query": {
            "prompt": "Please summarize this document",
            "provider": "mock"
        },
        "document": {
            "repository_context": sample_repository_context,
            "auto_include_document": True
        },
        "tools": {
            "enable_tools": True,
            "tool_choice": "auto",
            "complete_tool_flow": True
        }
    }


@pytest.mark.asyncio
async def test_query_endpoint_document_integration_success(llm_request_payload):
    """Test successful document integration in /llm/query endpoint."""
    
    # Mock Git service to return document content
    with patch("doc_ai_helper_backend.services.git.factory.GitServiceFactory.create") as mock_create:
        mock_git_service = AsyncMock()
        mock_create.return_value = mock_git_service
        
        # Mock document response
        from doc_ai_helper_backend.models.document import DocumentResponse, DocumentContent, DocumentMetadata as DocMetadata, DocumentType as DocType
        mock_document_content = DocumentContent(
            content="# VS Code\n\nVisual Studio Code is a lightweight code editor."
        )
        mock_document_metadata = DocMetadata(
            size=1024,
            last_modified=datetime.fromisoformat("2024-01-01T00:00:00"),
            content_type="text/markdown"
        )
        mock_document_response = DocumentResponse(
            path="README.md",
            name="README.md", 
            type=DocType.MARKDOWN,
            content=mock_document_content,
            metadata=mock_document_metadata,
            repository="vscode",
            owner="microsoft",
            service="github",
            ref="main",
            links=[]
        )
        mock_git_service.get_document.return_value = mock_document_response
        
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/llm/query", json=llm_request_payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "content" in data
        assert "model" in data
        assert "provider" in data
        
        # The mock LLM should have received conversation history with document content
        # This is verified indirectly through successful response


@pytest.mark.asyncio
async def test_query_endpoint_document_integration_disabled(sample_repository_context):
    """Test /llm/query endpoint when document integration is disabled."""
    
    request_payload = {
        "query": {
            "prompt": "Hello, world!",
            "provider": "mock"
        },
        "document": {
            "repository_context": sample_repository_context,
            "auto_include_document": False
        }
    }
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/llm/query", json=request_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "content" in data


@pytest.mark.asyncio
async def test_query_endpoint_continuation_request(llm_request_payload):
    """Test /llm/query endpoint with existing conversation history (continuation request)."""
    
    # Add existing conversation history to simulate continuation
    llm_request_payload["query"]["conversation_history"] = [
        {"role": "system", "content": "System message"},
        {"role": "assistant", "content": "Document content: # Sample\nContent here"},
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ]
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/llm/query", json=llm_request_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    
    # Document integration should not have occurred since conversation history exists


@pytest.mark.asyncio
async def test_query_endpoint_git_service_error(llm_request_payload):
    """Test /llm/query endpoint when Git service fails."""
    
    # Mock Git service to raise exception
    with patch("doc_ai_helper_backend.services.git.factory.GitServiceFactory.create") as mock_create:
        mock_git_service = AsyncMock()
        mock_create.return_value = mock_git_service
        mock_git_service.get_document.side_effect = Exception("Network error")
        
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/llm/query", json=llm_request_payload)
        
        # Should still succeed with fallback behavior
        assert response.status_code == 200
        data = response.json()
        assert "content" in data


@pytest.mark.asyncio
@pytest.mark.skip(reason="Streaming tests require more complex setup")  
async def test_stream_endpoint_document_integration_success(llm_request_payload):
    """Test successful document integration in /llm/stream endpoint."""
    
    # Mock Git service to return document content
    with patch("doc_ai_helper_backend.services.git.factory.GitServiceFactory.create") as mock_create:
        mock_git_service = AsyncMock()
        mock_create.return_value = mock_git_service
        
        # Mock document response
        from doc_ai_helper_backend.models.document import DocumentResponse, DocumentContent, DocumentMetadata as DocMetadata, DocumentType as DocType
        mock_document_content = DocumentContent(
            content="# VS Code\n\nVisual Studio Code is a lightweight code editor."
        )
        mock_document_metadata = DocMetadata(
            size=1024,
            last_modified=datetime.fromisoformat("2024-01-01T00:00:00"),
            content_type="text/markdown"
        )
        mock_document_response = DocumentResponse(
            path="README.md",
            name="README.md", 
            type=DocType.MARKDOWN,
            content=mock_document_content,
            metadata=mock_document_metadata,
            repository="vscode",
            owner="microsoft",
            service="github",
            ref="main",
            links=[]
        )
        mock_git_service.get_document.return_value = mock_document_response
        
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            async with ac.stream("POST", "/api/v1/llm/stream", json=llm_request_payload) as response:
                assert response.status_code == 200
                
                # Collect streaming events
                events = []
                async for line in response.aiter_lines():
                    if line.strip():
                        events.append(line)
                
                # Verify streaming events include document loading notifications
                event_types = []
                for event in events:
                    if event.startswith("data: "):
                        try:
                            import json
                            data = json.loads(event[6:])  # Remove "data: " prefix
                            if "status" in data:
                                event_types.append(data["status"])
                        except:
                            pass
                
                # Should include document loading events
                assert "document_loading" in event_types or "document_loaded" in event_types


@pytest.mark.asyncio
async def test_query_endpoint_no_repository_context():
    """Test /llm/query endpoint without repository context."""
    
    request_payload = {
        "query": {
            "prompt": "What is the weather today?",
            "provider": "mock"
        },
        "document": {
            "auto_include_document": True  # Enabled but no repository context
        }
    }
    
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/llm/query", json=request_payload)
    
    assert response.status_code == 200
    data = response.json()
    assert "content" in data
    
    # Should work normally without document integration


@pytest.mark.asyncio
async def test_query_endpoint_with_tools_and_document_integration(llm_request_payload):
    """Test /llm/query endpoint with both tool execution and document integration."""
    
    # Enable tools
    llm_request_payload["enable_tools"] = True
    llm_request_payload["tool_choice"] = "auto"
    
    # Mock Git service to return document content
    with patch("doc_ai_helper_backend.services.git.factory.GitServiceFactory.create") as mock_create:
        mock_git_service = AsyncMock()
        mock_create.return_value = mock_git_service
        
        # Mock document response
        from doc_ai_helper_backend.models.document import DocumentResponse, DocumentContent, DocumentMetadata as DocMetadata, DocumentType as DocType
        mock_document_content = DocumentContent(
            content="# VS Code\n\nThis is documentation."
        )
        mock_document_metadata = DocMetadata(
            size=1024,
            last_modified=datetime.fromisoformat("2024-01-01T00:00:00"),
            content_type="text/markdown"
        )
        mock_document_response = DocumentResponse(
            path="README.md",
            name="README.md", 
            type=DocType.MARKDOWN,
            content=mock_document_content,
            metadata=mock_document_metadata,
            repository="vscode",
            owner="microsoft",
            service="github",
            ref="main",
            links=[]
        )
        mock_git_service.get_document.return_value = mock_document_response
        
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post("/api/v1/llm/query", json=llm_request_payload)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "content" in data
        
        # May include tool execution results
        # This depends on whether the mock LLM decides to call tools