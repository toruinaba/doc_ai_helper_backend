"""
Prompt Manager (Prompt Manager)

LLMサービス向けのシステムプロンプト管理機能を提供します。

主要機能:
- システムプロンプトのキャッシュ管理
- コンテキスト対応システムプロンプトの構築
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Dict, Any, Optional, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

logger = logging.getLogger(__name__)


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
        repository_context: "RepositoryContext",
        document_metadata: Optional["DocumentMetadata"] = None,
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
        repository_context: "RepositoryContext",
        document_metadata: Optional["DocumentMetadata"] = None,
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
        repository_context: "RepositoryContext",
        system_prompt: str,
        document_metadata: Optional["DocumentMetadata"] = None,
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
        repository_context: "RepositoryContext",
        document_metadata: Optional["DocumentMetadata"] = None,
        custom_instructions: Optional[str] = None,
        template_id: Optional[str] = None,
        enable_bilingual_tools: bool = True,
    ) -> str:
        """
        コンテキスト対応システムプロンプトを構築

        Args:
            repository_context: リポジトリコンテキスト
            document_metadata: ドキュメントメタデータ
            custom_instructions: カスタム指示
            template_id: 使用するテンプレートID
            enable_bilingual_tools: バイリンガルツール機能を有効にするか

        Returns:
            str: 構築されたシステムプロンプト
        """
        # キャッシュから取得を試行
        if self.cache:
            cached_prompt = self.cache.get(repository_context, document_metadata)
            if (
                cached_prompt and not custom_instructions and not enable_bilingual_tools
            ):  # カスタム指示やバイリンガル機能がある場合はキャッシュしない
                return cached_prompt

        # システムプロンプトを構築
        prompt_parts = []

        # BiLingual Tools System Prompt (if enabled)
        if enable_bilingual_tools:
            prompt_parts.append("""=== BILINGUAL TOOL EXECUTION SYSTEM ===

IMPORTANT: You have access to tools for document analysis and repository management. When the user requests tool execution in Japanese, you MUST:

1. **TOOL SELECTION**: Interpret Japanese tool requests as English tool execution instructions
   - When user says "summarize_document_with_llm ツールを呼び出してください" → Execute summarize_document_with_llm tool
   - When user says "create_improvement_recommendations_with_llm ツールを呼び出してください" → Execute create_improvement_recommendations_with_llm tool  
   - When user says "create_git_issue ツールを呼び出してください" → Execute create_git_issue tool
   - When user requests multiple tools → Execute ALL requested tools

2. **TOOL EXECUTION**: Always execute tools when explicitly requested by the user
   - Use auto_include_document=True to automatically retrieve document content
   - Pass appropriate parameters to each tool
   - Execute multiple tools if requested

3. **RESPONSE LANGUAGE**: Always respond to the user in Japanese (日本語)
   - Tool execution results should be summarized in Japanese
   - Maintain natural Japanese conversation flow
   - Provide helpful explanations in Japanese

4. **PRIORITY**: Tool execution takes priority over conversation
   - If user requests tools, execute them immediately
   - Don't ask for confirmation - execute the requested tools
   - Provide results and summary in Japanese""")

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

        # キャッシュに保存（カスタム指示やバイリンガル機能がない場合のみ）
        if self.cache and not custom_instructions and not enable_bilingual_tools:
            self.cache.set(repository_context, system_prompt, document_metadata)

        return system_prompt
