"""
Messaging utilities for LLM services.

This module provides functionality for conversation history management and system prompt building.
Combines system prompt building with conversation utilities for better organization.
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
from .tokens import (
    estimate_message_tokens,
    estimate_conversation_tokens,
    DEFAULT_MAX_TOKENS,
)

logger = logging.getLogger(__name__)

# === Conversation History Management ===


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

    # 最適化情報を作成
    optimized_tokens = estimate_conversation_tokens(optimized_history, encoding_name)
    optimization_info = {
        "was_optimized": True,
        "optimization_method": "truncation",
        "original_message_count": len(history),
        "optimized_message_count": len(optimized_history),
        "original_tokens": original_tokens,
        "optimized_tokens": optimized_tokens,
        "messages_removed": len(history) - len(optimized_history),
    }

    logger.debug(
        f"Optimized conversation history: {len(history)} messages -> {len(optimized_history)} messages, "
        f"tokens: ~{optimized_tokens}/{max_tokens}"
    )

    return optimized_history, optimization_info


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


# === System Prompt Classes (kept as is from system_prompt_builder.py) ===

"""
System prompt builder for document-aware LLM interactions.

This module provides functionality to build context-aware system prompts
that include repository and document information for enhanced LLM responses.
"""

import hashlib
import json
import logging
import time
from typing import Dict, Any, Optional, List
from pathlib import Path

from doc_ai_helper_backend.models.repository_context import (
    RepositoryContext,
    DocumentMetadata,
    RepositoryContextSummary,
)

logger = logging.getLogger(__name__)


class SystemPromptCache:
    """Simple in-memory cache for system prompts."""

    def __init__(self, ttl_seconds: int = 3600):
        """
        Initialize cache.

        Args:
            ttl_seconds: Time to live for cached prompts in seconds
        """
        self.cache: Dict[str, str] = {}
        self.cache_times: Dict[str, float] = {}
        self.ttl_seconds = ttl_seconds

    def get(self, key: str) -> Optional[str]:
        """Get cached prompt if valid."""
        if key not in self.cache:
            return None

        # Check TTL
        if time.time() - self.cache_times[key] > self.ttl_seconds:
            self._remove(key)
            return None

        return self.cache[key]

    def set(self, key: str, value: str):
        """Cache a prompt."""
        self.cache[key] = value
        self.cache_times[key] = time.time()

    def _remove(self, key: str):
        """Remove a cached item."""
        self.cache.pop(key, None)
        self.cache_times.pop(key, None)

    def clear(self):
        """Clear all cached items."""
        self.cache.clear()
        self.cache_times.clear()

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        valid_items = sum(
            1
            for cache_time in self.cache_times.values()
            if current_time - cache_time <= self.ttl_seconds
        )

        return {
            "total_items": len(self.cache),
            "valid_items": valid_items,
            "expired_items": len(self.cache) - valid_items,
            "ttl_seconds": self.ttl_seconds,
        }


class SystemPromptBuilder:
    """
    Base system prompt builder.

    Builds context-aware system prompts using repository and document information.
    """

    def __init__(self, cache_ttl: int = 3600):
        """
        Initialize the builder.

        Args:
            cache_ttl: Cache time-to-live in seconds
        """
        self.cache = SystemPromptCache(cache_ttl)
        self.templates: Dict[str, Dict[str, Any]] = {}
        self._load_templates()

    def _load_templates(self):
        """Load system prompt templates."""
        # Default templates will be loaded from JSON file
        # For now, provide default templates
        self.templates = self._get_default_templates()

    def _get_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get default system prompt templates."""
        return {
            "minimal_context_ja": {
                "template": """あなたは {repository_context.owner}/{repository_context.repo} リポジトリを扱うアシスタントです。

現在作業中のリポジトリ: {repository_context.owner}/{repository_context.repo}

GitHubツールを使用する際は、特に指定がない限り自動的に "{repository_context.owner}/{repository_context.repo}" リポジトリを使用してください。日本語で自然に応答し、技術的な内容も分かりやすく説明してください。""",
                "required_context": ["repository_context"],
            },
            "contextual_document_assistant_ja": {
                "template": """あなたはリポジトリ {repository_context.owner}/{repository_context.repo} のドキュメントを扱う専門アシスタントです。

現在のコンテキスト：
- リポジトリ: {repository_context.service}:{repository_context.owner}/{repository_context.repo} (ブランチ: {repository_context.ref})
- 現在表示中のドキュメント: {repository_context.current_path}
- ドキュメント形式: {document_metadata.type}
- 最終更新: {document_metadata.last_modified}

{document_content_section}

重要な指示：
1. GitHubのIssueやPull Requestの作成を求められた場合は、自動的に "{repository_context.owner}/{repository_context.repo}" リポジトリを使用してください
2. 「このドキュメント」「このファイル」と言及された場合は、{repository_context.current_path} を指しています
3. ドキュメントの具体的な内容を参照して、詳細で実用的な提案を行ってください
4. 改善提案やフィードバックは、表示中のドキュメントの文脈に基づいて行ってください
5. 日本語で自然に応答し、技術用語は適切に日本語化するか併記してください

利用可能なツール：
- create_github_issue: 現在のリポジトリにIssueを作成
- create_github_pull_request: 現在のリポジトリにPull Requestを作成
- validate_github_repository: リポジトリアクセスの確認

対話例：
- ユーザー「このドキュメントの説明が分かりにくい部分があります」
  → ドキュメント内容を分析し、具体的な改善点を特定してIssueとして提案
- ユーザー「英語の部分を日本語化してほしい」
  → 該当箇所を特定し、日本語化のPull Requestを提案
- ユーザー「このAPIの使用例を追加したい」
  → 適切な場所にサンプルコードを追加するPull Requestを提案""",
                "required_context": ["repository_context", "document_metadata"],
            },
        }

    def generate_cache_key(
        self,
        repository_context: Optional[RepositoryContext] = None,
        document_metadata: Optional[DocumentMetadata] = None,
        document_content: Optional[str] = None,
        template_id: str = "contextual_document_assistant_ja",
    ) -> str:
        """
        Generate cache key for system prompt.

        Args:
            repository_context: Repository context
            document_metadata: Document metadata
            document_content: Document content (hashed for cache key)
            template_id: Template identifier

        Returns:
            Cache key string
        """
        # Create a deterministic cache key
        key_parts = [template_id]

        if repository_context:
            key_parts.extend(
                [
                    repository_context.service.value,
                    repository_context.owner,
                    repository_context.repo,
                    repository_context.ref,
                    repository_context.current_path or "root",
                ]
            )

        if document_metadata:
            key_parts.extend(
                [
                    document_metadata.type.value,
                    document_metadata.last_modified or "unknown",
                    str(document_metadata.file_size or 0),
                ]
            )

        if document_content:
            # Hash the content to avoid extremely long keys
            content_hash = hashlib.md5(document_content.encode("utf-8")).hexdigest()[:8]
            key_parts.append(content_hash)

        # Create deterministic hash
        key_string = "|".join(key_parts)
        cache_key = hashlib.sha256(key_string.encode("utf-8")).hexdigest()[:16]

        return cache_key

    def sanitize_document_content(self, content: str, max_length: int = 8000) -> str:
        """
        Sanitize document content for system prompt inclusion.

        Args:
            content: Raw document content
            max_length: Maximum length in characters

        Returns:
            Sanitized content
        """
        if not content:
            return ""

        # Truncate if too long
        if len(content) > max_length:
            # Try to truncate at a reasonable boundary
            truncated = content[:max_length]

            # Find last complete line
            last_newline = truncated.rfind("\n")
            if last_newline > max_length // 2:  # Don't truncate too aggressively
                truncated = truncated[:last_newline]

            content = truncated + "\n\n... (内容が長いため省略されました)"

        # Escape markdown code blocks to prevent prompt injection
        content = content.replace("```", "\\`\\`\\`")

        return content

    def build_system_prompt(
        self,
        repository_context: Optional[RepositoryContext] = None,
        document_metadata: Optional[DocumentMetadata] = None,
        document_content: Optional[str] = None,
        template_id: str = "contextual_document_assistant_ja",
    ) -> str:
        """
        Build system prompt with context.

        Args:
            repository_context: Repository context
            document_metadata: Document metadata
            document_content: Document content
            template_id: Template identifier

        Returns:
            Generated system prompt
        """
        # Check cache first
        cache_key = self.generate_cache_key(
            repository_context, document_metadata, document_content, template_id
        )

        cached_prompt = self.cache.get(cache_key)
        if cached_prompt:
            logger.debug(f"Using cached system prompt (key: {cache_key})")
            return cached_prompt

        # Get template
        template_data = self.templates.get(template_id)
        if not template_data:
            logger.warning(f"Template not found: {template_id}, using default")
            template_id = "minimal_context_ja"
            template_data = self.templates[template_id]

        template = template_data["template"]
        required_context = template_data.get("required_context", [])

        # Check required context
        context_vars = {}

        if repository_context:
            context_vars["repository_context"] = repository_context

        if document_metadata:
            context_vars["document_metadata"] = document_metadata

        # Validate required context
        missing_context = [ctx for ctx in required_context if ctx not in context_vars]

        if missing_context:
            logger.warning(
                f"Missing required context: {missing_context}, using minimal template"
            )
            template_id = "minimal_context_ja"
            template = self.templates[template_id]["template"]

        # Build document content section
        document_content_section = ""
        if document_content and template_id != "minimal_context_ja":
            sanitized_content = self.sanitize_document_content(document_content)
            if sanitized_content:
                document_content_section = f"""表示中のドキュメント内容：
```{document_metadata.type.value if document_metadata else 'text'}
{sanitized_content}
```"""
            else:
                document_content_section = (
                    "※ドキュメント内容は大きすぎるため表示されていません。"
                )

        # Format template
        try:
            formatted_prompt = template.format(
                repository_context=repository_context,
                document_metadata=document_metadata,
                document_content_section=document_content_section,
            )
        except Exception as e:
            logger.error(f"Error formatting template {template_id}: {e}")
            # Fallback to minimal template
            fallback_template = self.templates["minimal_context_ja"]["template"]
            formatted_prompt = fallback_template.format(
                repository_context=repository_context
            )

        # Cache the result
        self.cache.set(cache_key, formatted_prompt)

        # Log generation
        if repository_context:
            summary = RepositoryContextSummary.from_context(
                repository_context, document_metadata
            )
            logger.info(
                f"Generated system prompt: {summary.repository} - {template_id}"
            )

        return formatted_prompt

    def clear_cache(self):
        """Clear the system prompt cache."""
        self.cache.clear()
        logger.info("System prompt cache cleared")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.cache.get_stats()


class JapaneseSystemPromptBuilder(SystemPromptBuilder):
    """
    Japanese-optimized system prompt builder.

    Specialized for Japanese documentation and development workflows.
    """

    def _get_default_templates(self) -> Dict[str, Dict[str, Any]]:
        """Get Japanese-optimized templates."""
        templates = super()._get_default_templates()

        # Add specialized Japanese templates
        templates.update(
            {
                "documentation_specialist_ja": {
                    "template": """あなたは日本語ドキュメントの専門家として、{repository_context.owner}/{repository_context.repo} のドキュメント改善をサポートします。

現在のドキュメント: {repository_context.current_path}

{document_content_section}

専門領域：
✅ 日本語の文章構成と可読性の改善
✅ 技術ドキュメントの構造化と整理
✅ コードサンプルの説明と改善
✅ 用語の統一と適切な日本語化
✅ ユーザビリティを考慮した情報設計

改善提案の指針：
1. 読み手の立場に立った分かりやすさを重視
2. 具体的で実行可能な改善案を提示
3. 技術用語は日本語での説明を併記
4. 構造的な問題があれば全体的な再構成を提案
5. 実際のGitHub IssueやPull Requestとして具体化

このドキュメントに関する質問や改善要望があれば、専門的な観点から詳細に分析し、実行可能な形で提案します。""",
                    "required_context": ["repository_context", "document_metadata"],
                },
                "code_reviewer_ja": {
                    "template": """あなたは {repository_context.owner}/{repository_context.repo} のコードレビューアーとして機能します。

現在確認中のファイル: {repository_context.current_path}

{document_content_section}

レビュー観点：
🔍 コードの品質と可読性
🔍 日本語コメントの適切性
🔍 命名規則の一貫性
🔍 ドキュメント化の充実度
🔍 ベストプラクティスの適用

フィードバック形式：
- 改善点は具体的な修正案とともに提示
- 良い点も積極的に評価
- 学習のための追加説明を提供
- 必要に応じてIssueやPull Requestとして具体化

コードに関する質問や改善要望があれば、技術的に正確で実用的なフィードバックを提供します。""",
                    "required_context": ["repository_context", "document_metadata"],
                },
            }
        )

        return templates

    def select_appropriate_template(
        self,
        repository_context: RepositoryContext,
        document_metadata: Optional[DocumentMetadata] = None,
    ) -> str:
        """
        Select appropriate template based on context.

        Args:
            repository_context: Repository context
            document_metadata: Document metadata

        Returns:
            Template ID
        """
        if not document_metadata:
            return "minimal_context_ja"

        # Check if it's a documentation file
        if document_metadata.is_documentation:
            if "README" in (repository_context.current_path or "").upper():
                return "documentation_specialist_ja"
            elif any(
                keyword in (repository_context.current_path or "").lower()
                for keyword in ["doc", "docs", "api", "spec", "guide", "manual"]
            ):
                return "documentation_specialist_ja"

        # Check if it's a code file
        elif document_metadata.is_code_file:
            return "code_reviewer_ja"

        # Default to contextual assistant
        return "contextual_document_assistant_ja"
