"""
Query processor service for handling LLM request processing logic.

This module provides a centralized service for processing LLM queries,
eliminating code duplication between endpoints and providing a clean
separation of concerns.
"""

import json
import logging
from typing import Dict, Any, List, Optional, Tuple, AsyncGenerator, Union

from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    CoreQueryRequest,
    ToolConfiguration,
    DocumentContext,
    ProcessingOptions,
    LLMResponse,
    MessageItem,
    FunctionDefinition,
    ToolChoice,
)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.conversation_manager import ConversationManager
from doc_ai_helper_backend.core.exceptions import LLMServiceException

logger = logging.getLogger(__name__)


class QueryProcessor:
    """
    Service for processing LLM queries with centralized logic.
    
    This class handles all the common processing logic that was previously
    duplicated between the query and stream endpoints.
    """
    
    def __init__(self, conversation_manager: ConversationManager):
        """
        Initialize QueryProcessor.
        
        Args:
            conversation_manager: Manager for document integration via conversation history
        """
        self.conversation_manager = conversation_manager
    
    async def setup_provider(self, provider: str, **additional_config) -> LLMServiceBase:
        """
        Configure and create LLM service instance.
        
        Args:
            provider: The LLM provider name
            **additional_config: Additional configuration options
            
        Returns:
            LLMServiceBase: Configured LLM service instance
            
        Raises:
            LLMServiceException: If provider setup fails
        """
        try:
            from doc_ai_helper_backend.core.config import settings
            
            # Configure provider-specific settings
            config = {}
            if provider == "openai":
                config["api_key"] = settings.openai_api_key
                config["default_model"] = settings.default_openai_model
                if settings.openai_base_url:
                    config["base_url"] = settings.openai_base_url
            
            # Add any additional config
            config.update(additional_config)
            
            # Create LLM service for the requested provider
            llm_service = LLMServiceFactory.create_with_mcp(provider, **config)
            logger.info(f"Successfully created LLM service for provider: {provider}")
            return llm_service
            
        except Exception as e:
            logger.error(f"Failed to create LLM service for provider '{provider}': {e}")
            raise LLMServiceException(
                message=f"Failed to setup provider '{provider}'",
                detail=str(e)
            )
    
    async def prepare_conversation(
        self,
        core_request: CoreQueryRequest,
        document_context: Optional[DocumentContext] = None
    ) -> List[MessageItem]:
        """
        Handle document integration via conversation manager.
        
        Args:
            core_request: Core query parameters
            document_context: Document integration context
            
        Returns:
            List[MessageItem]: Processed conversation history
        """
        conversation_history = core_request.conversation_history or []
        
        # Check if document integration is needed
        if (document_context and 
            document_context.auto_include_document and
            document_context.repository_context and
            self.conversation_manager.is_initial_request(
                conversation_history, 
                document_context.repository_context
            )):
            try:
                # Create document-aware conversation history
                conversation_history = await self.conversation_manager.create_document_aware_conversation(
                    repository_context=document_context.repository_context,
                    initial_prompt=core_request.prompt,
                    document_metadata=document_context.document_metadata
                )
                logger.info("Document integration: Created document-aware conversation history")
            except Exception as e:
                logger.warning(f"Document integration failed, continuing with original conversation: {e}")
                # Continue with original conversation history if document integration fails
                conversation_history = core_request.conversation_history or []
        
        return conversation_history
    
    async def setup_tools(
        self,
        tool_config: Optional[ToolConfiguration],
        llm_service: LLMServiceBase
    ) -> Tuple[Optional[List[FunctionDefinition]], Optional[ToolChoice]]:
        """
        Prepare tools and tool choice for function calling.
        
        Args:
            tool_config: Tool configuration parameters
            llm_service: LLM service instance
            
        Returns:
            Tuple[Optional[List[FunctionDefinition]], Optional[ToolChoice]]: 
                Available tools and tool choice configuration
        """
        if not tool_config or not tool_config.enable_tools:
            return None, None
        
        # Get available tools from the LLM service
        available_tools = await llm_service.get_available_functions()
        
        # Convert tool_choice string to ToolChoice object
        tool_choice = None
        if tool_config.tool_choice:
            if tool_config.tool_choice in ["auto", "none", "required"]:
                tool_choice = ToolChoice(type=tool_config.tool_choice)  # type: ignore
            else:
                # Assume it's a specific function name
                tool_choice = ToolChoice(
                    type="required", 
                    function={"name": tool_config.tool_choice}
                )
        
        return available_tools, tool_choice
    
    def prepare_processing_options(
        self,
        core_request: CoreQueryRequest,
        processing_options: Optional[ProcessingOptions] = None,
        document_context: Optional[DocumentContext] = None
    ) -> Dict[str, Any]:
        """
        Prepare processing options for the LLM service call.
        
        Args:
            core_request: Core query parameters
            processing_options: Processing configuration
            document_context: Document context for additional options
            
        Returns:
            Dict[str, Any]: Prepared options dictionary
        """
        options = {}
        
        # Add model if specified
        if core_request.model:
            options["model"] = core_request.model
        
        # Add processing options if provided
        if processing_options:
            if processing_options.disable_cache:
                options["disable_cache"] = True
            
            # Merge additional options
            options.update(processing_options.options)
        
        # Add context documents if provided
        if document_context and document_context.context_documents:
            options["context_documents"] = document_context.context_documents
        
        return options
    
    async def execute_query(
        self,
        request: LLMQueryRequest,
        streaming: bool = False
    ) -> Union[LLMResponse, AsyncGenerator[Dict[str, Any], None]]:
        """
        Execute LLM query with the new structured request format.
        
        Args:
            request: Structured LLM query request
            streaming: Whether to return streaming response
            
        Returns:
            Union[LLMResponse, AsyncGenerator]: Query response or streaming generator
        """
        # Setup provider
        llm_service = await self.setup_provider(request.query.provider)
        
        # Prepare conversation history with document integration
        conversation_history = await self.prepare_conversation(
            request.query, 
            request.document
        )
        
        # Setup tools if enabled
        available_tools, tool_choice = await self.setup_tools(
            request.tools, 
            llm_service
        )
        
        # Prepare processing options
        options = self.prepare_processing_options(
            request.query,
            request.processing,
            request.document
        )
        
        # Execute query based on configuration
        if streaming:
            return self._execute_streaming_query(
                llm_service=llm_service,
                request=request,
                conversation_history=conversation_history,
                available_tools=available_tools,
                tool_choice=tool_choice,
                options=options
            )
        else:
            return await self._execute_regular_query(
                llm_service=llm_service,
                request=request,
                conversation_history=conversation_history,
                available_tools=available_tools,
                tool_choice=tool_choice,
                options=options
            )
    
    async def _execute_regular_query(
        self,
        llm_service: LLMServiceBase,
        request: LLMQueryRequest,
        conversation_history: List[MessageItem],
        available_tools: Optional[List[FunctionDefinition]],
        tool_choice: Optional[ToolChoice],
        options: Dict[str, Any]
    ) -> LLMResponse:
        """Execute regular (non-streaming) query."""
        
        if request.tools and request.tools.enable_tools and available_tools:
            # Tool-enabled query
            if request.tools.complete_tool_flow:
                # Use new complete flow
                response = await llm_service.query_with_tools_and_followup(
                    prompt=request.query.prompt,
                    tools=available_tools,
                    conversation_history=conversation_history,
                    tool_choice=tool_choice,
                    options=options,
                    repository_context=request.document.repository_context if request.document else None,
                    document_metadata=request.document.document_metadata if request.document else None,
                    document_content=None,  # Deprecated parameter
                    system_prompt_template="contextual_document_assistant_ja",
                    include_document_in_system_prompt=True,
                )
            else:
                # Use legacy flow
                response = await llm_service.query_with_tools(
                    prompt=request.query.prompt,
                    tools=available_tools,
                    conversation_history=conversation_history,
                    tool_choice=tool_choice,
                    options=options,
                    repository_context=request.document.repository_context if request.document else None,
                    document_metadata=request.document.document_metadata if request.document else None,
                    document_content=None,  # Deprecated parameter
                    system_prompt_template="contextual_document_assistant_ja",
                    include_document_in_system_prompt=True,
                )
                
                # Execute function calls if present (legacy behavior)
                if response.tool_calls:
                    executed_results = []
                    for tool_call in response.tool_calls:
                        try:
                            # Convert repository context to dict if available
                            repo_context_dict = None
                            if request.document and request.document.repository_context:
                                repo_context_dict = request.document.repository_context.model_dump()
                            
                            result = await llm_service.execute_function_call(
                                tool_call.function,
                                {func.name: func for func in available_tools},
                                repository_context=repo_context_dict,
                            )
                            executed_results.append({
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "result": result,
                            })
                        except Exception as e:
                            executed_results.append({
                                "tool_call_id": tool_call.id,
                                "function_name": tool_call.function.name,
                                "error": str(e),
                            })
                    
                    # Add execution results to response
                    response.tool_execution_results = executed_results
        else:
            # Regular query without tools
            response = await llm_service.query(
                request.query.prompt,
                conversation_history=conversation_history,
                options=options,
                repository_context=request.document.repository_context if request.document else None,
                document_metadata=request.document.document_metadata if request.document else None,
                document_content=None,  # Deprecated parameter
                system_prompt_template="contextual_document_assistant_ja",
                include_document_in_system_prompt=True,
            )
        
        return response
    
    async def _execute_streaming_query(
        self,
        llm_service: LLMServiceBase,
        request: LLMQueryRequest,
        conversation_history: List[MessageItem],
        available_tools: Optional[List[FunctionDefinition]],
        tool_choice: Optional[ToolChoice],
        options: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Execute streaming query."""
        
        try:
            # Check if streaming is supported
            capabilities = await llm_service.get_capabilities()
            if not capabilities.supports_streaming:
                yield {"error": "The selected LLM provider does not support streaming"}
                return
            
            # Check if tools/function calling is enabled
            if request.tools and request.tools.enable_tools and available_tools:
                # For streaming with Function Calling, we need to handle it differently
                if request.tools.complete_tool_flow:
                    # Use complete flow with streaming
                    yield {
                        "status": "tools_processing",
                        "message": "Analyzing request and selecting tools...",
                    }
                    
                    # Execute tools first, then stream the final response
                    response = await llm_service.query_with_tools_and_followup(
                        prompt=request.query.prompt,
                        tools=available_tools,
                        conversation_history=conversation_history,
                        tool_choice=tool_choice,
                        options=options,
                    )
                    
                    # Stream the final response content
                    if hasattr(response, "content") and response.content:
                        # Send tool execution info
                        if (hasattr(response, "tool_execution_results") and 
                            response.tool_execution_results):
                            tool_info = {
                                "tools_executed": len(response.tool_execution_results),
                                "tool_names": [
                                    r.get("function_name", "unknown")
                                    for r in response.tool_execution_results
                                ],
                            }
                            yield {"status": "tools_completed", "tool_info": tool_info}
                        
                        # Stream the content word by word for a smooth experience
                        words = response.content.split()
                        for i, word in enumerate(words):
                            chunk = word + (" " if i < len(words) - 1 else "")
                            yield {"text": chunk}
                            # Small delay for smooth streaming effect
                            import asyncio
                            await asyncio.sleep(0.02)
                else:
                    # Legacy flow - execute tools and return results
                    yield {"status": "tools_processing", "message": "Executing tools..."}
                    
                    response = await llm_service.query_with_tools(
                        prompt=request.query.prompt,
                        tools=available_tools,
                        conversation_history=conversation_history,
                        tool_choice=tool_choice,
                        options=options,
                    )
                    
                    # Execute function calls if present
                    if response.tool_calls:
                        executed_results = []
                        for tool_call in response.tool_calls:
                            try:
                                # Convert repository context to dict if available
                                repo_context_dict = None
                                if request.document and request.document.repository_context:
                                    repo_context_dict = request.document.repository_context.model_dump()
                                
                                result = await llm_service.execute_function_call(
                                    tool_call.function,
                                    {func.name: func for func in available_tools},
                                    repository_context=repo_context_dict,
                                )
                                executed_results.append({
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "result": result,
                                })
                                # Send progress update
                                yield {
                                    "status": "tool_executed",
                                    "tool_name": tool_call.function.name,
                                }
                            except Exception as e:
                                executed_results.append({
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "error": str(e),
                                })
                        
                        # Send tool execution results
                        yield {"tool_execution_results": executed_results}
                    
                    # Send any content from the initial response
                    if hasattr(response, "content") and response.content:
                        yield {"text": response.content}
            else:
                # Regular streaming without tools
                async for text_chunk in llm_service.stream_query(
                    request.query.prompt,
                    conversation_history=conversation_history,
                    options=options,
                    repository_context=request.document.repository_context if request.document else None,
                    document_metadata=request.document.document_metadata if request.document else None,
                    document_content=None,  # Deprecated parameter
                    system_prompt_template="contextual_document_assistant_ja",
                    include_document_in_system_prompt=True,
                ):
                    # Send each chunk as an SSE event
                    yield {"text": text_chunk}
            
            # Signal completion
            yield {"done": True}
            
        except Exception as e:
            # Send error as an event
            error_msg = str(e)
            yield {"error": error_msg}