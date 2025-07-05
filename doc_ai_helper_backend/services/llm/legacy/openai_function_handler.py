"""
OpenAI Function Calling handler.

This module handles function calling specific operations for OpenAI service,
including tool execution and follow-up queries.
"""

import logging
from typing import Dict, Any, Optional, List, TYPE_CHECKING

if TYPE_CHECKING:
    from doc_ai_helper_backend.models.llm import (
        MessageItem,
        FunctionDefinition,
        ToolChoice,
    )
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

from doc_ai_helper_backend.models.llm import LLMResponse, MessageItem
from doc_ai_helper_backend.core.exceptions import LLMServiceException

logger = logging.getLogger(__name__)


class OpenAIFunctionHandler:
    """Handler for OpenAI Function Calling operations."""

    def __init__(
        self, api_client, response_converter, options_builder, mcp_adapter=None
    ):
        """
        Initialize the function handler.

        Args:
            api_client: OpenAI API client
            response_converter: Response converter
            options_builder: Options builder
            mcp_adapter: MCP adapter for function execution
        """
        self.api_client = api_client
        self.response_converter = response_converter
        self.options_builder = options_builder
        self.mcp_adapter = mcp_adapter

    async def query_with_tools(
        self,
        prompt: str,
        tools: List["FunctionDefinition"],
        conversation_history: Optional[List["MessageItem"]] = None,
        options: Optional[Dict[str, Any]] = None,
        tool_choice: Optional["ToolChoice"] = None,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        Query with tools/functions available.

        Args:
            prompt: The prompt to send
            tools: Available tools/functions
            conversation_history: Previous messages
            options: Additional options
            tool_choice: Tool choice strategy
            repository_context: Repository context
            document_metadata: Document metadata
            document_content: Document content
            system_prompt_template: System prompt template
            include_document_in_system_prompt: Whether to include document content

        Returns:
            LLMResponse: The response from the LLM
        """
        options = options or {}

        # Add tools to options
        options["tools"] = tools
        if tool_choice:
            options["tool_choice"] = tool_choice

        # Generate system prompt if needed
        system_prompt = self._generate_system_prompt(
            repository_context,
            document_metadata,
            document_content,
            system_prompt_template,
            include_document_in_system_prompt,
        )

        # Prepare options
        query_options = self.options_builder.prepare_options(
            prompt, options, conversation_history, system_prompt=system_prompt
        )
        model = query_options.get("model", self.options_builder.default_model)

        try:
            # Make API call
            response = await self.api_client.call_api(query_options)

            # Convert response
            llm_response = self.response_converter.convert_to_llm_response(
                response, model
            )

            logger.info(f"Query with tools completed, model: {model}")
            return llm_response

        except Exception as e:
            logger.error(f"Error in query_with_tools: {str(e)}")
            raise LLMServiceException(f"Query with tools failed: {str(e)}")

    async def query_with_tools_and_followup(
        self,
        prompt: str,
        tools: List["FunctionDefinition"],
        conversation_history: Optional[List["MessageItem"]] = None,
        options: Optional[Dict[str, Any]] = None,
        tool_choice: Optional["ToolChoice"] = None,
        max_iterations: int = 3,
        repository_context: Optional["RepositoryContext"] = None,
        document_metadata: Optional["DocumentMetadata"] = None,
        document_content: Optional[str] = None,
        system_prompt_template: str = "contextual_document_assistant_ja",
        include_document_in_system_prompt: bool = True,
    ) -> LLMResponse:
        """
        Query with tools and automatic follow-up for tool calls.

        Args:
            prompt: The prompt to send
            tools: Available tools/functions
            conversation_history: Previous messages
            options: Additional options
            tool_choice: Tool choice strategy
            max_iterations: Maximum number of tool call iterations
            repository_context: Repository context
            document_metadata: Document metadata
            document_content: Document content
            system_prompt_template: System prompt template
            include_document_in_system_prompt: Whether to include document content

        Returns:
            LLMResponse: The final response after all tool calls
        """
        if not self.mcp_adapter:
            raise LLMServiceException(
                "MCP adapter not available for function execution"
            )

        # Initialize conversation with history
        current_conversation = (
            list(conversation_history) if conversation_history else []
        )

        # Add initial user message
        current_conversation.append(MessageItem(role="user", content=prompt))

        iteration = 0
        while iteration < max_iterations:
            logger.info(f"Tool execution iteration {iteration + 1}/{max_iterations}")

            # Query with tools
            response = await self.query_with_tools(
                prompt="",  # Empty prompt since we're using conversation history
                tools=tools,
                conversation_history=current_conversation,
                options=options,
                tool_choice=tool_choice,
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                system_prompt_template=system_prompt_template,
                include_document_in_system_prompt=include_document_in_system_prompt,
            )

            # Add assistant response to conversation
            assistant_message = MessageItem(
                role="assistant",
                content=response.content,
                tool_calls=response.tool_calls,
            )
            current_conversation.append(assistant_message)

            # Check if there are tool calls to execute
            if not response.tool_calls:
                logger.info("No tool calls in response, finishing")
                return response

            # Execute tool calls
            tool_results = []
            for tool_call in response.tool_calls:
                try:
                    result = await self.execute_function_call(
                        tool_call.function.name, tool_call.function.arguments
                    )
                    tool_results.append(
                        {"tool_call_id": tool_call.id, "result": result}
                    )
                    logger.info(f"Executed tool {tool_call.function.name}")
                except Exception as e:
                    error_msg = f"Error executing {tool_call.function.name}: {str(e)}"
                    logger.error(error_msg)
                    tool_results.append(
                        {"tool_call_id": tool_call.id, "result": {"error": error_msg}}
                    )

            # Add tool results to conversation
            for tool_result in tool_results:
                tool_message = MessageItem(
                    role="tool",
                    content=str(tool_result["result"]),
                    tool_call_id=tool_result["tool_call_id"],
                )
                current_conversation.append(tool_message)

            iteration += 1

        # If we've reached max iterations, return the last response
        logger.warning(f"Reached maximum iterations ({max_iterations})")
        return response

    async def get_available_functions(self) -> List["FunctionDefinition"]:
        """
        Get available functions from MCP adapter.

        Returns:
            List[FunctionDefinition]: Available functions
        """
        if not self.mcp_adapter:
            logger.warning("MCP adapter not available")
            return []

        try:
            return await self.mcp_adapter.get_available_functions()
        except Exception as e:
            logger.error(f"Error getting available functions: {str(e)}")
            return []

    async def execute_function_call(
        self, function_name: str, arguments: str
    ) -> Dict[str, Any]:
        """
        Execute a function call using the MCP adapter.

        Args:
            function_name: Name of the function to call
            arguments: JSON string of function arguments

        Returns:
            Dict[str, Any]: The result of the function call
        """
        if not self.mcp_adapter:
            raise LLMServiceException(
                "MCP adapter not available for function execution"
            )

        try:
            return await self.mcp_adapter.execute_function(function_name, arguments)
        except Exception as e:
            logger.error(f"Error executing function {function_name}: {str(e)}")
            raise LLMServiceException(f"Function execution failed: {str(e)}")

    def _generate_system_prompt(
        self,
        repository_context: Optional["RepositoryContext"],
        document_metadata: Optional["DocumentMetadata"],
        document_content: Optional[str],
        system_prompt_template: str,
        include_document_in_system_prompt: bool,
    ) -> Optional[str]:
        """
        Generate system prompt if repository context is provided.

        Args:
            repository_context: Repository context
            document_metadata: Document metadata
            document_content: Document content
            system_prompt_template: Template ID
            include_document_in_system_prompt: Whether to include document content

        Returns:
            Optional[str]: Generated system prompt or None
        """
        if not repository_context or not include_document_in_system_prompt:
            return None

        try:
            # Import here to avoid circular imports
            from doc_ai_helper_backend.services.llm.utils import JapaneseSystemPromptBuilder

            system_prompt_builder = JapaneseSystemPromptBuilder()
            return system_prompt_builder.build_system_prompt(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content=document_content,
                template_id=system_prompt_template,
            )
        except Exception as e:
            logger.warning(f"Failed to generate system prompt: {e}")
            return self._create_fallback_system_prompt(repository_context)

    def _create_fallback_system_prompt(
        self, repository_context: Optional["RepositoryContext"]
    ) -> str:
        """
        Create a fallback system prompt.

        Args:
            repository_context: Repository context

        Returns:
            str: Fallback system prompt
        """
        if repository_context:
            return (
                f"あなたは{repository_context.repository}リポジトリの"
                f"ドキュメントアシスタントです。"
                f"ユーザーの質問に対して、提供されたコンテキストを基に回答してください。"
            )
        else:
            return "あなたは親切なアシスタントです。ユーザーの質問に回答してください。"
