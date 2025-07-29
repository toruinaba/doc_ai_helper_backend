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
        # ServiceNotFoundErrorの場合は、詳細なエラーメッセージが文字列として返される
        assert "unsupported_provider" in data["detail"]
        assert "not found" in data["detail"]
    
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
        # Test invalid prompt (empty string should fail)
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
        
        assert response.status_code == 422  # Pydantic validation error for empty prompt
        data = response.json()
        assert "detail" in data
        # Pydantic validation errors are returned as a list
        assert isinstance(data["detail"], list)
        assert len(data["detail"]) > 0

    @pytest.mark.asyncio
    async def test_conversation_history_optimization_long(self):
        """Test conversation history optimization with very long history to ensure summarization."""
        # Create very long conversation history (100 exchanges to ensure token limit is exceeded)
        conversation_history = []
        for i in range(100):
            conversation_history.extend([
                {
                    "role": "user",
                    "content": f"質問{i+1}: これは{i+1}番目の非常に長い質問です。トークン数を大幅に増やすために、この文章を非常に長くしています。具体的には、日常生活について、仕事について、趣味について、将来の計画について、家族について、友人について、健康について、旅行について、読書について、映画について、音楽について、スポーツについて、料理について、学習について、キャリアについて、投資について、技術について、ニュースについて、環境について、政治について、文化について、芸術について、科学について、歴史について、哲学について、宗教について、心理学について、社会学について、経済学について等々、様々なトピックについて詳細に質問したいと思います。この質問は意図的に非常に長くしてトークン数を増やしています。"
                },
                {
                    "role": "assistant", 
                    "content": f"回答{i+1}: ご質問ありがとうございます。{i+1}番目のご質問にお答えします。詳細な説明をさせていただきますと、このような内容になります。日常生活、仕事、趣味、将来の計画、家族、友人、健康、旅行、読書、映画、音楽、スポーツ、料理、学習、キャリア、投資、技術、ニュース、環境、政治、文化、芸術、科学、歴史、哲学、宗教、心理学、社会学、経済学など、どのトピックについても丁寧にお答えできます。この回答も意図的に長くしてトークン数を増やし、確実に最適化が発生するようにしています。各トピックについて詳しく説明することで、より具体的で有用な情報を提供できます。"
                }
            ])

        request_data = {
            "query": {
                "prompt": "この会話をまとめてください。",
                "provider": "mock",
                "conversation_history": conversation_history
            },
            "processing": {
                "options": {
                    "temperature": 0.7
                }
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
        assert "optimized_conversation_history" in data
        assert "history_optimization_info" in data
        
        # Verify optimization occurred
        assert data["optimized_conversation_history"] is not None
        assert data["history_optimization_info"] is not None
        
        # Check that optimization reduced the conversation length
        original_count = len(conversation_history)
        optimized_count = len(data["optimized_conversation_history"])
        
        # Mock provider should optimize long conversations
        assert optimized_count < original_count, f"Expected optimization: {optimized_count} < {original_count}"
        assert data["history_optimization_info"]["was_optimized"] is True

    @pytest.mark.asyncio
    async def test_conversation_history_with_system_message(self):
        """Test conversation history handling with system messages preserved."""
        request_data = {
            "query": {
                "prompt": "前回の話の続きをお願いします。",
                "provider": "mock",
                "conversation_history": [
                    {
                        "role": "system",
                        "content": "あなたは親切なアシスタントです。常に丁寧に回答してください。"
                    },
                    {
                        "role": "user", 
                        "content": "プロジェクトの進捗について相談があります。"
                    },
                    {
                        "role": "assistant",
                        "content": "プロジェクトの進捗についてご相談いただき、ありがとうございます。どのような点についてお聞かせください？"
                    }
                ]
            },
            "processing": {
                "options": {
                    "temperature": 0.7
                }
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
        assert "optimized_conversation_history" in data
        
        # System message should be preserved in optimized history
        optimized_history = data["optimized_conversation_history"]
        system_messages = [msg for msg in optimized_history if msg["role"] == "system"]
        assert len(system_messages) > 0, "System message should be preserved"
        assert system_messages[0]["content"] == "あなたは親切なアシスタントです。常に丁寧に回答してください。"

    @pytest.mark.asyncio
    async def test_conversation_history_empty_and_none(self):
        """Test handling of empty and None conversation history."""
        # Test with empty conversation history
        request_data_empty = {
            "query": {
                "prompt": "初回の質問です。",
                "provider": "mock",
                "conversation_history": []
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data_empty)
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "optimized_conversation_history" in data
        assert isinstance(data["optimized_conversation_history"], list)
        
        # Test with no conversation history field (None)
        request_data_none = {
            "query": {
                "prompt": "初回の質問です。",
                "provider": "mock"
                # conversation_history is intentionally omitted
            }
        }
        
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            response = await client.post("/api/v1/llm/query", json=request_data_none)
        
        assert response.status_code == 200
        data = response.json()
        assert "content" in data
        assert "optimized_conversation_history" in data
        assert isinstance(data["optimized_conversation_history"], list)
        assert len(data["optimized_conversation_history"]) == 0  # Should be empty list for None case


