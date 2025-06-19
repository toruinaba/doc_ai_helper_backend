"""
LLM API endpoints.

This module provides the API endpoints for LLM functionality.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sse_starlette.sse import EventSourceResponse

from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    LLMResponse,
    PromptTemplate,
    LLMStreamChunk,
)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.core.exceptions import (
    LLMServiceException,
    TemplateNotFoundError,
    TemplateSyntaxError,
)
from doc_ai_helper_backend.api.dependencies import get_llm_service

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post(
    "/query",
    response_model=LLMResponse,
    summary="Query LLM",
    description="Send a query to an LLM with optional document context",
)
async def query_llm(
    request: LLMQueryRequest,
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Send a query to an LLM.

    Args:
        request: The query request containing prompt and options
        llm_service: The LLM service to use (injected)

    Returns:
        LLMResponse: The response from the LLM
    """
    try:
        # 会話履歴の最適化判定
        optimized_history = None
        optimization_info = None
        conversation_history = request.conversation_history
        
        # 会話履歴が長い場合は要約を実行
        if conversation_history and len(conversation_history) > 10:
            from doc_ai_helper_backend.services.llm.utils import summarize_conversation_history
            try:
                optimized_history, optimization_info = await summarize_conversation_history(
                    conversation_history, 
                    llm_service,
                    max_messages_to_keep=6
                )
                conversation_history = optimized_history
            except Exception as summarize_error:
                # 要約に失敗した場合は元の履歴を使用し、ログに記録
                logger.warning(f"Failed to summarize conversation history: {str(summarize_error)}")
                optimization_info = {
                    "optimization_applied": False, 
                    "error": str(summarize_error)
                }
        
        # Prepare options
        options = request.options or {}
        if request.model:
            options["model"] = request.model

        # Set cache control flag
        if request.disable_cache:
            options["disable_cache"] = True

        # Process context documents if provided
        if request.context_documents:
            options["context_documents"] = request.context_documents

        # Send query to LLM with conversation history
        response = await llm_service.query(
            request.prompt,
            conversation_history=conversation_history,
            options=options,
        )
        
        # 最適化された会話履歴をレスポンスに含める
        if optimized_history is not None:
            # 現在のユーザーメッセージとアシスタントの応答を追加
            from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
            from datetime import datetime
            
            current_user_message = MessageItem(
                role=MessageRole.USER,
                content=request.prompt,
                timestamp=datetime.now()
            )
            
            current_assistant_message = MessageItem(
                role=MessageRole.ASSISTANT,
                content=response.content,
                timestamp=datetime.now()
            )
            
            # フロントエンドが次回使用する最適化済み履歴
            response.optimized_conversation_history = optimized_history + [
                current_user_message,
                current_assistant_message
            ]
            response.history_optimization_info = optimization_info
        
        return response

    except Exception as e:
        raise LLMServiceException(message="Error querying LLM", detail=str(e))


@router.get(
    "/capabilities",
    summary="Get LLM capabilities",
    description="Get the capabilities of the configured LLM provider",
)
async def get_capabilities(
    provider: Optional[str] = Query(
        None, description="LLM provider to check capabilities for"
    ),
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Get the capabilities of an LLM provider.

    Args:
        provider: The provider to check capabilities for (optional)
        llm_service: The LLM service to use (injected)

    Returns:
        dict: The provider capabilities
    """
    try:
        capabilities = await llm_service.get_capabilities()
        return capabilities

    except Exception as e:
        raise LLMServiceException(
            message="Error getting LLM capabilities", detail=str(e)
        )


@router.get(
    "/templates",
    response_model=List[str],
    summary="List available templates",
    description="Get a list of available prompt templates",
)
async def list_templates(
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Get a list of available prompt templates.

    Args:
        llm_service: The LLM service to use (injected)

    Returns:
        List[str]: List of template IDs
    """
    try:
        templates = await llm_service.get_available_templates()
        return templates

    except Exception as e:
        raise LLMServiceException(message="Error listing templates", detail=str(e))


@router.post(
    "/format-prompt",
    response_model=str,
    summary="Format prompt template",
    description="Format a prompt template with provided variables",
)
async def format_prompt(
    request: Dict[str, Any],
    template_id: str = Query(..., description="ID of the template to format"),
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Format a prompt template with variables.

    Args:
        request: The variables to substitute in the template
        template_id: The ID of the template to format
        llm_service: The LLM service to use (injected)

    Returns:
        str: The formatted prompt
    """
    try:
        formatted = await llm_service.format_prompt(template_id, request)
        return formatted

    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateSyntaxError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise LLMServiceException(message="Error formatting template", detail=str(e))


@router.post(
    "/stream",
    summary="Stream LLM response",
    description="Stream response from LLM in real-time using Server-Sent Events (SSE)",
)
async def stream_llm_response(
    request: LLMQueryRequest,
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Stream a response from an LLM.

    Args:
        request: The query request containing prompt and options
        llm_service: The LLM service to use (injected)

    Returns:
        EventSourceResponse: Server-Sent Events response
    """
    # Check if streaming is supported
    capabilities = await llm_service.get_capabilities()
    if not capabilities.supports_streaming:
        raise HTTPException(
            status_code=400,
            detail="The selected LLM provider does not support streaming",
        )

    async def event_generator():
        try:  # Prepare options
            options = request.options or {}
            if request.model:
                options["model"] = request.model

            # Process context documents if provided
            if request.context_documents:
                options["context_documents"] = request.context_documents
            # Stream query to LLM with conversation history
            stream = llm_service.stream_query(
                request.prompt,
                conversation_history=request.conversation_history,
                options=options,
            )
            async for text_chunk in stream:
                # Send each chunk as an SSE event
                yield f"data: {json.dumps({'text': text_chunk})}\n\n"

            # Signal completion
            yield f"data: {json.dumps({'done': True})}\n\n"

        except Exception as e:
            # Send error as an event
            error_msg = str(e)
            yield f"data: {json.dumps({'error': error_msg})}\n\n"

    # Return an SSE response
    return EventSourceResponse(event_generator())
