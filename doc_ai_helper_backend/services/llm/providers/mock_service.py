"""
Mock LLM Service (統合版)

開発とテスト用のモックLLMサービスの統合実装。
以前の複雑なデリゲーションパターンを簡素化し、
必要な機能を直接実装したクリーンなモックサービス。
"""

import asyncio
import uuid
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
    ProviderCapabilities,
    MessageItem,
    MessageRole,
    FunctionDefinition,
    ToolChoice,
    ToolCall,
    FunctionCall,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException


class MockLLMService(LLMServiceBase):
    """
    モックLLMサービス
    
    開発とテスト用のモックLLMサービスの簡素化実装。
    オーケストレータパターンとの統合により、
    シンプルで予測可能なレスポンスを提供。
    """

    def __init__(
        self, 
        response_delay: float = 0.1, 
        default_model: str = "mock-model", 
        **kwargs
    ):
        """
        モックLLMサービスの初期化

        Args:
            response_delay: レスポンス前の遅延（秒）
            default_model: 使用するデフォルトモデル
            **kwargs: 追加の設定オプション
        """
        self.response_delay = response_delay
        self.default_model = default_model
        self.default_options = kwargs

        # レスポンスパターン
        self.response_patterns = {
            "hello": "Hello! This is a mock response from the Mock LLM service.",
            "test": "This is a test response from the Mock LLM service.",
            "python": "Python is a high-level programming language known for its simplicity and readability.",
            "what is": "That's a great question. As a mock service, I provide standardized responses for testing.",
            "how to": "Here are the general steps for that task. This is a mock response for development purposes.",
            "エラー": "エラーをシミュレートしています",
            "error": "Simulating an error condition",
        }

        # 利用可能モデル
        self.available_models = [
            "mock-model",
            "mock-gpt-3.5",
            "mock-gpt-4",
            "mock-claude",
        ]

    # === プロバイダー固有実装 ===

    async def get_capabilities(self) -> ProviderCapabilities:
        """モックプロバイダーの機能を取得"""
        return ProviderCapabilities(
            provider="mock",
            available_models=self.available_models,
            max_tokens={model: 4096 for model in self.available_models},
            supports_streaming=True,
            supports_function_calling=True,
        )

    async def estimate_tokens(self, text: str) -> int:
        """テキスト内のトークン数を推定（簡単な文字ベース）"""
        return len(text) // 4  # 簡単な推定

    async def _prepare_provider_options(
        self,
        prompt: str,
        conversation_history: Optional[List[MessageItem]] = None,
        options: Optional[Dict[str, Any]] = None,
        system_prompt: Optional[str] = None,
        tools: Optional[List[FunctionDefinition]] = None,
        tool_choice: Optional[ToolChoice] = None,
    ) -> Dict[str, Any]:
        """モックプロバイダーオプションを準備"""
        prepared_options = options.copy() if options else {}
        prepared_options.update({
            "model": prepared_options.get("model", self.default_model),
            "prompt": prompt,
            "system_prompt": system_prompt,
            "conversation_history": conversation_history,
            "tools": tools,
            "tool_choice": tool_choice,
        })
        return prepared_options

    async def _call_provider_api(self, options: Dict[str, Any]) -> Dict[str, Any]:
        """モックプロバイダーAPI呼び出し"""
        # 遅延をシミュレート
        await asyncio.sleep(self.response_delay)

        prompt = options.get("prompt", "")
        system_prompt = options.get("system_prompt")
        tools = options.get("tools", [])

        # エラーシミュレーション
        if "raise error" in prompt.lower() or "エラー" in prompt:
            raise LLMServiceException("Simulated error from mock service")

        # レスポンス生成
        content = self._generate_mock_response(prompt, system_prompt)
        
        # ツール呼び出しシミュレーション
        tool_calls = []
        if tools and self._should_call_tools(prompt):
            tool_calls = self._generate_mock_tool_calls(tools)

        return {
            "content": content,
            "model": options.get("model", self.default_model),
            "usage": {
                "prompt_tokens": len(prompt) // 4,
                "completion_tokens": len(content) // 4,
                "total_tokens": len(prompt) // 4 + len(content) // 4,
            },
            "tool_calls": tool_calls,
            "finish_reason": "stop",
        }

    async def _stream_provider_api(self, options: Dict[str, Any]) -> AsyncGenerator[str, None]:
        """モックストリーミングプロバイダーAPI呼び出し"""
        # 完全なレスポンスを取得
        response = await self._call_provider_api(options)
        content = response["content"]

        # コンテンツをチャンクに分割してストリーミング
        chunk_size = 10
        for i in range(0, len(content), chunk_size):
            chunk = content[i:i + chunk_size]
            await asyncio.sleep(self.response_delay / 10)  # 小さな遅延
            yield chunk

    async def _convert_provider_response(self, raw_response: Dict[str, Any], options: Dict[str, Any]) -> LLMResponse:
        """モックプロバイダーレスポンスを標準化されたLLMResponseに変換"""
        usage = LLMUsage(
            prompt_tokens=raw_response["usage"]["prompt_tokens"],
            completion_tokens=raw_response["usage"]["completion_tokens"],
            total_tokens=raw_response["usage"]["total_tokens"],
        )

        # ツール呼び出し変換
        tool_calls = []
        for mock_tool_call in raw_response.get("tool_calls", []):
            tool_calls.append(
                ToolCall(
                    id=mock_tool_call["id"],
                    function=FunctionCall(
                        name=mock_tool_call["function"]["name"],
                        arguments=mock_tool_call["function"]["arguments"],
                    ),
                )
            )

        return LLMResponse(
            content=raw_response["content"],
            model=raw_response["model"],
            provider="mock",
            usage=usage,
            tool_calls=tool_calls,
            finish_reason=raw_response.get("finish_reason", "stop"),
        )

    # === ツール実行 ===

    async def execute_function_call(
        self,
        function_call: FunctionCall,
        available_functions: Dict[str, Any],
        repository_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """モック関数呼び出しを実行"""
        # 遅延をシミュレート
        await asyncio.sleep(self.response_delay)

        function_name = function_call.name
        
        # 関数固有のモックレスポンス
        if function_name == "summarize_document_with_llm":
            return {
                "success": True,
                "result": '{"summary": "This is a mock document summary", "key_points": ["Point 1", "Point 2"]}',
                "error": None,
            }
        elif function_name == "create_improvement_recommendations_with_llm":
            return {
                "success": True,
                "result": '{"recommendations": ["Improve documentation", "Add error handling"]}',
                "error": None,
            }
        elif function_name == "create_git_issue":
            if not repository_context:
                return {
                    "success": False,
                    "result": None,
                    "error": "Repository context required for git operations",
                }
            return {
                "success": True,
                "result": '{"issue_number": 42, "url": "https://github.com/example/repo/issues/42"}',
                "error": None,
            }
        else:
            # 汎用モックレスポンス
            return {
                "success": True,
                "result": f"Mock execution result for {function_name}",
                "error": None,
            }

    async def get_available_functions(self) -> List[FunctionDefinition]:
        """利用可能なモック関数を取得"""
        return [
            FunctionDefinition(
                name="summarize_document_with_llm",
                description="文書を要約するモック関数",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_path": {"type": "string", "description": "文書のパス"}
                    },
                    "required": ["document_path"]
                }
            ),
            FunctionDefinition(
                name="create_improvement_recommendations_with_llm",
                description="改善提案を作成するモック関数",
                parameters={
                    "type": "object",
                    "properties": {
                        "document_path": {"type": "string", "description": "文書のパス"}
                    },
                    "required": ["document_path"]
                }
            ),
            FunctionDefinition(
                name="create_git_issue",
                description="Gitイシューを作成するモック関数",
                parameters={
                    "type": "object",
                    "properties": {
                        "title": {"type": "string", "description": "イシューのタイトル"},
                        "body": {"type": "string", "description": "イシューの本文"}
                    },
                    "required": ["title", "body"]
                }
            ),
        ]

    # === ヘルパーメソッド ===

    def _generate_mock_response(self, prompt: str, system_prompt: Optional[str] = None) -> str:
        """モックレスポンスを生成"""
        prompt_lower = prompt.lower()

        # パターンマッチング
        for pattern, response in self.response_patterns.items():
            if pattern in prompt_lower:
                return response

        # システムプロンプトに基づくレスポンス
        if system_prompt:
            if "repository" in system_prompt.lower() or "github" in system_prompt.lower():
                return f"リポジトリコンテキストを理解しました。'{prompt}' に関するモックレスポンスです。"
            elif "document" in system_prompt.lower():
                return f"文書コンテキストを理解しました。'{prompt}' に関するモックレスポンスです。"

        # デフォルトレスポンス
        if len(prompt) < 20:
            return f"短いプロンプト '{prompt}' に対するモックレスポンスです。"
        else:
            return f"{len(prompt)}文字のプロンプトを受信しました。これはモックLLMサービスからのテスト用レスポンスです。"

    def _should_call_tools(self, prompt: str) -> bool:
        """プロンプトがツール呼び出しを示すかどうかを判定"""
        tool_keywords = [
            "要約", "summarize", "分析", "analyze", 
            "改善", "improve", "作成", "create",
            "ツールを呼び出して", "call tool"
        ]
        prompt_lower = prompt.lower()
        return any(keyword in prompt_lower for keyword in tool_keywords)

    def _generate_mock_tool_calls(self, tools: List[FunctionDefinition]) -> List[Dict[str, Any]]:
        """モックツール呼び出しを生成"""
        if not tools:
            return []
        
        # 最初のツールを呼び出すモック
        tool = tools[0]
        return [{
            "id": f"call_{uuid.uuid4().hex[:8]}",
            "function": {
                "name": tool.name,
                "arguments": '{"mock": "arguments"}',
            },
        }]

    # === 公開メソッド ===

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
        """モックLLMクエリを実行"""
        # 遅延をシミュレート
        await asyncio.sleep(self.response_delay)
        
        # オプションを準備
        prepared_options = await self._prepare_provider_options(
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            system_prompt=None,  # 簡素化
        )
        
        # プロバイダーAPIを呼び出し
        raw_response = await self._call_provider_api(prepared_options)
        
        # レスポンスを変換
        return await self._convert_provider_response(raw_response, prepared_options)

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
        """モックLLMストリーミングクエリを実行"""
        # オプションを準備
        prepared_options = await self._prepare_provider_options(
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            system_prompt=None,  # 簡素化
        )
        
        # ストリーミングAPIを呼び出し
        async for chunk in self._stream_provider_api(prepared_options):
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
        """ツールありモックLLMクエリを実行"""
        # 遅延をシミュレート
        await asyncio.sleep(self.response_delay)
        
        # オプションを準備
        prepared_options = await self._prepare_provider_options(
            prompt=prompt,
            conversation_history=conversation_history,
            options=options,
            system_prompt=None,  # 簡素化
            tools=tools,
            tool_choice=tool_choice,
        )
        
        # プロバイダーAPIを呼び出し
        raw_response = await self._call_provider_api(prepared_options)
        
        # レスポンスを変換
        return await self._convert_provider_response(raw_response, prepared_options)

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
        """ツールありフォローアップモックLLMクエリを実行"""
        # 基本的にはquery_with_toolsと同じ（簡素化）
        return await self.query_with_tools(
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