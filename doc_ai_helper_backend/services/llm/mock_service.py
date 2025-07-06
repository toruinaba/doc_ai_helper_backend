"""
Mock LLM service for development and testing using composition pattern.

This module provides a mock implementation of the LLM service interface
using composition with LLMServiceCommon for shared functionality.
"""

import json
import time
import uuid
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    FunctionCall,
    ToolChoice,
    ToolCall,
)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.common import LLMServiceCommon


class MockLLMService(LLMServiceBase):
    """
    Mock implementation of the LLM service using composition pattern.

    This service returns predefined responses for testing and development.
    Uses composition pattern with LLMServiceCommon for shared functionality.
    """

    def __init__(
        self, response_delay: float = 1.0, default_model: str = "mock-model", **kwargs
    ):
        """
        Initialize the mock LLM service.

        Args:
            response_delay: Delay in seconds before returning response (to simulate network latency)
            default_model: Default model name to use
            **kwargs: Additional configuration options
        """
        # Initialize common functionality through composition
        self._common = LLMServiceCommon()

        self.response_delay = response_delay
        self.default_model = default_model
        self.additional_options = kwargs

        # Predefined responses for different query patterns
        self.response_patterns = {
            "hello": "Hello! I'm a mock LLM assistant. How can I help you today?",
            "help": "I'm a mock LLM service used for testing. You can ask me anything, but I'll respond with predefined answers.",
            "error": "I'm simulating an error response for testing purposes.",
            "time": f"The current mock time is {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "version": "Mock LLM Service v1.0.0",
        }

    # === Interface methods (delegated to common implementation) ===

    async def query(
        self,
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
        Send a query to the mock LLM.

        This method delegates to LLMServiceCommon for standard processing.
        """
        return await self._common.query(
            service=self,
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
        Stream a query to the mock LLM.

        This method delegates to LLMServiceCommon for standard processing.
        """
        async for chunk in self._common.stream_query(
            service=self,
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
        Query with tools using LLMServiceCommon.

        This method delegates to LLMServiceCommon for standard processing.
        """
        return await self._common.query_with_tools(
            service=self,
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
        Query with tools and followup using LLMServiceCommon.

        This method delegates to LLMServiceCommon for standard processing.
        """
        return await self._common.query_with_tools_and_followup(
            service=self,
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

    async def execute_function_call(
        self, function_call: FunctionCall, available_functions: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Execute function call using LLMServiceCommon."""
        return await self._common.execute_function_call(
            function_call, available_functions
        )

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """Get available functions using LLMServiceCommon."""
        return await self._common.get_available_functions()

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """Format prompt using mock implementation."""
        try:
            # Try using the common implementation first
            return await self._common.format_prompt(template_id, variables)
        except Exception as e:
            # If template not found or error, provide mock formatting
            if "not found" in str(e).lower():
                # Mock template formatting for testing
                formatted_vars = ", ".join([f"{k}={v}" for k, v in variables.items()])
                return f"Mock template '{template_id}' with variables: {formatted_vars}"
            else:
                # For other errors, return error message with variables
                return f"Error formatting template '{template_id}': {str(e)}. Variables: {variables}"

    async def get_available_templates(self) -> List[str]:
        """Get available templates using mock implementation."""
        try:
            # Try using the common implementation first
            return await self._common.get_available_templates()
        except Exception:
            # If error, return mock template list
            return ["mock_template", "simple_template", "test_template"]

    # === Provider-specific abstract method implementations ===

    async def _prepare_provider_options(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[FunctionDefinition]] = None,
        tool_choice: Optional[ToolChoice] = None,
    ) -> Dict[str, Any]:
        """Prepare mock provider options."""
        prepared_options = options.copy() if options else {}
        prepared_options["model"] = prepared_options.get("model", self.default_model)
        prepared_options["prompt"] = prompt
        prepared_options["system_prompt"] = system_prompt
        prepared_options["tools"] = tools
        prepared_options["tool_choice"] = tool_choice

        # Check if conversation history contains system messages
        has_system_in_history = False
        if conversation_history:
            has_system_in_history = any(
                msg.role == MessageRole.SYSTEM for msg in conversation_history
            )

        prepared_options["has_system_in_history"] = has_system_in_history
        return prepared_options

    async def _call_provider_api(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """Mock provider API call."""
        # Simulate delay
        await self._simulate_delay()

        prompt = options.get("prompt", "")

        # Check for error simulation
        if any(
            keyword in prompt.lower()
            for keyword in ["simulate_error", "force_error", "test_error"]
        ):
            from doc_ai_helper_backend.core.exceptions import LLMServiceException

            raise LLMServiceException("Simulated error for testing purposes")

        # Check for system context
        system_prompt = options.get("system_prompt")
        has_system_in_history = options.get("has_system_in_history", False)

        # Generate mock response considering system context
        if (
            has_system_in_history or system_prompt
        ) and "continue our conversation" in prompt.lower():
            content = "I understand you want to continue our conversation. As your assistant, I'm ready to help with any questions you may have."
        else:
            content = self._generate_simple_response(prompt, system_prompt)

        return {
            "content": content,
            "model": options.get("model", self.default_model),
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": (len(prompt) // 4) + (len(content) // 4),
            },
            "id": f"mock-{int(time.time())}",
            "created": int(time.time()),
        }

    async def _stream_provider_api(
        self, options: Dict[str, Any]
    ) -> AsyncGenerator[str, None]:
        """Mock streaming provider API call."""
        prompt = options.get("prompt", "")

        # Check for error simulation
        if any(
            keyword in prompt.lower()
            for keyword in ["simulate_error", "force_error", "test_error"]
        ):
            from doc_ai_helper_backend.core.exceptions import LLMServiceException

            raise LLMServiceException("Simulated error for testing purposes")

        # Get full response first
        response = await self._call_provider_api(options)
        content = response["content"]

        # Split into chunks
        chunk_size = 15
        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]
            delay = min(0.1, self.response_delay / (len(content) / chunk_size))
            await asyncio.sleep(delay)
            yield chunk

    async def _convert_provider_response(
        self, raw_response: Dict[str, Any], options: Dict[str, Any]
    ) -> LLMResponse:
        """Convert mock provider response to LLMResponse."""
        usage_data = raw_response.get("usage", {})

        response = LLMResponse(
            content=raw_response.get("content", ""),
            model=raw_response.get("model", self.default_model),
            provider="mock",
            usage=LLMUsage(
                prompt_tokens=usage_data.get("prompt_tokens", 0),
                completion_tokens=usage_data.get("completion_tokens", 0),
                total_tokens=usage_data.get("total_tokens", 0),
            ),
            raw_response=raw_response,
        )

        # Add conversation history optimization info for test compatibility
        response.history_optimization_info = {
            "was_optimized": False,
            "reason": "Mock service does not optimize conversation history",
            "original_length": 0,
            "optimized_length": 0,
        }

        # Set optimized_conversation_history for test compatibility
        response.optimized_conversation_history = []

        return response

    def _generate_simple_response(
        self, prompt: str, system_prompt: Optional[str] = None
    ) -> str:
        """Generate a simple mock response."""
        # Check for pattern matches first
        prompt_lower = prompt.lower()

        for pattern, response in self.response_patterns.items():
            if pattern in prompt_lower:
                return response

        # Handle conversation history references
        if "前の質問" in prompt or "previous question" in prompt:
            return "What is Python?"  # This matches test expectations

        # Handle previous answer references
        if "前の回答" in prompt or "previous answer" in prompt:
            return "Python is a programming language."

        # Handle conversation continuation
        if "continue our conversation" in prompt_lower:
            if system_prompt:
                return "I understand you want to continue our conversation. As your assistant, I'm ready to help with any questions you may have."
            else:
                return "Let's continue our conversation. How can I assist you further?"

        # Check system prompt context
        if system_prompt:
            if "microsoft/vscode" in system_prompt:
                return f"I understand you're asking about Visual Studio Code. {prompt}"
            elif "github.com" in system_prompt or "repository" in system_prompt.lower():
                return (
                    f"I received your question about this repository context. {prompt}"
                )

        # Default responses
        if "?" in prompt:
            return "That's an interesting question. As a mock LLM, I'd provide a detailed answer here."
        elif len(prompt) < 20:
            return f"I received your short prompt: '{prompt}'. This is a mock response."
        else:
            return (
                f"I received your prompt of {len(prompt)} characters. "
                "In a real LLM service, I would analyze this and provide a thoughtful response. "
                "This is just a mock response for development and testing purposes."
            )

    async def get_capabilities(self) -> ProviderCapabilities:
        """Get the capabilities of the mock LLM provider."""
        return ProviderCapabilities(
            available_models=["mock-model", "mock-model-large", "mock-model-small"],
            max_tokens={
                "mock-model": 4096,
                "mock-model-large": 8192,
                "mock-model-small": 2048,
            },
            supports_streaming=True,
            supports_function_calling=True,
            supports_vision=False,
        )

    async def estimate_tokens(self, text: str) -> int:
        """Estimate the number of tokens in a text."""
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    async def _simulate_delay(self) -> None:
        """Simulate network and processing delay."""
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

    # === Property accessors for compatibility ===

    @property
    def function_manager(self):
        """Get the function manager from common implementation."""
        return self._common.function_manager

    @property
    def cache_service(self):
        """Get the cache service from common implementation."""
        return self._common.cache_service

    @property
    def template_manager(self):
        """Get the template manager from common implementation."""
        return self._common.template_manager

    @property
    def system_prompt_builder(self):
        """Get the system prompt builder from common implementation."""
        return self._common.system_prompt_builder

    @property
    def mcp_adapter(self):
        """Get the MCP adapter from common implementation."""
        return self._common.get_mcp_adapter()

    # === MCP adapter methods (delegated to common) ===

    def set_mcp_adapter(self, adapter):
        """Set the MCP adapter through common implementation."""
        self._common.set_mcp_adapter(adapter)

    def get_mcp_adapter(self):
        """Get the MCP adapter from common implementation."""
        return self._common.get_mcp_adapter()

    # === Test utility methods (for backward compatibility) ===

    def _should_call_github_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests a GitHub/Git operation should be performed.

        This method is used by tests to verify function calling logic.
        """
        github_keywords = [
            "create issue",
            "create an issue",
            "report bug",
            "report issue",
            "create pr",
            "create pull request",
            "submit pr",
            "submit a pr",
            "make pr",
            "make a pr",
            "check permissions",
            "check repository",
            "check access",
            "post to github",
            "post this to github",
            "submit to github",
            "create in github",
            "create git issue",
            "create git pr",
            "git issue",
            "git pull request",
            "github issue",
            "github pr",
            "github pull request",
        ]

        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in github_keywords)

    def _should_call_utility_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests a utility operation should be performed.

        This method is used by tests to verify function calling logic.
        """
        utility_keywords = [
            "current time",
            "what time",
            "time is",
            "clock",
            "now",
            "count",
            "character",
            "length",
            "how many",
            "word count",
            "email",
            "validate",
            "valid",
            "check email",
            "random",
            "generate",
            "random data",
            "uuid",
            "calculate",
            "math",
            "compute",
            "add",
            "subtract",
            "multiply",
            "divide",
        ]

        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in utility_keywords)

    def _should_call_analysis_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests an analysis operation should be performed.

        This method is used by tests to verify function calling logic.
        """
        analysis_keywords = [
            "analyze",
            "analysis",
            "examine",
            "review",
            "study",
            "evaluate",
            "assess",
            "text",
            "document",
            "content",
            "structure",
        ]

        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in analysis_keywords)

    def _generate_contextual_response(
        self,
        prompt: str,
        history: List[MessageItem],
        system_prompt: Optional[str] = None,
    ) -> str:
        """
        会話履歴を考慮した応答を生成する。

        This method is used by tests to verify conversation handling.
        """
        # Handle conversation continuation with system context
        if "continue our conversation" in prompt.lower() and system_prompt:
            return "I understand you want to continue our conversation. As your assistant, I'm ready to help with any questions you may have."

        # If system prompt is provided, include relevant information in response
        if system_prompt:
            if "microsoft/vscode" in system_prompt:
                return f"Based on our conversation history and the Visual Studio Code context, I understand: {prompt}"
            elif "test/minimal" in system_prompt:
                return f"Considering our previous exchanges about the test/minimal repository: {prompt}"
            elif "github.com" in system_prompt or "repository" in system_prompt.lower():
                return f"Taking into account the repository context and our conversation: {prompt}"

        # パターンに一致する応答があればそれを使用
        for pattern, response in self.response_patterns.items():
            if pattern.lower() in prompt.lower():
                return f"{response} (会話履歴を考慮しています)"

        # historyが空または不正な場合のデフォルト処理
        if not history or not isinstance(history, list):
            # Include the prompt in the response for test compatibility
            simple_response = self._generate_simple_response(prompt, system_prompt)
            if prompt in simple_response:
                return simple_response
            else:
                return f"Contextual response for: {prompt}. " + simple_response

        # 有効なMessageItemのみをフィルタ
        valid_history = [
            msg for msg in history if hasattr(msg, "role") and hasattr(msg, "content")
        ]

        # システムメッセージがあるかチェック
        system_messages = [
            msg for msg in valid_history if msg.role == MessageRole.SYSTEM
        ]
        has_system_message = len(system_messages) > 0

        # 前回の質問を参照する場合
        if "前の質問" in prompt.lower() or "previous question" in prompt.lower():
            for msg in reversed(valid_history):
                if msg.role == MessageRole.USER and msg.content != prompt:
                    return f"前の質問は「{msg.content}」でした。"

        # 過去の回答を参照する場合
        if (
            "前の回答" in prompt.lower()
            or "previous answer" in prompt.lower()
            or "last response" in prompt.lower()
        ):
            for msg in reversed(valid_history):
                if msg.role == MessageRole.ASSISTANT:
                    return f"前回の回答は「{msg.content}」でした。"

        # 会話の長さに基づく応答
        if len(valid_history) > 2:
            base_response = f"会話の文脈を考慮した応答です。これまでに{len(valid_history)}回のやり取りがありました。"
            if has_system_message:
                system_info = f" システム指示 [system] が設定されています: 「{system_messages[0].content[:30]}...」"
                return f"{base_response}{system_info}\n実際のプロンプト: {prompt}"
            return f"{base_response}\n実際のプロンプト: {prompt}"

        # 会話履歴の要約
        conversation_summary = "\n".join(
            [f"[{msg.role.value}]: {msg.content[:30]}..." for msg in history[-3:]]
        )

        # デフォルトの応答
        return f"これはモック応答です。会話履歴に基づいて生成されました。\n\n最近の会話:\n{conversation_summary}\n\n現在の質問: {prompt}"
