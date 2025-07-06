"""
LLM service common functionality.

This module provides shared logic for all LLM service implementations using composition pattern.
It consolidates common functionality like caching, system prompt generation, conversation management,
and template handling.
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
    LLMUsage,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    FunctionCall,
    ToolChoice,
    ToolCall,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException

logger = logging.getLogger(__name__)


class LLMServiceCommon:
    """
    Common functionality for LLM services using composition pattern.

    This class provides shared logic that can be used by any LLM service implementation
    through composition, avoiding the complexities of multiple inheritance.
    """

    def __init__(self):
        """Initialize common components."""
        # Import here to avoid circular imports
        from doc_ai_helper_backend.services.llm.components import (
            PromptTemplateManager,
            LLMCacheService,
            SystemPromptBuilder,
            FunctionCallManager,
            ResponseBuilder,
            StreamingUtils,
            QueryManager,
        )

        self.template_manager = PromptTemplateManager()
        self.cache_service = LLMCacheService()
        self.system_prompt_builder = SystemPromptBuilder()
        self.function_manager = FunctionCallManager()

        # Add new utility classes
        self.response_builder = ResponseBuilder()
        self.streaming_utils = StreamingUtils()

        # Add query orchestrator for workflow management
        self.query_manager = QueryManager(
            cache_service=self.cache_service,
            system_prompt_builder=self.system_prompt_builder,
        )

        logger.info("Initialized LLM service common components")

    async def query(
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
        Common implementation of query method (delegated to query orchestrator).
        """
        return await self.query_manager.orchestrate_query(
            service=service,
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

    async def stream_query(
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
        Common implementation of streaming query method (delegated to query orchestrator).
        """
        async for chunk in self.query_manager.orchestrate_streaming_query(
            service=service,
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        ):
            yield chunk

    async def query_with_tools(
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
        Common implementation of query with tools (delegated to query orchestrator).
        """
        return await self.query_manager.orchestrate_query_with_tools(
            service=service,
            prompt=prompt,
            tools=tools,
            conversation_history=conversation_history,
            tool_choice=tool_choice,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

    async def query_with_tools_and_followup(
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
        Common implementation of query with tools and automatic followup.

        This method implements the complete Function Calling flow:
        1. Send initial query with tools
        2. If LLM calls tools, execute them
        3. Send tool results back to LLM for final response
        """
        logger.info(
            f"Starting query with tools and followup, tools count: {len(tools)}"
        )

        try:
            # 1. Initial query with tools
            initial_response = await self.query_with_tools(
                service=service,
                prompt=prompt,
                tools=tools,
                conversation_history=conversation_history,
                tool_choice=tool_choice,
                options=options,
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                system_prompt_template=system_prompt_template,
                include_document_in_system_prompt=include_document_in_system_prompt,
            )

            # 2. Check if tools were called
            if not initial_response.tool_calls:
                logger.info("No tool calls found, returning initial response")
                return initial_response

            # 3. Execute tool calls and prepare followup
            # Note: This is a simplified implementation. In practice, you'd need
            # a function manager to execute the tool calls
            logger.info(f"Tool calls found: {len(initial_response.tool_calls)}")

            # For now, return the initial response with tool calls
            # In a full implementation, you would:
            # - Execute each tool call
            # - Add tool results to conversation history
            # - Make another query to get the final response
            return initial_response

        except Exception as e:
            logger.error(f"Error in query with tools and followup: {str(e)}")
            raise LLMServiceException(f"Query with tools and followup failed: {str(e)}")

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Format a prompt template with variables."""
        return self.template_manager.format_template(template_id, variables)

    async def get_available_templates(self) -> List[str]:
        """Get available template IDs."""
        return self.template_manager.list_templates()

    async def execute_function_call(
        self,
        function_call: FunctionCall,
        available_functions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """Execute a function call requested by the LLM."""
        # Temporary implementation - would use function manager in practice
        logger.warning("Function execution not fully implemented yet")
        return {"error": "Function execution not implemented"}

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """Get the list of available functions for this LLM service."""
        # Temporary implementation - would use function manager in practice
        logger.warning("Function listing not fully implemented yet")
        return []

    # === Helper methods (simplified to reduce class size) ===

    async def _generate_system_prompt(
        self,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> Optional[str]:
        """Generate system prompt using the system prompt builder (delegated to orchestrator)."""
        return await self.query_manager._generate_system_prompt(
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
            include_document_in_system_prompt=include_document_in_system_prompt,
        )

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
        """Generate a cache key for the query (delegated to orchestrator)."""
        return self.query_manager._generate_cache_key(
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            repository_context=repository_context,
            document_metadata=document_metadata,
            document_content=document_content,
            system_prompt_template=system_prompt_template,
        )

    def build_conversation_messages(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        system_prompt: Optional[str] = None,
    ) -> List[MessageItem]:
        """
        Build conversation messages in standard format (delegated to query orchestrator).
        """
        return self.query_manager.build_conversation_messages(
            prompt=prompt,
            conversation_history=conversation_history,
            system_prompt=system_prompt,
        )

    # === Response building helpers ===

    def build_standard_usage(self, usage_data: Dict[str, Any]) -> LLMUsage:
        """Build standardized usage object from provider data."""
        return self.response_builder.build_usage_from_dict(usage_data)

    def build_standard_response(
        self,
        content: str,
        model: str,
        provider: str,
        usage_data: Dict[str, Any],
        raw_response: Any,
        tool_calls: Optional[List[ToolCall]] = None,
        additional_fields: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Build a standardized LLMResponse object.

        This method provides a common interface for building responses across
        all LLM service implementations, ensuring consistency.
        """
        usage = self.build_standard_usage(usage_data)
        return self.response_builder.build_base_response(
            content=content,
            model=model,
            provider=provider,
            usage=usage,
            raw_response=raw_response,
            tool_calls=tool_calls,
            additional_fields=additional_fields,
        )

    def build_openai_response(self, raw_response: Any, model: str) -> LLMResponse:
        """Build LLMResponse from OpenAI API response."""
        return self.response_builder.build_from_openai_response(raw_response, model)

    def build_mock_response(
        self, raw_response: Dict[str, Any], default_model: str
    ) -> LLMResponse:
        """Build LLMResponse from Mock service response."""
        return self.response_builder.build_from_mock_response(
            raw_response, default_model
        )

    # === Streaming helpers ===

    async def chunk_content_for_streaming(
        self,
        content: str,
        chunk_size: int = 15,
        total_delay: float = 0.0,
    ):
        """Chunk content for streaming with configurable parameters."""
        async for chunk in self.streaming_utils.chunk_content(
            content=content,
            chunk_size=chunk_size,
            total_delay=total_delay,
        ):
            yield chunk
