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

            # 5. Handle tool execution and followup if tools were called
            if llm_response.tool_calls:
                logger.info(f"Tool calls detected: {len(llm_response.tool_calls)}, executing tools and generating followup response")
                
                # Execute all tool calls
                executed_results = []
                for tool_call in llm_response.tool_calls:
                    try:
                        # Convert repository context to dict if available
                        repo_context_dict = None
                        if repository_context:
                            repo_context_dict = {
                                "service": repository_context.service.value if hasattr(repository_context.service, 'value') else repository_context.service,
                                "owner": repository_context.owner,
                                "repo": repository_context.repo,
                                "ref": repository_context.ref,
                                "current_path": repository_context.current_path,
                                "base_url": repository_context.base_url,
                            }
                        
                        # Get available functions mapping
                        available_functions = {func.name: func for func in tools}
                        
                        # Execute the tool call
                        result = await service.execute_function_call(
                            tool_call.function,
                            available_functions,
                            repository_context=repo_context_dict,
                        )
                        
                        executed_results.append({
                            "tool_call_id": tool_call.id,
                            "function_name": tool_call.function.name,
                            "result": result,
                        })
                        
                        logger.info(f"Tool '{tool_call.function.name}' executed successfully")
                        
                    except Exception as e:
                        executed_results.append({
                            "tool_call_id": tool_call.id,  
                            "function_name": tool_call.function.name,
                            "error": str(e),
                        })
                        logger.error(f"Tool '{tool_call.function.name}' execution failed: {e}")

                # Add execution results to response
                llm_response.tool_execution_results = executed_results
                
                # Generate followup response based on tool execution results
                followup_response = await self._generate_followup_response(
                    service=service,
                    original_prompt=prompt,
                    tool_calls=llm_response.tool_calls,
                    tool_results=executed_results,
                    conversation_history=conversation_history,
                    system_prompt=system_prompt,
                    options=options or {},
                )
                
                # Update the main response content with followup
                if followup_response and followup_response.content:
                    llm_response.content = followup_response.content
                    # Update usage if available
                    if followup_response.usage and llm_response.usage:
                        llm_response.usage.prompt_tokens += followup_response.usage.prompt_tokens
                        llm_response.usage.completion_tokens += followup_response.usage.completion_tokens
                        llm_response.usage.total_tokens += followup_response.usage.total_tokens
                    
                    logger.info(f"Followup response generated: {len(llm_response.content)} characters")
                else:
                    logger.warning("Followup response generation failed or returned empty content")

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
                enable_bilingual_tools=True,  # Enable bilingual tool execution
            )
        except Exception as e:
            logger.warning(
                f"Failed to generate system prompt: {str(e)}, continuing without system prompt"
            )
            return None

    async def _generate_followup_response(
        self,
        service: "LLMServiceBase",
        original_prompt: str,
        tool_calls: List,
        tool_results: List[Dict[str, Any]],
        conversation_history: Optional[List[MessageItem]] = None,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> Optional[LLMResponse]:
        """
        Generate a followup response based on tool execution results.
        
        This method constructs a new conversation that includes the original prompt,
        tool calls, and tool results, then asks the LLM to provide a comprehensive
        final response based on all the information.
        """
        try:
            logger.info("Generating followup response based on tool execution results")
            
            # Build the followup conversation history
            followup_history = []
            
            # Add original conversation history if present
            if conversation_history:
                followup_history.extend(conversation_history)
            
            # Add the original user prompt
            followup_history.append(MessageItem(
                role=MessageRole.USER,
                content=original_prompt
            ))
            
            # Add assistant response with tool calls (simplified representation)
            tool_call_summary = []
            for i, tool_call in enumerate(tool_calls):
                tool_call_summary.append(f"{i+1}. {tool_call.function.name}を実行しました")
            
            followup_history.append(MessageItem(
                role=MessageRole.ASSISTANT,
                content=f"以下のツールを実行しました：\n" + "\n".join(tool_call_summary)
            ))
            
            # Add tool results as user messages (simulating tool response)
            tool_results_summary = []
            for result in tool_results:
                function_name = result.get("function_name", "不明なツール")
                if "error" in result:
                    tool_results_summary.append(f"❌ {function_name}: エラーが発生しました - {result['error']}")
                else:
                    # Extract meaningful content from result
                    result_data = result.get("result", {})
                    if isinstance(result_data, dict):
                        if result_data.get("success"):
                            if "result" in result_data and isinstance(result_data["result"], str):
                                # Try to parse JSON result
                                try:
                                    import json
                                    parsed_result = json.loads(result_data["result"])
                                    if isinstance(parsed_result, dict):
                                        if "summary" in parsed_result:
                                            tool_results_summary.append(f"✅ {function_name}: 要約が生成されました")
                                        elif "recommendations" in parsed_result:
                                            tool_results_summary.append(f"✅ {function_name}: 改善提案が生成されました")
                                        else:
                                            tool_results_summary.append(f"✅ {function_name}: 分析が完了しました")
                                    else:
                                        tool_results_summary.append(f"✅ {function_name}: 処理が完了しました")
                                except json.JSONDecodeError:
                                    tool_results_summary.append(f"✅ {function_name}: 結果を取得しました")
                            else:
                                tool_results_summary.append(f"✅ {function_name}: 実行完了")
                        else:
                            tool_results_summary.append(f"❌ {function_name}: {result_data.get('error', '実行に失敗しました')}")
                    else:
                        tool_results_summary.append(f"✅ {function_name}: 実行完了")
            
            # Create followup prompt asking for comprehensive response
            followup_prompt = f"""上記のツール実行結果を踏まえて、以下の内容で包括的な回答を日本語で提供してください：

ツール実行結果：
{chr(10).join(tool_results_summary)}

元のリクエストに対する完全な回答を、ツール実行結果を統合して作成してください。具体的で実用的な内容を含め、ユーザーに価値のある情報を提供してください。"""
            
            followup_history.append(MessageItem(
                role=MessageRole.USER,
                content=followup_prompt
            ))
            
            # Prepare options for followup call (disable tools to avoid recursion)
            followup_options = (options or {}).copy()
            followup_options["temperature"] = 0.7  # Slightly more creative for synthesis
            
            # Generate followup response without tools
            followup_provider_options = await service._prepare_provider_options(
                prompt=followup_prompt,
                conversation_history=followup_history[:-1],  # Exclude the followup prompt as it's added separately
                options=followup_options,
                system_prompt=system_prompt,
                tools=None,  # No tools for followup to avoid recursion
                tool_choice=None,
            )
            
            # Call provider API for followup
            followup_raw_response = await service._call_provider_api(followup_provider_options)
            
            # Convert followup response
            followup_response = await service._convert_provider_response(
                followup_raw_response, followup_provider_options
            )
            
            logger.info(f"Followup response generated successfully: {len(followup_response.content) if followup_response.content else 0} characters")
            return followup_response
            
        except Exception as e:
            logger.error(f"Error generating followup response: {str(e)}")
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
