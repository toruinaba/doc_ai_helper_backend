"""
OpenAI LLM Service (統合版)

OpenAIのAPIを使用したLLMサービスの統合実装。
以前の複雑なデリゲーションパターンを簡素化し、
必要な機能を直接実装したクリーンなサービスクラス。
"""

import json
import logging
from typing import Dict, Any, Optional, List, AsyncGenerator, TYPE_CHECKING

import tiktoken
from openai import AsyncOpenAI

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
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    ToolCall,
    FunctionCall,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException

logger = logging.getLogger(__name__)


class OpenAIService(LLMServiceBase):
    """
    OpenAI統合サービス
    
    OpenAIのAPIを使用したLLMサービスの簡素化実装。
    オーケストレータパターンとの統合により、
    共通機能は外部に委譲し、プロバイダー固有の機能のみを実装。
    """

    def __init__(
        self,
        api_key: str,
        default_model: str = "gpt-3.5-turbo",
        base_url: Optional[str] = None,
        **kwargs,
    ):
        """
        OpenAIサービスの初期化

        Args:
            api_key: OpenAI APIキーまたはプロキシサーバーAPIキー
            default_model: 使用するデフォルトモデル
            base_url: APIのベースURL（LiteLLMプロキシURLなど）
            **kwargs: 追加の設定オプション
        """
        self.api_key = api_key
        self.default_model = default_model
        self.base_url = base_url
        self.default_options = kwargs

        # FastMCPサーバー
        self._mcp_server = None

        # OpenAIクライアントとトークンエンコーダーの初期化
        self._initialize_clients_and_encoder()

        logger.info(
            f"Initialized OpenAIService with model {default_model}"
            f"{' and custom base URL' if base_url else ''}"
        )

    def _initialize_clients_and_encoder(self):
        """OpenAIクライアントとトークンエンコーダーを初期化"""
        # OpenAIクライアント初期化
        client_params = {"api_key": self.api_key}
        if self.base_url:
            client_params["base_url"] = self.base_url

        self.async_client = AsyncOpenAI(**client_params)

        # デフォルトモデル用のトークンエンコーダー読み込み
        try:
            self._token_encoder = tiktoken.encoding_for_model(self.default_model)
        except KeyError:
            # モデル固有のエンコーダーが利用できない場合の代替
            self._token_encoder = tiktoken.get_encoding("cl100k_base")

    # === FastMCPサーバーメソッド ===

    def set_mcp_server(self, server):
        """FastMCPサーバーを設定"""
        self._mcp_server = server
        logger.info(f"MCP server set on OpenAI service: {server is not None}")

    def get_mcp_server(self):
        """FastMCPサーバーを取得"""
        return self._mcp_server

    # === プロバイダー固有実装 ===

    async def get_capabilities(self) -> ProviderCapabilities:
        """OpenAIプロバイダーの機能を取得"""
        return ProviderCapabilities(
            provider="openai",
            available_models=[
                "gpt-3.5-turbo",
                "gpt-3.5-turbo-16k",
                "gpt-4",
                "gpt-4-turbo",
                "gpt-4o",
                "gpt-4o-mini",
            ],
            max_tokens={
                "gpt-3.5-turbo": 4096,
                "gpt-3.5-turbo-16k": 16384,
                "gpt-4": 8192,
                "gpt-4-turbo": 128000,
                "gpt-4o": 128000,
                "gpt-4o-mini": 128000,
            },
            supports_streaming=True,
            supports_function_calling=True,
        )

    async def estimate_tokens(self, text: str) -> int:
        """OpenAIのtiktokenを使用してテキスト内のトークン数を推定"""
        try:
            return len(self._token_encoder.encode(text))
        except Exception as e:
            logger.warning(f"Failed to estimate tokens: {str(e)}, using character approximation")
            return len(text) // 4

    async def _prepare_provider_options(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[FunctionDefinition]] = None,
        tool_choice: Optional[ToolChoice] = None,
    ) -> Dict[str, Any]:
        """API呼び出し用のOpenAI固有オプションを準備"""
        options = options or {}

        # 標準フォーマットで会話メッセージを構築
        messages = self._build_conversation_messages(prompt, conversation_history, system_prompt)

        # OpenAIフォーマットに変換
        openai_messages = self._convert_messages_to_openai_format(messages)

        # OpenAI固有オプション準備
        provider_options = {
            "model": options.get("model", self.default_model),
            "messages": openai_messages,
            "temperature": options.get("temperature", 1.0),
            "max_completion_tokens": options.get("max_completion_tokens", options.get("max_tokens", 1000)),
        }

        # ツール/関数の処理
        if tools:
            logger.info(f"Converting {len(tools)} tools to OpenAI format")
            provider_options["tools"] = self._convert_tools_to_openai_format(tools)
            
            if tool_choice:
                provider_options["tool_choice"] = self._convert_tool_choice_to_openai_format(tool_choice)

        # 追加オプション（処理済みのもの以外）
        excluded_keys = {"model", "tools", "tool_choice", "temperature", "max_tokens", "max_completion_tokens"}
        for key, value in options.items():
            if key not in excluded_keys:
                provider_options[key] = value

        logger.info(f"Prepared OpenAI options with model: {provider_options['model']}")
        return provider_options

    async def _call_provider_api(self, options: Dict[str, Any]) -> Any:
        """準備されたオプションでOpenAI APIを呼び出し"""
        try:
            logger.info(f"OpenAI API request - tools: {bool(options.get('tools'))}")
            
            response = await self.async_client.chat.completions.create(**options)
            logger.info(f"OpenAI API call successful, model: {response.model}")
            
            # レスポンス詳細ログ
            choice = response.choices[0] if response.choices else None
            if choice and hasattr(choice.message, 'tool_calls') and choice.message.tool_calls:
                logger.info(f"OpenAI returned {len(choice.message.tool_calls)} tool calls")
                for i, tool_call in enumerate(choice.message.tool_calls):
                    logger.info(f"Tool call {i+1}: {tool_call.function.name}")
            
            return response
            
        except Exception as e:
            logger.error(f"OpenAI API call failed: {str(e)}")
            raise LLMServiceException(f"OpenAI API call failed: {str(e)}")

    async def _stream_provider_api(self, options: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """準備されたオプションでOpenAI APIからストリーミング"""
        try:
            # ストリーミング有効化
            options["stream"] = True

            stream = await self.async_client.chat.completions.create(**options)

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            logger.error(f"OpenAI streaming API call failed: {str(e)}")
            raise LLMServiceException(f"OpenAI streaming failed: {str(e)}")

    async def _convert_provider_response(self, raw_response: Any, options: Dict[str, Any]) -> LLMResponse:
        """OpenAIレスポンスを標準化されたLLMResponseに変換"""
        try:
            choice = raw_response.choices[0] if raw_response.choices else None
            if not choice:
                raise LLMServiceException("No choices in OpenAI response")

            message = choice.message
            content = message.content or ""

            # 使用量統計
            usage = None
            if raw_response.usage:
                usage = LLMUsage(
                    prompt_tokens=raw_response.usage.prompt_tokens,
                    completion_tokens=raw_response.usage.completion_tokens,
                    total_tokens=raw_response.usage.total_tokens,
                )

            # ツール呼び出し処理
            tool_calls = []
            if hasattr(message, 'tool_calls') and message.tool_calls:
                for tool_call in message.tool_calls:
                    tool_calls.append(
                        ToolCall(
                            id=tool_call.id,
                            function=FunctionCall(
                                name=tool_call.function.name,
                                arguments=tool_call.function.arguments,
                            ),
                        )
                    )

            return LLMResponse(
                content=content,
                model=raw_response.model,
                provider="openai",
                usage=usage,
                tool_calls=tool_calls,
                finish_reason=choice.finish_reason,
            )

        except Exception as e:
            logger.error(f"Failed to convert OpenAI response: {str(e)}")
            raise LLMServiceException(f"Response conversion failed: {str(e)}")

    # === ツール実行 ===

    async def execute_function_call(
        self,
        function_call: FunctionCall,
        available_functions: Dict[str, Any],
        repository_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """FastMCPサーバーを使用して関数呼び出しを実行"""
        # 利用可能な場合はFastMCPサーバーを最初に試行
        if self._mcp_server:
            try:
                tool_name = function_call.name
                arguments = function_call.arguments
                
                # 引数がJSON文字列形式の場合は解析
                if isinstance(arguments, str):
                    arguments = json.loads(arguments)
                elif not isinstance(arguments, dict):
                    arguments = {}
                
                # 提供されている場合はリポジトリコンテキストを引数に追加
                if repository_context:
                    arguments['repository_context'] = repository_context
                elif tool_name in ['create_git_issue', 'create_git_pull_request', 'check_git_repository_permissions']:
                    # Gitツールはrepository_contextが必要 - 利用できない場合は失敗
                    error_msg = f"Git tool '{tool_name}' requires repository context but none is available."
                    logger.error(error_msg)
                    return {"success": False, "result": None, "error": error_msg}
                
                logger.info(f"Executing function via FastMCP: {tool_name}")
                result = await self._mcp_server.call_tool(tool_name, **arguments)
                return {"success": True, "result": result, "error": None}
                
            except Exception as e:
                logger.warning(f"FastMCP execution failed: {e}")
                return {"success": False, "result": None, "error": str(e)}
        
        # FastMCPが利用できない場合はエラー
        return {
            "success": False, 
            "result": None, 
            "error": "Function execution requires FastMCP server"
        }

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """FastMCPツールを含む利用可能な関数を取得"""
        functions = []
        
        # FastMCP関数を追加（サーバーが利用可能な場合）
        if self._mcp_server:
            try:
                mcp_tools = await self._mcp_server.app.get_tools()
                logger.debug(f"FastMCP tools retrieved: {len(mcp_tools) if mcp_tools else 0}")
                functions.extend(self._convert_mcp_tools_to_function_definitions(mcp_tools))
            except Exception as e:
                logger.warning(f"Failed to get FastMCP tools: {e}")
        else:
            logger.warning("No MCP server available for function calling")
        
        logger.info(f"Total available functions: {len(functions)}")
        return functions
    
    def _convert_mcp_tools_to_function_definitions(self, mcp_tools: Dict) -> List[FunctionDefinition]:
        """FastMCPツールを関数定義に変換"""
        function_definitions = []
        for tool_name, tool in mcp_tools.items():
            try:
                function_def = FunctionDefinition(
                    name=tool_name,
                    description=tool.description or f"FastMCP tool: {tool_name}",
                    parameters=tool.parameters or {"type": "object", "properties": {}, "required": []}
                )
                function_definitions.append(function_def)
            except Exception as e:
                logger.warning(f"Failed to convert FastMCP tool {tool_name}: {e}")
        
        return function_definitions

    # === フォーマット変換ヘルパー ===

    def _build_conversation_messages(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        system_prompt: Optional[str] = None,
    ) -> List[MessageItem]:
        """標準フォーマットで会話メッセージを構築"""
        messages = []

        # システムプロンプト追加
        if system_prompt:
            messages.append(MessageItem(role=MessageRole.SYSTEM, content=system_prompt))

        # 会話履歴追加
        if conversation_history:
            messages.extend(conversation_history)

        # 現在のプロンプト追加（空でない場合のみ）
        if prompt.strip():
            messages.append(MessageItem(role=MessageRole.USER, content=prompt))

        return messages

    def _convert_messages_to_openai_format(self, messages: List[MessageItem]) -> List[Dict[str, Any]]:
        """メッセージをOpenAIフォーマットに変換"""
        openai_messages = []
        for msg in messages:
            openai_msg = {"role": msg.role.value, "content": msg.content}

            # アシスタントメッセージのツール呼び出し処理
            if hasattr(msg, "tool_calls") and msg.tool_calls:
                openai_msg["tool_calls"] = []
                for tool_call in msg.tool_calls:
                    openai_msg["tool_calls"].append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.function.name,
                            "arguments": tool_call.function.arguments,
                        },
                    })

            # ツールメッセージのツール呼び出しID処理
            if hasattr(msg, "tool_call_id") and msg.tool_call_id:
                openai_msg["tool_call_id"] = msg.tool_call_id

            openai_messages.append(openai_msg)

        return openai_messages

    def _convert_tools_to_openai_format(self, tools: List[FunctionDefinition]) -> List[Dict[str, Any]]:
        """関数定義をOpenAIツールフォーマットに変換"""
        openai_tools = []
        for func_def in tools:
            if hasattr(func_def, "name"):
                tool = {
                    "type": "function",
                    "function": {
                        "name": func_def.name,
                        "description": func_def.description,
                        "parameters": func_def.parameters,
                    },
                }
                openai_tools.append(tool)
        return openai_tools

    def _convert_tool_choice_to_openai_format(self, tool_choice: ToolChoice) -> Any:
        """ツール選択をOpenAIフォーマットに変換"""
        if isinstance(tool_choice, str):
            return tool_choice
        elif hasattr(tool_choice, "value"):
            return tool_choice.value
        elif hasattr(tool_choice, "type"):
            if tool_choice.type in ["auto", "none", "required"]:
                return tool_choice.type
            elif tool_choice.type == "function" and tool_choice.function:
                return {
                    "type": "function",
                    "function": tool_choice.function
                }
            else:
                return tool_choice.type
        else:
            return tool_choice