"""
レスポンス構築サービス (Response Builder Service)

LLMサービス向けの標準化されたレスポンス構築機能を提供します。
元ファイル: utils/response_builder.py

このコンポーネントは純粋な委譲パターンで使用され、mixin継承は使用しません。

主要機能:
- LLMResponseオブジェクトの標準化構築
- プロバイダー固有レスポンスの変換
- 使用量情報の統一フォーマット
"""

import logging
from typing import Dict, Any, Optional, List, Union
from doc_ai_helper_backend.models.llm import (
    LLMResponse,
    LLMUsage,
    ToolCall,
    FunctionCall,
)

logger = logging.getLogger(__name__)


class ResponseBuilder:
    """
    標準化されたLLMResponseオブジェクトを構築するユーティリティクラス

    様々なプロバイダー固有のレスポンス形式からLLMResponseオブジェクトを構築し、
    すべてのLLMサービス間で一貫性を確保します。
    """

    def __init__(self):
        """レスポンスビルダーの初期化"""
        self.logger = logger

    def build_usage_from_dict(self, usage_data: Dict[str, Any]) -> LLMUsage:
        """
        使用量データ辞書からLLMUsageオブジェクトを構築

        Args:
            usage_data: トークン使用量情報を含む辞書

        Returns:
            LLMUsage: 標準化された使用量オブジェクト
        """
        return LLMUsage(
            prompt_tokens=usage_data.get("prompt_tokens", 0),
            completion_tokens=usage_data.get("completion_tokens", 0),
            total_tokens=usage_data.get("total_tokens", 0),
        )

    def build_usage_from_openai(self, usage_obj: Any) -> LLMUsage:
        """
        OpenAIの使用量オブジェクトからLLMUsageオブジェクトを構築

        Args:
            usage_obj: OpenAIの使用量オブジェクト

        Returns:
            LLMUsage: 標準化された使用量オブジェクト
        """
        if not usage_obj:
            return LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        return LLMUsage(
            prompt_tokens=getattr(usage_obj, "prompt_tokens", 0),
            completion_tokens=getattr(usage_obj, "completion_tokens", 0),
            total_tokens=getattr(usage_obj, "total_tokens", 0),
        )

    def build_tool_calls_from_openai(
        self, tool_calls_data: List[Any]
    ) -> Optional[List[ToolCall]]:
        """
        OpenAIのツール呼び出しデータからToolCallオブジェクトのリストを構築

        Args:
            tool_calls_data: OpenAIのツール呼び出しデータのリスト

        Returns:
            Optional[List[ToolCall]]: 標準化されたツール呼び出しオブジェクトのリスト
                                     （空またはNoneの場合はNoneを返す）
        """
        if not tool_calls_data:
            return None

        tool_calls = []
        for tool_call_data in tool_calls_data:
            try:
                # OpenAIの形式からToolCallオブジェクトを構築
                tool_call = ToolCall(
                    id=getattr(tool_call_data, "id", ""),
                    type=getattr(tool_call_data, "type", "function"),
                    function=(
                        FunctionCall(
                            name=getattr(tool_call_data.function, "name", ""),
                            arguments=getattr(
                                tool_call_data.function, "arguments", "{}"
                            ),
                        )
                        if hasattr(tool_call_data, "function")
                        else None
                    ),
                )
                tool_calls.append(tool_call)
            except Exception as e:
                self.logger.warning(f"Failed to parse tool call: {e}")
                continue

        return tool_calls

    def build_response_from_openai(
        self,
        response_data: Any,
        model: Optional[str] = None,
    ) -> LLMResponse:
        """
        OpenAIレスポンスからLLMResponseオブジェクトを構築

        Args:
            response_data: OpenAIのレスポンスデータ
            model: オプション: モデル名（指定しない場合はレスポンスから取得）

        Returns:
            LLMResponse: 標準化されたLLMレスポンス
        """
        try:
            # 基本的な情報を抽出
            choices = getattr(response_data, "choices", [])
            if not choices:
                raise ValueError("No choices in OpenAI response")

            choice = choices[0]
            message = getattr(choice, "message", None)
            if not message:
                raise ValueError("No message in OpenAI choice")

            # コンテンツとツール呼び出しを取得
            content = getattr(message, "content", "") or ""
            tool_calls_data = getattr(message, "tool_calls", None)
            tool_calls = self.build_tool_calls_from_openai(tool_calls_data or [])

            # 使用量情報を構築
            usage = self.build_usage_from_openai(getattr(response_data, "usage", None))

            # LLMResponseオブジェクトを構築
            return LLMResponse(
                content=content,
                usage=usage,
                model=model or getattr(response_data, "model", "unknown"),
                provider="openai",  # OpenAIプロバイダーを指定
                tool_calls=tool_calls,
            )

        except Exception as e:
            self.logger.error(f"Failed to build response from OpenAI data: {e}")
            # 上位レイヤー（OpenAIService）でのエラーハンドリングのため例外を再発生
            raise

    def build_response_from_dict(
        self,
        response_dict: Dict[str, Any],
        prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        辞書形式のレスポンスからLLMResponseオブジェクトを構築

        Args:
            response_dict: レスポンスデータの辞書
            prompt: 元のプロンプト
            options: 元のオプション

        Returns:
            LLMResponse: 標準化されたLLMレスポンス
        """
        try:
            # 使用量情報を構築
            usage_data = response_dict.get("usage", {})
            usage = self.build_usage_from_dict(usage_data)

            # ツール呼び出しを構築
            tool_calls_data = response_dict.get("tool_calls", [])
            tool_calls = []
            for tool_call_data in tool_calls_data:
                tool_call = ToolCall(
                    id=tool_call_data.get("id", ""),
                    type=tool_call_data.get("type", "function"),
                    function=(
                        FunctionCall(
                            name=tool_call_data.get("function", {}).get("name", ""),
                            arguments=tool_call_data.get("function", {}).get(
                                "arguments", "{}"
                            ),
                        )
                        if tool_call_data.get("function")
                        else None
                    ),
                )
                tool_calls.append(tool_call)

            return LLMResponse(
                content=response_dict.get("content", ""),
                usage=usage,
                model=response_dict.get("model", "unknown"),
                provider=response_dict.get("provider", "unknown"),
                tool_calls=tool_calls,
                finish_reason=response_dict.get("finish_reason", "unknown"),
                prompt=prompt,
                options=options or {},
            )

        except Exception as e:
            self.logger.error(f"Failed to build response from dict: {e}")
            # フォールバックレスポンス
            return LLMResponse(
                content=f"Error processing response: {str(e)}",
                usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
                model="unknown",
                provider="unknown",
                tool_calls=[],
                finish_reason="error",
                prompt=prompt,
                options=options or {},
            )

    def build_error_response(
        self,
        error_message: str,
        prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
    ) -> LLMResponse:
        """
        エラーレスポンスを構築

        Args:
            error_message: エラーメッセージ
            prompt: 元のプロンプト
            options: 元のオプション

        Returns:
            LLMResponse: エラーレスポンス
        """
        return LLMResponse(
            content=f"Error: {error_message}",
            usage=LLMUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0),
            model="error",
            provider="error",
            tool_calls=[],
            finish_reason="error",
            prompt=prompt,
            options=options or {},
        )

    def build_mock_response(
        self,
        content: str,
        model: str = "mock",
        prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        usage: Optional[LLMUsage] = None,
    ) -> LLMResponse:
        """
        モックレスポンスを構築

        Args:
            content: レスポンスコンテンツ
            model: モデル名
            prompt: 元のプロンプト
            options: 元のオプション
            usage: 使用量情報

        Returns:
            LLMResponse: モックレスポンス
        """
        if usage is None:
            # デフォルトの使用量情報
            usage = LLMUsage(
                prompt_tokens=len(prompt.split()) if prompt else 0,
                completion_tokens=len(content.split()),
                total_tokens=(
                    len(prompt.split()) + len(content.split())
                    if prompt
                    else len(content.split())
                ),
            )

        return LLMResponse(
            content=content,
            usage=usage,
            model=model,
            provider="mock",
            tool_calls=[],
            finish_reason="stop",
            prompt=prompt,
            options=options or {},
        )


# 後方互換性のためのクラスエイリアス
LLMResponseBuilder = ResponseBuilder
