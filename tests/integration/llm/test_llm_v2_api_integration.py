"""
Integration tests for LLM v2 API endpoints.

This module tests the new structured API endpoints to ensure they work
correctly and provide the expected improvements over the legacy format.
"""

import pytest
import httpx
import json
from unittest.mock import patch, AsyncMock
from datetime import datetime

from doc_ai_helper_backend.main import app
from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    CoreQueryRequest,
    ToolConfiguration,
    DocumentContext,
    ProcessingOptions,
)


class TestLLMAPIIntegration:
    """Integration tests for LLM API endpoints with structured parameters."""
    
    @pytest.mark.asyncio
    async def test_query_basic_request(self):
        """Test basic query endpoint functionality."""
        request_data = {
            "query": {
                "prompt": "Hello, world!",
                "provider": "mock",
                "model": "mock-model"
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "content" in data
        assert "model" in data
        assert "provider" in data
        assert "usage" in data
        assert data["provider"] == "mock"
    
    @pytest.mark.asyncio
    async def test_query_with_tools(self):
        """Test v2 query with tool configuration."""
        request_data = {
            "query": {
                "prompt": "Analyze this document",
                "provider": "mock"
            },
            "tools": {
                "enable_tools": True,
                "tool_choice": "auto",
                "complete_tool_flow": True
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        
        # Tools may or may not be called depending on mock behavior
        # The important thing is the request doesn't fail
    
    @pytest.mark.asyncio
    async def test_query_with_document_context(self):
        """Test v2 query with document integration."""
        request_data = {
            "query": {
                "prompt": "Summarize this document",
                "provider": "mock"
            },
            "document": {
                "repository_context": {
                    "service": "github",
                    "owner": "microsoft",
                    "repo": "vscode",
                    "current_path": "README.md",
                    "ref": "main"
                },
                "auto_include_document": True,
                "context_documents": ["README.md"]
            }
        }
        
        # Mock Git service for document fetching
        with patch("doc_ai_helper_backend.services.git.factory.GitServiceFactory.create") as mock_create:
            mock_git_service = AsyncMock()
            mock_create.return_value = mock_git_service
            
            # Mock document response
            from doc_ai_helper_backend.models.document import DocumentResponse, DocumentContent, DocumentMetadata, DocumentType
            mock_document_content = DocumentContent(content="# Test Document\nContent here")
            mock_document_metadata = DocumentMetadata(
                size=1024,
                last_modified=datetime.now(),
                content_type="text/markdown"
            )
            mock_document_response = DocumentResponse(
                path="README.md",
                name="README.md",
                type=DocumentType.MARKDOWN,
                content=mock_document_content,
                metadata=mock_document_metadata,
                repository="vscode",
                owner="microsoft",
                service="github",
                ref="main",
                links=[]
            )
            mock_git_service.get_document.return_value = mock_document_response
            
            async with httpx.AsyncClient(
                transport=httpx.ASGITransport(app=app), base_url="http://test"
            ) as client:
                response = await client.post("/api/v1/llm/query", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert "content" in data
    
    @pytest.mark.asyncio
    async def test_query_with_processing_options(self):
        """Test v2 query with processing options."""
        request_data = {
            "query": {
                "prompt": "Test prompt",
                "provider": "mock"
            },
            "processing": {
                "disable_cache": True,
                "options": {
                    "temperature": 0.7,
                    "max_tokens": 100
                }
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
    
    @pytest.mark.asyncio
    async def test_query_full_request(self):
        """Test v2 query with all parameter groups."""
        request_data = {
            "query": {
                "prompt": "Analyze this code and suggest improvements",
                "provider": "mock",
                "model": "mock-model",
                "conversation_history": [
                    {"role": "user", "content": "Hello"},
                    {"role": "assistant", "content": "Hi there!"}
                ]
            },
            "tools": {
                "enable_tools": True,
                "tool_choice": "auto",
                "complete_tool_flow": True
            },
            "document": {
                "repository_context": {
                    "service": "github",
                    "owner": "microsoft",
                    "repo": "vscode",
                    "current_path": "src/main.py",
                    "ref": "main"
                },
                "auto_include_document": False,  # Disabled since conversation history exists
                "context_documents": ["main.py", "utils.py"]
            },
            "processing": {
                "disable_cache": True,
                "options": {
                    "temperature": 0.8,
                    "max_tokens": 200
                }
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "provider" in data
        assert data["provider"] == "mock"
    
    @pytest.mark.asyncio
    async def test_stream_basic(self):
        """Test basic v2 streaming endpoint."""
        request_data = {
            "query": {
                "prompt": "Tell me a story",
                "provider": "mock"
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            async with client.stream("POST", "/api/v1/llm/stream", json=request_data) as response:
                assert response.status_code == 200
                assert response.headers["content-type"] == "text/event-stream; charset=utf-8"
                
                # Collect streaming events
                events = []
                async for line in response.aiter_lines():
                    if line.strip():
                        try:
                            # Parse SSE data
                            if line.startswith("data: "):
                                data = json.loads(line[6:])
                                events.append(data)
                        except json.JSONDecodeError:
                            pass
                
                # Should have received some events
                assert len(events) > 0
                
                # Should have a completion event
                done_events = [e for e in events if e.get("done") is True]
                assert len(done_events) > 0
    
    @pytest.mark.asyncio
    async def test_validation_error(self):
        """Test v2 endpoint validation error handling."""
        # Invalid request: empty prompt
        request_data = {
            "query": {
                "prompt": "",  # Invalid: empty prompt
                "provider": "mock"
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data
    
    @pytest.mark.asyncio
    async def test_unsupported_provider(self):
        """Test v2 endpoint with unsupported provider."""
        request_data = {
            "query": {
                "prompt": "Test prompt",
                "provider": "unsupported_provider"
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "validation_errors" in data["detail"]
    
    @pytest.mark.asyncio
    async def test_provider_info_endpoint(self):
        """Test provider information endpoint."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/llm/providers")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "available_providers" in data
        assert "all_supported_providers" in data
        assert "provider_details" in data
        assert "total_available" in data
        assert "total_supported" in data
        
        # Should include mock provider
        assert "mock" in data["all_supported_providers"]
        assert "mock" in data["available_providers"]
    
    @pytest.mark.asyncio
    async def test_provider_status_endpoint(self):
        """Test specific provider status endpoint."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/llm/providers/mock/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Verify response structure
        assert "provider" in data
        assert "supported" in data
        assert "configured" in data
        assert "available" in data
        assert data["provider"] == "mock"
        assert data["supported"] is True
        assert data["available"] is True
    
    @pytest.mark.asyncio
    async def test_provider_status_nonexistent(self):
        """Test provider status for nonexistent provider."""
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.get("/api/v1/llm/providers/nonexistent/status")
        
        assert response.status_code == 200
        data = response.json()
        
        # Should return status indicating not supported
        assert "provider" in data
        assert "supported" in data
        assert data["provider"] == "nonexistent"
        assert data["supported"] is False
    
    @pytest.mark.asyncio
    async def test_conversation_history_handling(self):
        """Test that v2 endpoints handle conversation history correctly."""
        conversation_history = [
            {"role": "user", "content": "What is Python?"},
            {"role": "assistant", "content": "Python is a programming language."},
            {"role": "user", "content": "Tell me more about it."}
        ]
        
        request_data = {
            "query": {
                "prompt": "What are its main features?",
                "provider": "mock",
                "conversation_history": conversation_history
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        
        # Should include optimized conversation history
        assert "optimized_conversation_history" in data
        assert data["optimized_conversation_history"] is not None
    
    @pytest.mark.asyncio
    async def test_parameter_validation_detailed(self):
        """Test detailed parameter validation in v2 endpoints."""
        # Test invalid temperature
        request_data = {
            "query": {
                "prompt": "Test prompt",
                "provider": "mock"
            },
            "processing": {
                "options": {
                    "temperature": 5.0  # Invalid: > 2.0
                }
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "detail" in data
        assert "validation_errors" in data["detail"]
        
        # Should include specific temperature validation error
        validation_errors = data["detail"]["validation_errors"]
        temp_errors = [err for err in validation_errors if "temperature" in err.lower()]
        assert len(temp_errors) > 0


