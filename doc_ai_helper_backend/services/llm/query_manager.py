"""
Query management utilities for LLM services.

This module provides query management utilities that coordinate the complete workflow
of LLM queries, including caching, response processing, and provider coordination.
"""

import hashlib
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )
    from doc_ai_helper_backend.services.llm.base import LLMServiceBase

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException
from .messaging import optimize_conversation_history

logger = logging.getLogger(__name__)


class QueryManager:
    """
    Manages the complete workflow of LLM queries.

    This class coordinates the query lifecycle including caching, system prompt generation,
    provider communication, and response processing. It acts as a coordinator between
    different utility classes and the LLM service implementation.
    """

    def __init__(self, cache_service, system_prompt_builder):
        """
        Initialize the query manager.

        Args:
            cache_service: Cache service for response caching
            system_prompt_builder: System prompt builder for context generation
        """
        self.cache_service = cache_service
        self.system_prompt_builder = system_prompt_builder

    async def orchestrate_query(
        self,
        service: "LLMServiceBase",
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        Orchestrate a complete LLM query workflow.

        Args:
            service: The LLM service instance to delegate provider-specific operations to
            prompt: The prompt to send to the LLM
            conversation_history: Previous messages in the conversation for context
            options: Additional options for the query (model, temperature, etc.)
            repository_context: Repository context for system prompt generation
            document_metadata: Document metadata for context
            document_content: Document content to include in system prompt
            system_prompt_template: Template ID for system prompt generation
            include_document_in_system_prompt: Whether to include document content

        Returns:
            LLMResponse: The response from the LLM
        """
        logger.info(
            f"Starting query orchestration with prompt length: {len(prompt or '')}"
        )

        try:
            # Validate prompt
            if prompt is None or not prompt.strip():
                raise LLMServiceException("Prompt cannot be empty")

            # 1. Check cache first
            cache_key = self._generate_cache_key(
                prompt,
                conversation_history,
                options,
                repository_context,
                document_metadata,
                document_content,
                system_prompt_template,
            )

            if cached_response := self.cache_service.get(cache_key):
                logger.info("Returning cached response")
                return cached_response

            # 2. Generate system prompt if needed
            system_prompt = await self._generate_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                system_prompt_template=system_prompt_template,
                include_document_in_system_prompt=include_document_in_system_prompt,
            )

            # 3. Prepare provider-specific options
            provider_options = await service._prepare_provider_options(
                prompt=prompt,
                conversation_history=conversation_history,
                options=options or {},
                system_prompt=system_prompt,
            )

            # 4. Call provider API
            raw_response = await service._call_provider_api(provider_options)

            # 5. Convert response
            llm_response = await service._convert_provider_response(
                raw_response, provider_options
            )

            # 6. Set conversation history optimization information
            if conversation_history:
                optimized_history, optimization_info = optimize_conversation_history(
                    conversation_history, max_tokens=4000
                )
                llm_response.optimized_conversation_history = optimized_history
                llm_response.history_optimization_info = optimization_info
            else:
                llm_response.optimized_conversation_history = []
                llm_response.history_optimization_info = {
                    "was_optimized": False,
                    "reason": "No conversation history provided",
                }

            # 7. Cache result
            self.cache_service.set(cache_key, llm_response)

            logger.info(
                f"Query orchestration completed successfully, model: {llm_response.model}"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error in query orchestration: {str(e)}")
            raise LLMServiceException(f"Query orchestration failed: {str(e)}")

    async def orchestrate_streaming_query(
        self,
        service: "LLMServiceBase",
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Orchestrate a streaming LLM query workflow.
        """
        logger.info(
            f"Starting streaming query orchestration with prompt length: {len(prompt or '')}"
        )

        try:
            # Validate prompt
            if prompt is None or not prompt.strip():
                raise LLMServiceException("Prompt cannot be empty")

            # 1. Generate system prompt if needed
            system_prompt = await self._generate_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                system_prompt_template=system_prompt_template,
                include_document_in_system_prompt=include_document_in_system_prompt,
            )

            # 2. Prepare provider-specific options
            provider_options = await service._prepare_provider_options(
                prompt=prompt,
                conversation_history=conversation_history,
                options=options or {},
                system_prompt=system_prompt,
            )

            # 3. Stream from provider API
            async for chunk in service._stream_provider_api(provider_options):
                yield chunk

            logger.info("Streaming query orchestration completed successfully")

        except Exception as e:
            logger.error(f"Error in streaming query orchestration: {str(e)}")
            raise LLMServiceException(f"Streaming query orchestration failed: {str(e)}")

    async def orchestrate_query_with_tools(
        self,
        service: "LLMServiceBase",
        prompt: str,
        tools: List[FunctionDefinition],
        conversation_history: Optional[List[MessageItem]] = None,
        tool_choice: Optional[ToolChoice] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        Orchestrate a LLM query with tools workflow.
        """
        logger.info(
            f"Starting query with tools orchestration, tools count: {len(tools)}"
        )

        try:
            # 1. Generate system prompt if needed
            system_prompt = await self._generate_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                system_prompt_template=system_prompt_template,
                include_document_in_system_prompt=include_document_in_system_prompt,
            )

            # 2. Prepare provider-specific options with tools
            provider_options = await service._prepare_provider_options(
                prompt=prompt,
                conversation_history=conversation_history,
                options=options or {},
                system_prompt=system_prompt,
                tools=tools,
                tool_choice=tool_choice,
            )

            # 3. Call provider API
            raw_response = await service._call_provider_api(provider_options)

            # 4. Convert response
            llm_response = await service._convert_provider_response(
                raw_response, provider_options
            )

            # 5. Set conversation history optimization information
            if conversation_history:
                optimized_history, optimization_info = optimize_conversation_history(
                    conversation_history, max_tokens=4000
                )
                llm_response.optimized_conversation_history = optimized_history
                llm_response.history_optimization_info = optimization_info
            else:
                llm_response.optimized_conversation_history = []
                llm_response.history_optimization_info = {
                    "was_optimized": False,
                    "reason": "No conversation history provided",
                }

            logger.info(
                f"Query with tools orchestration completed successfully, model: {llm_response.model}"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error in query with tools orchestration: {str(e)}")
            raise LLMServiceException(
                f"Query with tools orchestration failed: {str(e)}"
            )

    def build_conversation_messages(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        system_prompt: Optional[str] = None,
    ) -> List[MessageItem]:
        """
        Build conversation messages in standard format.

        This is common across all providers, though the final format
        will be converted by each provider.
        """
        messages = []

        # Add system prompt if provided
        if system_prompt:
            messages.append(MessageItem(role=MessageRole.SYSTEM, content=system_prompt))

        # Add conversation history
        if conversation_history:
            messages.extend(conversation_history)

        # Add current prompt (only if not empty)
        if prompt.strip():
            messages.append(MessageItem(role=MessageRole.USER, content=prompt))

        return messages

    async def _generate_system_prompt(
        self,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> Optional[str]:
        """Generate system prompt using the system prompt builder."""
        try:
            if not include_document_in_system_prompt:
                return None

            return self.system_prompt_builder.build_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                custom_instructions=None,
                template_id=system_prompt_template,
            )
        except Exception as e:
            logger.warning(
                f"Failed to generate system prompt: {str(e)}, continuing without system prompt"
            )
            return None

    def _generate_cache_key(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
    ) -> str:
        """Generate a cache key for the query."""
        key_data = {
            "prompt": prompt,
            "conversation_history": (
                [msg.model_dump() for msg in conversation_history]
                if conversation_history
                else None
            ),
            "options": options,
            "repository_context": (
                repository_context.model_dump() if repository_context else None
            ),
            "document_metadata": (
                document_metadata.model_dump() if document_metadata else None
            ),
            "document_content": document_content,
            "system_prompt_template": system_prompt_template,
        }

        key_string = str(sorted(key_data.items()))
        return hashlib.md5(key_string.encode()).hexdigest()


# Backward compatibility alias
QueryOrchestrator = QueryManager
