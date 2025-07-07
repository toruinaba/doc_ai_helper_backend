"""
メッセージング・会話履歴管理サービス (Messaging & Conversation History Service)

LLMサービスのメッセージング機能と会話履歴管理を提供します。
元ファイル: utils/messaging.py

このコンポーネントは純粋な委譲パターンで使用され、mixin継承は使用しません。

主要機能:
- 会話履歴の最適化とトークン管理
- システムプロンプトの構築
- メッセージの処理とフォーマット
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List, Tuple, Union
from pathlib import Path
from datetime import datetime

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole
from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    RepositoryContextSummary,
)
from ..processing.tokens import (
    estimate_message_tokens,
    estimate_conversation_tokens,
    DEFAULT_MAX_TOKENS,
    TokenCounter,
)

logger = logging.getLogger(__name__)


class MessageBuilder:
    """
    メッセージ構築とフォーマットのユーティリティクラス
    """

    @staticmethod
    def create_system_message(content: str) -> MessageItem:
        """システムメッセージを作成"""
        return MessageItem(
            role=MessageRole.SYSTEM, content=content, timestamp=datetime.now()
        )

    @staticmethod
    def create_user_message(content: str) -> MessageItem:
        """ユーザーメッセージを作成"""
        return MessageItem(
            role=MessageRole.USER, content=content, timestamp=datetime.now()
        )

    @staticmethod
    def create_assistant_message(content: str) -> MessageItem:
        """アシスタントメッセージを作成"""
        return MessageItem(
            role=MessageRole.ASSISTANT, content=content, timestamp=datetime.now()
        )

    @staticmethod
    def format_messages_for_api(messages: List[MessageItem]) -> List[Dict[str, str]]:
        """メッセージをAPI用のフォーマットに変換"""
        return [{"role": msg.role.value, "content": msg.content} for msg in messages]


def optimize_conversation_history(
    history: List[MessageItem],
    max_tokens: int = DEFAULT_MAX_TOKENS,
    preserve_recent: int = 2,
    encoding_name: str = "cl100k_base",
) -> Tuple[List[MessageItem], Dict[str, Any]]:
    """
    トークン制限内に収まるよう会話履歴を最適化する。

    会話履歴が指定されたトークン数を超える場合、
    最も古いメッセージから削除していく。
    ただし、指定された数の最新メッセージは常に保持する。

    Args:
        history: 最適化する会話履歴
        max_tokens: 最大トークン数
        preserve_recent: 常に保持する最新メッセージ数
        encoding_name: 使用するエンコーディング名

    Returns:
        Tuple[List[MessageItem], Dict[str, Any]]: 最適化された会話履歴と最適化情報
    """
    if not history:
        return [], {"was_optimized": False, "reason": "Empty history"}

    # 元の履歴のトークン数を計算
    original_tokens = estimate_conversation_tokens(history, encoding_name)

    # 最適化が不要な場合
    if original_tokens <= max_tokens:
        optimization_info = {
            "was_optimized": False,
            "reason": "Within token limit",
            "original_message_count": len(history),
            "optimized_message_count": len(history),
            "original_tokens": original_tokens,
            "optimized_tokens": original_tokens,
        }
        return history.copy(), optimization_info

    # 最新のN個を保存するため、履歴を逆順にする
    preserved_messages = (
        history[-preserve_recent:] if len(history) > preserve_recent else history.copy()
    )
    remaining_messages = (
        history[:-preserve_recent] if len(history) > preserve_recent else []
    )

    # 保存するメッセージのトークン数を計算
    preserved_tokens = estimate_conversation_tokens(preserved_messages, encoding_name)

    # 残りのトークン数
    remaining_token_budget = max_tokens - preserved_tokens

    # トークン数に余裕がある場合は、古いメッセージも可能な限り含める
    optimized_history = []

    # 新しい順に追加していく
    for message in reversed(remaining_messages):
        message_tokens = estimate_message_tokens(message, encoding_name)
        if remaining_token_budget >= message_tokens:
            optimized_history.append(message)
            remaining_token_budget -= message_tokens
        else:
            break

    # 時系列順に戻す
    optimized_history.reverse()

    # 保存するメッセージを追加
    optimized_history.extend(preserved_messages)

    # 最適化情報
    optimized_tokens = estimate_conversation_tokens(optimized_history, encoding_name)
    optimization_info = {
        "was_optimized": True,
        "reason": "Token limit exceeded",
        "original_message_count": len(history),
        "optimized_message_count": len(optimized_history),
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "messages_removed": len(history) - len(optimized_history),
        "messages_preserved": preserve_recent,
    }

    return optimized_history, optimization_info


async def optimize_conversation_with_summary(
    history: List[MessageItem],
    llm_service,  # LLMServiceBaseのインスタンス
    max_messages_to_keep: int = 10,
    summary_prompt_template: Optional[str] = None,
) -> Tuple[List[MessageItem], Dict[str, Any]]:
    """
    LLMを使用して会話履歴を要約し、最適化する。

    古い会話を要約して1つのメッセージにまとめ、
    最新のメッセージと組み合わせて効率的なコンテキストを作成する。

    Args:
        history: 最適化する会話履歴
        llm_service: 要約に使用するLLMサービス
        max_messages_to_keep: 要約せずに保持する最新メッセージ数
        summary_prompt_template: 要約用のプロンプトテンプレート

    Returns:
        Tuple[List[MessageItem], Dict[str, Any]]: 最適化された会話履歴と最適化情報
    """
    if not history:
        return [], {"optimization_applied": False, "reason": "Empty history"}

    # システムメッセージを分離
    system_messages = [msg for msg in history if msg.role == MessageRole.SYSTEM]
    conversation_messages = [msg for msg in history if msg.role != MessageRole.SYSTEM]

    if len(conversation_messages) <= max_messages_to_keep:
        return history, {
            "optimization_applied": False,
            "reason": "Below threshold after system separation",
        }

    # 最新のメッセージを保持
    recent_messages = conversation_messages[-max_messages_to_keep:]
    messages_to_summarize = conversation_messages[:-max_messages_to_keep]

    if not messages_to_summarize:
        return history, {
            "optimization_applied": False,
            "reason": "No messages to summarize",
        }

    # 要約用のプロンプトを準備
    if summary_prompt_template is None:
        summary_prompt_template = """以下の会話履歴を簡潔に要約してください。重要な文脈と情報を保持しながら、簡潔にまとめてください。

会話履歴:
{conversation_text}

要約:"""

    # 会話履歴をテキストに変換
    conversation_text = "\n".join(
        [f"{msg.role.value}: {msg.content}" for msg in messages_to_summarize]
    )

    summary_prompt = summary_prompt_template.format(conversation_text=conversation_text)

    try:
        # LLMサービスを使用して要約を生成
        summary_response = await llm_service.query(
            summary_prompt,
            conversation_history=None,  # 要約時は履歴を使用しない
            options={"temperature": 0.3, "max_tokens": 500},  # 要約は一貫性を重視
        )

        # 要約を含む最適化済み履歴を作成
        summary_message = MessageItem(
            role=MessageRole.ASSISTANT,
            content=f"[会話要約] {summary_response.content}",
            timestamp=datetime.now(),
        )

        # システムメッセージ + 要約 + 最新メッセージ
        optimized_history = system_messages + [summary_message] + recent_messages

        optimization_info = {
            "optimization_applied": True,
            "original_message_count": len(history),
            "optimized_message_count": len(optimized_history),
            "summarized_message_count": len(messages_to_summarize),
            "kept_recent_message_count": len(recent_messages),
            "summary_tokens": estimate_message_tokens(summary_message),
        }

        return optimized_history, optimization_info

    except Exception as e:
        logger.error(f"Failed to summarize conversation history: {str(e)}")
        # 要約に失敗した場合は、古いメッセージを削除して最新メッセージのみ保持
        fallback_history = system_messages + recent_messages
        optimization_info = {
            "optimization_applied": True,
            "optimization_method": "fallback_truncation",
            "original_message_count": len(history),
            "optimized_message_count": len(fallback_history),
            "error": str(e),
        }

        return fallback_history, optimization_info


def format_conversation_for_provider(
    conversation_history: List[MessageItem], provider: str
) -> List[Dict[str, Any]]:
    """
    会話履歴を特定のプロバイダ形式に変換する。

    Args:
        conversation_history: 変換する会話履歴
        provider: LLMプロバイダ名 ('openai', 'anthropic', 'ollama' など)

    Returns:
        List[Dict[str, Any]]: プロバイダ形式の会話履歴
    """
    if not conversation_history:
        return []

    if provider.lower() == "openai":
        # OpenAI形式: {"role": "user|assistant|system", "content": "..."}
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation_history
        ]

    elif provider.lower() == "anthropic":
        # Anthropic形式: Claude用の形式
        formatted = []
        for msg in conversation_history:
            if msg.role.value == "user":
                formatted.append({"role": "human", "content": msg.content})
            elif msg.role.value == "assistant":
                formatted.append({"role": "assistant", "content": msg.content})
            elif msg.role.value == "system":
                # システムメッセージは最初に一つだけ
                if not formatted or formatted[0].get("role") != "system":
                    formatted.insert(0, {"role": "system", "content": msg.content})
        return formatted

    elif provider.lower() == "ollama":
        # Ollama形式: {"role": "user|assistant|system", "content": "..."}
        # 基本的にOpenAIと同じ
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation_history
        ]

    else:
        # デフォルトはOpenAI形式に準ずる
        logger.warning(f"Unknown provider '{provider}', using OpenAI format as default")
        return [
            {"role": msg.role.value, "content": msg.content}
            for msg in conversation_history
        ]


async def summarize_conversation_history(
    history: List[MessageItem],
    llm_service: Any,  # LLMServiceBaseの循環インポートを避けるためAnyを使用
    max_messages_to_keep: int = 6,
    summary_prompt_template: Optional[str] = None,
) -> Tuple[List[MessageItem], Dict[str, Any]]:
    """
    長い会話履歴を要約して、最新のメッセージと要約を組み合わせた最適化済み履歴を返す。

    Args:
        history: 要約する会話履歴
        llm_service: 要約に使用するLLMサービス
        max_messages_to_keep: 要約対象外として保持する最新メッセージ数
        summary_prompt_template: 要約に使用するプロンプトテンプレート

    Returns:
        Tuple[List[MessageItem], Dict[str, Any]]:
            最適化された会話履歴と最適化情報
    """
    if len(history) <= max_messages_to_keep:
        return history, {"optimization_applied": False, "reason": "Below threshold"}

    # システムメッセージを分離
    system_messages = [msg for msg in history if msg.role == MessageRole.SYSTEM]
    conversation_messages = [msg for msg in history if msg.role != MessageRole.SYSTEM]

    if len(conversation_messages) <= max_messages_to_keep:
        return history, {
            "optimization_applied": False,
            "reason": "Below threshold after system separation",
        }

    # 最新のメッセージを保持
    recent_messages = conversation_messages[-max_messages_to_keep:]
    messages_to_summarize = conversation_messages[:-max_messages_to_keep]

    if not messages_to_summarize:
        return history, {
            "optimization_applied": False,
            "reason": "No messages to summarize",
        }

    # 要約用のプロンプトを準備
    if summary_prompt_template is None:
        summary_prompt_template = """以下の会話履歴を簡潔に要約してください。重要な文脈と情報を保持しながら、簡潔にまとめてください。

会話履歴:
{conversation_text}

要約:"""

    # 会話履歴をテキストに変換
    conversation_text = "\n".join(
        [f"{msg.role.value}: {msg.content}" for msg in messages_to_summarize]
    )

    summary_prompt = summary_prompt_template.format(conversation_text=conversation_text)

    try:
        # LLMサービスを使用して要約を生成
        summary_response = await llm_service.query(
            summary_prompt,
            conversation_history=None,  # 要約時は履歴を使用しない
            options={"temperature": 0.3, "max_tokens": 500},  # 要約は一貫性を重視
        )

        # 要約を含む最適化済み履歴を作成
        summary_message = MessageItem(
            role=MessageRole.ASSISTANT,
            content=f"[会話要約] {summary_response.content}",
            timestamp=datetime.now(),
        )

        # システムメッセージ + 要約 + 最新メッセージ
        optimized_history = system_messages + [summary_message] + recent_messages

        optimization_info = {
            "optimization_applied": True,
            "original_message_count": len(history),
            "optimized_message_count": len(optimized_history),
            "summarized_message_count": len(messages_to_summarize),
            "kept_recent_message_count": len(recent_messages),
            "summary_tokens": estimate_message_tokens(summary_message),
        }

        return optimized_history, optimization_info

    except Exception as e:
        logger.error(f"Failed to summarize conversation history: {str(e)}")
        # 要約に失敗した場合は、古いメッセージを削除して最新メッセージのみ保持
        fallback_history = system_messages + recent_messages
        optimization_info = {
            "optimization_applied": True,
            "optimization_method": "fallback_truncation",
            "original_message_count": len(history),
            "optimized_message_count": len(fallback_history),
            "error": str(e),
        }

        return fallback_history, optimization_info


class SystemPromptCache:
    """システムプロンプトのキャッシュ管理"""

    def __init__(self, cache_dir: Optional[str] = None, ttl_hours: int = 24):
        """
        キャッシュの初期化

        Args:
            cache_dir: キャッシュディレクトリのパス
            ttl_hours: キャッシュの有効期限（時間）
        """
        self.cache_dir = Path(cache_dir) if cache_dir else Path.cwd() / ".cache"
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl_seconds = ttl_hours * 3600

    def _get_cache_key(
        self,
        repository_context: RepositoryContext,
        document_metadata: Optional[DocumentMetadata] = None,
    ) -> str:
        """キャッシュキーを生成"""
        context_data = {
            "owner": repository_context.owner,
            "repo": repository_context.repo,
            "current_path": repository_context.current_path,
            "ref": repository_context.ref,
        }

        if document_metadata:
            context_data["document"] = {
                "filename": document_metadata.filename,
                "is_documentation": document_metadata.is_documentation,
                "is_code_file": document_metadata.is_code_file,
            }

        return hashlib.md5(
            json.dumps(context_data, sort_keys=True).encode()
        ).hexdigest()

    def get(
        self,
        repository_context: RepositoryContext,
        document_metadata: Optional[DocumentMetadata] = None,
    ) -> Optional[str]:
        """キャッシュからシステムプロンプトを取得"""
        cache_key = self._get_cache_key(repository_context, document_metadata)
        cache_file = self.cache_dir / f"{cache_key}.json"

        if not cache_file.exists():
            return None

        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                cache_data = json.load(f)

            # TTLチェック
            if time.time() - cache_data.get("timestamp", 0) > self.ttl_seconds:
                cache_file.unlink()  # 期限切れファイルを削除
                return None

            return cache_data.get("system_prompt")

        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_file}: {e}")
            return None

    def set(
        self,
        repository_context: RepositoryContext,
        system_prompt: str,
        document_metadata: Optional[DocumentMetadata] = None,
    ) -> None:
        """システムプロンプトをキャッシュに保存"""
        cache_key = self._get_cache_key(repository_context, document_metadata)
        cache_file = self.cache_dir / f"{cache_key}.json"

        cache_data = {
            "system_prompt": system_prompt,
            "timestamp": time.time(),
            "repository_context": repository_context.model_dump(),
        }

        if document_metadata:
            cache_data["document_metadata"] = document_metadata.model_dump()

        try:
            with open(cache_file, "w", encoding="utf-8") as f:
                json.dump(cache_data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")

    def clear(self) -> None:
        """キャッシュをクリア"""
        try:
            for cache_file in self.cache_dir.glob("*.json"):
                cache_file.unlink()
        except Exception as e:
            logger.warning(f"Failed to clear cache: {e}")

    def get_stats(self) -> Dict[str, Any]:
        """キャッシュの統計情報を取得"""
        total_files = 0
        valid_files = 0
        expired_files = 0

        try:
            for cache_file in self.cache_dir.glob("*.json"):
                total_files += 1
                try:
                    with open(cache_file, "r", encoding="utf-8") as f:
                        cache_data = json.load(f)

                    # TTLチェック
                    if time.time() - cache_data.get("timestamp", 0) > self.ttl_seconds:
                        expired_files += 1
                    else:
                        valid_files += 1

                except Exception:
                    expired_files += 1

        except Exception as e:
            logger.warning(f"Failed to get cache stats: {e}")

        return {
            "total_files": total_files,
            "valid_files": valid_files,
            "expired_files": expired_files,
            "ttl_seconds": self.ttl_seconds,
        }


class SystemPromptBuilder:
    """
    ドキュメント対応システムプロンプト構築クラス

    リポジトリとドキュメント情報を含むコンテキスト対応システムプロンプトを構築します。
    """

    def __init__(self, enable_cache: bool = True, cache_dir: Optional[str] = None):
        """
        システムプロンプト構築クラスの初期化

        Args:
            enable_cache: キャッシュを有効にするかどうか
            cache_dir: キャッシュディレクトリのパス
        """
        self.enable_cache = enable_cache
        self.cache = SystemPromptCache(cache_dir) if enable_cache else None

    def build_system_prompt(
        self,
        repository_context: RepositoryContext,
        document_metadata: Optional[DocumentMetadata] = None,
        custom_instructions: Optional[str] = None,
        template_id: Optional[str] = None,
    ) -> str:
        """
        コンテキスト対応システムプロンプトを構築

        Args:
            repository_context: リポジトリコンテキスト
            document_metadata: ドキュメントメタデータ
            custom_instructions: カスタム指示
            template_id: 使用するテンプレートID

        Returns:
            str: 構築されたシステムプロンプト
        """
        # キャッシュから取得を試行
        if self.cache:
            cached_prompt = self.cache.get(repository_context, document_metadata)
            if (
                cached_prompt and not custom_instructions
            ):  # カスタム指示がある場合はキャッシュしない
                return cached_prompt

        # システムプロンプトを構築
        prompt_parts = []

        # 基本的なコンテキスト情報
        prompt_parts.append(
            f"リポジトリ: {repository_context.owner}/{repository_context.repo}"
        )

        if repository_context.current_path:
            prompt_parts.append(f"現在のファイル: {repository_context.current_path}")

        # ドキュメント固有の情報
        if document_metadata:
            if document_metadata.is_documentation:
                prompt_parts.append("このファイルはドキュメントファイルです。")
            elif document_metadata.is_code_file:
                prompt_parts.append("このファイルはコードファイルです。")

        # カスタム指示を追加
        if custom_instructions:
            prompt_parts.append(f"追加指示: {custom_instructions}")

        # 基本的なプロンプトを組み立て
        system_prompt = "\n".join(prompt_parts)

        # キャッシュに保存（カスタム指示がない場合のみ）
        if self.cache and not custom_instructions:
            self.cache.set(repository_context, system_prompt, document_metadata)

        return system_prompt
