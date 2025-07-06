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
    MessageItem,
    MessageRole,
    FunctionDefinition,
    FunctionCall,
    ToolChoice,
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
        from doc_ai_helper_backend.services.llm.utils import (
            PromptTemplateManager,
            LLMCacheService,
            JapaneseSystemPromptBuilder,
            FunctionCallManager,
        )

        self.template_manager = PromptTemplateManager()
        self.cache_service = LLMCacheService()
        self.system_prompt_builder = JapaneseSystemPromptBuilder()
        self.function_manager = FunctionCallManager()

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
        Common implementation of query method.

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
        logger.info(f"Starting query with prompt length: {len(prompt or '')}")

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

            # 6. Cache result
            self.cache_service.set(cache_key, llm_response)

            logger.info(f"Query completed successfully, model: {llm_response.model}")
            return llm_response

        except Exception as e:
            logger.error(f"Error in query: {str(e)}")
            raise LLMServiceException(f"Query failed: {str(e)}")

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
        Common implementation of streaming query method.
        """
        logger.info(f"Starting streaming query with prompt length: {len(prompt or '')}")

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

            logger.info("Streaming query completed successfully")

        except Exception as e:
            logger.error(f"Error in streaming query: {str(e)}")
            raise LLMServiceException(f"Streaming query failed: {str(e)}")

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
        Common implementation of query with tools.
        """
        logger.info(f"Starting query with tools, tools count: {len(tools)}")

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

            logger.info(
                f"Query with tools completed successfully, model: {llm_response.model}"
            )
            return llm_response

        except Exception as e:
            logger.error(f"Error in query with tools: {str(e)}")
            raise LLMServiceException(f"Query with tools failed: {str(e)}")

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

    # === Helper methods ===

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
                document_content=document_content,
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
