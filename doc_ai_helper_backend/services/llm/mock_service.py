"""
Mock LLM service for development and testing.

This module provides a mock implementation of the LLM service interface.
"""

import json
import time
import os
import uuid
import asyncio
from typing import Dict, Any, Optional, List, AsyncGenerator

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
from doc_ai_helper_backend.services.llm.template_manager import PromptTemplateManager
from doc_ai_helper_backend.services.llm.utils import optimize_conversation_history


class MockLLMService(LLMServiceBase):
    """
    Mock implementation of the LLM service interface.

    This service returns predefined responses for testing and development.
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
        self.response_delay = response_delay
        self.default_model = default_model
        self.template_manager = PromptTemplateManager()

        # Predefined responses for different query patterns
        self.response_patterns = {
            "hello": "Hello! I'm a mock LLM assistant. How can I help you today?",
            "help": "I'm a mock LLM service used for testing. You can ask me anything, but I'll respond with predefined answers.",
            "error": "I'm simulating an error response for testing purposes.",
            "time": f"The current mock time is {time.strftime('%Y-%m-%d %H:%M:%S')}",
            "version": "Mock LLM Service v1.0.0",
        }

    async def query(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Send a query to the mock LLM.

        Args:
            prompt: The prompt to send
            conversation_history: Previous messages in the conversation
            options: Additional options for the query

        Returns:
            LLMResponse: A mock response

        Raises:
            Exception: If error simulation is requested
        """
        if options is None:
            options = {}

        # Check for error simulation requests
        if prompt and any(
            keyword in prompt.lower()
            for keyword in ["simulate_error", "force_error", "test_error"]
        ):
            from doc_ai_helper_backend.core.exceptions import LLMServiceException

            raise LLMServiceException("Simulated error for testing purposes")

        # Check for empty prompts
        if not prompt or prompt.strip() == "":
            from doc_ai_helper_backend.core.exceptions import LLMServiceException

            raise LLMServiceException("Prompt cannot be empty")

        # Simulate processing delay
        await self._simulate_delay()  # Determine which model to use
        model = options.get(
            "model", self.default_model
        )  # Check if function calling is requested
        functions = options.get("functions", [])
        github_functions = []
        utility_functions = []
        if functions:
            github_functions = [
                f
                for f in functions
                if hasattr(f, "name") and "github" in f.name.lower()
            ]
            utility_functions = [
                f
                for f in functions
                if hasattr(f, "name")
                and any(
                    keyword in f.name.lower()
                    for keyword in ["time", "count", "email", "random", "calculate"]
                )
            ]

        # Generate appropriate response
        tool_calls = []
        if github_functions and self._should_call_github_function(prompt):
            # Simulate GitHub function calling
            tool_calls = self._generate_mock_github_tool_calls(prompt, github_functions)
            content = "I'll help you with that GitHub operation."
        elif utility_functions and self._should_call_utility_function(prompt):
            # Simulate utility function calling
            tool_calls = self._generate_mock_utility_tool_calls(
                prompt, utility_functions
            )
            content = "I'll help you with that utility operation."
        else:
            # Generate normal response
            if conversation_history:
                content = self._generate_contextual_response(
                    prompt, conversation_history
                )
            else:
                content = self._generate_response(prompt)  # Calculate mock token usage
        prompt_tokens = len(prompt) // 4
        completion_tokens = len(content) // 4  # Create response
        response = LLMResponse(
            content=content,
            model=model,
            provider="mock",
            usage=LLMUsage(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=prompt_tokens + completion_tokens,
            ),
            raw_response={
                "id": f"mock-{int(time.time())}",
                "created": int(time.time()),
                "model": model,
                "content": content,
            },
            tool_calls=tool_calls if tool_calls else None,
        )

        # Optimize conversation history if provided
        if conversation_history:
            optimized_history, optimization_info = optimize_conversation_history(
                conversation_history, max_tokens=4000
            )
            response.optimized_conversation_history = optimized_history
            response.history_optimization_info = optimization_info
        else:
            # No conversation history provided
            response.optimized_conversation_history = []
            response.history_optimization_info = {
                "was_optimized": False,
                "reason": "No conversation history provided",
            }

        return response

    async def get_capabilities(self) -> ProviderCapabilities:
        """
        Get the capabilities of the mock LLM provider.

        Returns:
            ProviderCapabilities: Mock capabilities
        """
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

    async def format_prompt(self, template_id: str, variables: Dict[str, Any]) -> str:
        """
        Format a prompt template with variables.

        Args:
            template_id: The ID of the template to use
            variables: The variables to substitute in the template

        Returns:
            str: The formatted prompt
        """
        try:
            return self.template_manager.format_template(template_id, variables)
        except Exception as e:
            # In case of error, return a simple concatenation of variables
            return f"Template '{template_id}' with variables: {json.dumps(variables)}"

    async def get_available_templates(self) -> List[str]:
        """
        Get a list of available prompt template IDs.

        Returns:
            List[str]: List of template IDs
        """
        return self.template_manager.list_templates()

    async def estimate_tokens(self, text: str) -> int:
        """
        Estimate the number of tokens in a text.

        Args:
            text: The text to estimate tokens for

        Returns:
            int: Estimated token count
        """
        # Simple estimation: ~4 characters per token
        return len(text) // 4

    async def _simulate_delay(self) -> None:
        """
        Simulate network and processing delay.
        """
        if self.response_delay > 0:
            await asyncio.sleep(self.response_delay)

    def _generate_response(self, prompt: str) -> str:
        """
        Generate a response based on the prompt.

        Args:
            prompt: The input prompt

        Returns:
            str: A mock response
        """
        # Check for pattern matches
        prompt_lower = prompt.lower()

        for pattern, response in self.response_patterns.items():
            if pattern in prompt_lower:
                return response

        # Default response for no pattern match
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

    def _generate_contextual_response(
        self, prompt: str, history: List[MessageItem]
    ) -> str:
        """
        会話履歴を考慮した応答を生成する。

        Args:
            prompt: 現在のプロンプト
            history: 会話履歴

        Returns:
            str: 生成された応答
        """
        # パターンに一致する応答があればそれを使用
        for pattern, response in self.response_patterns.items():
            if pattern.lower() in prompt.lower():
                return f"{response} (会話履歴を考慮しています)"

        # システムメッセージがあるかチェック
        system_messages = [msg for msg in history if msg.role == MessageRole.SYSTEM]
        has_system_message = len(system_messages) > 0

        # 前回の質問を参照する場合
        if "前の質問" in prompt.lower() or "previous question" in prompt.lower():
            for msg in reversed(history):
                if msg.role == MessageRole.USER and msg.content != prompt:
                    return f"前の質問は「{msg.content}」でした。"

        # 過去の回答を参照する場合
        if (
            "前の回答" in prompt.lower()
            or "previous answer" in prompt.lower()
            or "last response" in prompt.lower()
        ):
            for msg in reversed(history):
                if msg.role == MessageRole.ASSISTANT:
                    return f"前回の回答は「{msg.content}」でした。"

        # 会話の長さに基づく応答
        if len(history) > 2:
            base_response = f"会話の文脈を考慮した応答です。これまでに{len(history)}回のやり取りがありました。"
            if has_system_message:
                system_info = f" システム指示 [system] が設定されています: 「{system_messages[0].content[:30]}...」"
                return f"{base_response}{system_info}\n実際のプロンプト: {prompt}"
            return f"{base_response}\n実際のプロンプト: {prompt}"  # 会話履歴の要約
        conversation_summary = "\n".join(
            [f"[{msg.role.value}]: {msg.content[:30]}..." for msg in history[-3:]]
        )

        # デフォルトの応答
        return f"これはモック応答です。会話履歴に基づいて生成されました。\n\n最近の会話:\n{conversation_summary}\n\n現在の質問: {prompt}"

    async def stream_query(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream a query to the mock LLM.

        Args:
            prompt: The prompt to send
            conversation_history: Previous messages in the conversation
            options: Additional options for the query

        Returns:
            AsyncGenerator[str, None]: An async generator that yields chunks of the response
        """
        if options is None:
            options = {}

        # Get the full response based on conversation history
        if conversation_history:
            full_response = self._generate_contextual_response(
                prompt, conversation_history
            )
        else:
            full_response = self._generate_response(prompt)

        # Split into chunks of approximately 10-20 characters
        chunks = []
        chunk_size = 15  # Average chunk size

        # Create chunks with natural word boundaries where possible
        start = 0
        while start < len(full_response):
            # Determine a variable chunk size around the average
            current_chunk_size = (
                chunk_size + (hash(full_response[start : start + 5]) % 10) - 5
            )

            # Make sure we don't go beyond the string length
            end = min(start + current_chunk_size, len(full_response))

            # Try to end at a space for more natural chunks
            if end < len(full_response) and not full_response[end].isspace():
                # Look for the nearest space backward
                space_pos = full_response.rfind(" ", start, end)
                if space_pos > start:
                    end = space_pos + 1

            chunks.append(full_response[start:end])
            start = end

        # Simulate streaming by yielding chunks with delays
        for chunk in chunks:
            # Simulate processing delay (shorter than full query to make streaming feel real)
            delay = min(0.3, self.response_delay / len(chunks))
            await asyncio.sleep(delay)

            yield chunk

    def _should_call_github_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests a GitHub operation should be performed.

        Args:
            prompt: The user prompt to analyze

        Returns:
            bool: True if a GitHub function should be called
        """
        github_keywords = [
            "create issue",
            "create an issue",
            "report bug",
            "report issue",
            "create pr",
            "create pull request",
            "submit pr",
            "make pr",
            "check permissions",
            "check repository",
            "check access",
            "post to github",
            "submit to github",
            "create in github",
        ]

        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in github_keywords)

    def _generate_mock_github_tool_calls(
        self, prompt: str, github_functions: List
    ) -> List:
        """
        Generate mock GitHub tool calls based on the prompt.

        Args:
            prompt: The user prompt
            github_functions: Available GitHub functions

        Returns:
            List of mock tool calls"""
        tool_calls = []
        prompt_lower = prompt.lower()

        # Determine which GitHub function to call based on prompt content
        if any(word in prompt_lower for word in ["issue", "bug", "report", "problem"]):
            # Create issue
            for func in github_functions:
                if hasattr(func, "name") and func.name == "create_github_issue":
                    function_call = FunctionCall(
                        name="create_github_issue",
                        arguments='{"repository": "owner/repo", "title": "Mock Issue", "description": "This is a mock issue created for testing", "labels": ["bug"]}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        elif any(word in prompt_lower for word in ["pr", "pull request", "merge"]):
            # Create pull request
            for func in github_functions:
                if hasattr(func, "name") and func.name == "create_github_pull_request":
                    function_call = FunctionCall(
                        name="create_github_pull_request",
                        arguments='{"repository": "owner/repo", "title": "Mock PR", "description": "This is a mock pull request", "head_branch": "feature-branch"}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        elif any(word in prompt_lower for word in ["permission", "access", "check"]):
            # Check permissions
            for func in github_functions:
                if (
                    hasattr(func, "name")
                    and func.name == "check_github_repository_permissions"
                ):
                    function_call = FunctionCall(
                        name="check_github_repository_permissions",
                        arguments='{"repository": "owner/repo"}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        return tool_calls

    def _should_call_utility_function(self, prompt: str) -> bool:
        """
        Determine if the prompt suggests a utility operation should be performed.

        Args:
            prompt: The user prompt to analyze

        Returns:
            bool: True if a utility function should be called
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

    def _generate_mock_utility_tool_calls(
        self, prompt: str, utility_functions: List
    ) -> List:
        """
        Generate mock utility tool calls based on the prompt.

        Args:
            prompt: The user prompt
            utility_functions: Available utility functions

        Returns:
            List of mock tool calls
        """
        tool_calls = []
        prompt_lower = prompt.lower()

        # Determine which utility function to call based on prompt content
        if any(word in prompt_lower for word in ["time", "clock", "now"]):
            # Get current time
            for func in utility_functions:
                if hasattr(func, "name") and func.name == "get_current_time":
                    function_call = FunctionCall(
                        name="get_current_time",
                        arguments='{"timezone": "UTC"}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        elif any(
            word in prompt_lower
            for word in ["count", "character", "length", "how many"]
        ):
            # Count characters
            for func in utility_functions:
                if hasattr(func, "name") and func.name == "count_text_characters":
                    # Extract text from prompt for counting
                    text_to_count = "sample text"
                    if "count" in prompt_lower:
                        # Try to extract quoted text or assume the prompt itself
                        text_to_count = prompt

                    function_call = FunctionCall(
                        name="count_text_characters",
                        arguments=f'{{"text": "{text_to_count}"}}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        elif any(
            word in prompt_lower
            for word in ["email", "validate", "valid", "check email"]
        ):
            # Validate email
            for func in utility_functions:
                if hasattr(func, "name") and func.name == "validate_email_format":
                    function_call = FunctionCall(
                        name="validate_email_format",
                        arguments='{"email": "test@example.com"}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        elif any(word in prompt_lower for word in ["random", "generate", "uuid"]):
            # Generate random data
            for func in utility_functions:
                if hasattr(func, "name") and func.name == "generate_random_data":
                    function_call = FunctionCall(
                        name="generate_random_data",
                        arguments='{"data_type": "uuid", "count": 1}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        elif any(
            word in prompt_lower
            for word in [
                "calculate",
                "math",
                "compute",
                "add",
                "subtract",
                "multiply",
                "divide",
            ]
        ):
            # Perform calculation
            for func in utility_functions:
                if hasattr(func, "name") and func.name == "calculate_simple_math":
                    # Extract numbers and operation from prompt
                    function_call = FunctionCall(
                        name="calculate_simple_math",
                        arguments='{"expression": "2 + 2"}',
                    )
                    tool_call = ToolCall(
                        id=f"call_{uuid.uuid4().hex[:8]}",
                        type="function",
                        function=function_call,
                    )
                    tool_calls.append(tool_call)
                    break

        return tool_calls

    async def query_with_tools(
        self,
        prompt: str,
        tools: List["FunctionDefinition"],
        conversation_history: Optional[List["MessageItem"]] = None,
        tool_choice: Optional["ToolChoice"] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        Send a query to the mock LLM with function calling tools.

        Args:
            prompt: The prompt to send to the LLM
            tools: List of available function definitions
            conversation_history: Previous messages in the conversation for context
            tool_choice: Strategy for tool selection
            options: Additional options for the query

        Returns:
            LLMResponse: The response from the LLM, potentially including tool calls
        """
        # Prepare options with function definitions
        query_options = options or {}
        query_options["functions"] = tools

        if tool_choice:
            query_options["tool_choice"] = tool_choice

        return await self.query(prompt, conversation_history, query_options)

    async def get_available_functions(self) -> List["FunctionDefinition"]:
        """
        Get the list of available functions for this mock LLM service.

        Returns:
            List[FunctionDefinition]: List of available function definitions
        """
        all_functions = []

        # Add GitHub function definitions for testing
        from doc_ai_helper_backend.services.llm.github_functions import (
            get_github_function_definitions,
        )

        all_functions.extend(get_github_function_definitions())

        # Add utility functions
        from doc_ai_helper_backend.services.llm.utility_functions import (
            get_utility_functions,
        )

        all_functions.extend(get_utility_functions())

        return all_functions

    async def execute_function_call(
        self,
        function_call: "FunctionCall",
        available_functions: Dict[str, Any],
    ) -> Dict[str, Any]:
        """
        Execute a mock function call.

        Args:
            function_call: The function call details from the LLM
            available_functions: Dictionary of available functions to call

        Returns:
            Dict[str, Any]: Mock result of the function execution
        """
        # Generate mock results based on function name
        if "github" in function_call.name.lower():
            if "issue" in function_call.name.lower():
                return {
                    "success": True,
                    "result": {
                        "number": 123,
                        "url": "https://github.com/owner/repo/issues/123",
                        "title": "Mock Issue",
                        "state": "open",
                    },
                }
            elif "pull_request" in function_call.name.lower():
                return {
                    "success": True,
                    "result": {
                        "number": 456,
                        "url": "https://github.com/owner/repo/pull/456",
                        "title": "Mock Pull Request",
                        "state": "open",
                    },
                }
            elif "permission" in function_call.name.lower():
                return {
                    "success": True,
                    "result": {
                        "admin": True,
                        "maintain": True,
                        "push": True,
                        "triage": True,
                        "pull": True,
                    },
                }

        # Mock results for utility functions
        elif "time" in function_call.name.lower():
            return {
                "success": True,
                "result": {
                    "current_time": "2025-06-24T10:30:00Z",
                    "timezone": "UTC",
                    "format": "ISO",
                    "timestamp": 1719225000,
                },
            }
        elif (
            "count" in function_call.name.lower()
            or "character" in function_call.name.lower()
        ):
            return {
                "success": True,
                "result": {
                    "all_characters": 42,
                    "no_spaces": 35,
                    "words": 7,
                    "lines": 1,
                    "analysis": {
                        "has_japanese": False,
                        "has_numbers": True,
                        "has_special_chars": False,
                    },
                },
            }
        elif (
            "email" in function_call.name.lower()
            or "validate" in function_call.name.lower()
        ):
            return {
                "success": True,
                "result": {
                    "is_valid": True,
                    "has_at_symbol": True,
                    "has_domain": True,
                    "local_part": "user",
                    "domain_part": "example.com",
                },
            }
        elif (
            "random" in function_call.name.lower()
            or "generate" in function_call.name.lower()
        ):
            return {
                "success": True,
                "result": {
                    "generated_data": "AbC123XyZ",
                    "data_type": "string",
                    "length": 9,
                    "actual_length": 9,
                },
            }
        elif (
            "math" in function_call.name.lower()
            or "calculate" in function_call.name.lower()
        ):
            return {
                "success": True,
                "result": {
                    "expression": "2+3*4",
                    "result": 14,
                    "result_type": "int",
                    "is_integer": True,
                },
            }

        # Default mock response
        return {
            "success": True,
            "result": f"Mock execution of {function_call.name}",
        }
