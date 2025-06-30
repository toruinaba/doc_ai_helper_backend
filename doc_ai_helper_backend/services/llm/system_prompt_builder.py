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
