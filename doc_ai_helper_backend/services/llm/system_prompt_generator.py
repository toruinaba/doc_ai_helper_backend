"""
System Prompt Generation

システムプロンプト生成機能を提供します。
リポジトリコンテキスト、ドキュメントメタデータ、ドキュメント内容を統合して
適切なシステムプロンプトを生成します。
"""

import logging
from typing import Optional, TYPE_CHECKING

# Forward references for repository context models
if TYPE_CHECKING:
    from doc_ai_helper_backend.models.repository_context import (
        RepositoryContext,
        DocumentMetadata,
    )

logger = logging.getLogger(__name__)


def generate_system_prompt(
    repository_context: Optional["RepositoryContext"] = None,
    document_metadata: Optional["DocumentMetadata"] = None,
    document_content: Optional[str] = None,
    include_document_in_system_prompt: bool = True,
) -> Optional[str]:
    """
    統合されたシステムプロンプト生成
    
    Args:
        repository_context: リポジトリコンテキスト情報
        document_metadata: ドキュメントメタデータ
        document_content: ドキュメント内容
        include_document_in_system_prompt: システムプロンプトにドキュメントを含めるか
        
    Returns:
        生成されたシステムプロンプト、または None
    """
    try:
        if not include_document_in_system_prompt:
            return None

        prompt_parts = []

        # バイリンガルツールシステムプロンプト（常に有効）
        prompt_parts.append(_build_bilingual_tool_system_prompt())

        # リポジトリコンテキスト情報
        if repository_context:
            prompt_parts.append(f"リポジトリ: {repository_context.owner}/{repository_context.repo}")
            
            if repository_context.current_path:
                prompt_parts.append(f"現在のファイル: {repository_context.current_path}")

        # ドキュメントメタデータ情報
        if document_metadata:
            # DocumentTypeを使用してファイルタイプを判定
            doc_type = document_metadata.type
            doc_type_value = doc_type.value if hasattr(doc_type, 'value') else str(doc_type)
            
            if doc_type_value in ['python', 'javascript', 'typescript', 'json', 'yaml']:
                prompt_parts.append("このファイルはコードファイルです。")
            elif doc_type_value in ['markdown', 'html', 'text']:
                prompt_parts.append("このファイルはドキュメントファイルです。")
            else:
                prompt_parts.append(f"ファイルタイプ: {doc_type_value}")
                
            # ファイルサイズ情報も追加
            if hasattr(document_metadata, 'file_size') and document_metadata.file_size:
                prompt_parts.append(f"ファイルサイズ: {document_metadata.file_size} bytes")

        # ドキュメント内容埋め込み
        if document_content:
            prompt_parts.append("=== 現在のドキュメント内容 ===")
            
            # 長すぎる場合は切り詰め（トークン制限を考慮）
            max_content_length = 8000  # 約2000トークンに相当
            if len(document_content) > max_content_length:
                truncated_content = document_content[:max_content_length] + "\n...(内容が長いため省略されました)"
                prompt_parts.append(truncated_content)
                logger.info(f"Document content truncated from {len(document_content)} to {max_content_length} characters")
            else:
                prompt_parts.append(document_content)
                logger.info(f"Full document content included: {len(document_content)} characters")
            
            prompt_parts.append("=== ドキュメント内容ここまで ===")
            prompt_parts.append("上記のドキュメント内容を参考にして、コンテキストに基づいた回答を提供してください。")

        return "\n".join(prompt_parts)

    except Exception as e:
        logger.warning(f"Failed to generate system prompt: {str(e)}, continuing without system prompt")
        return None


def _build_bilingual_tool_system_prompt() -> str:
    """
    バイリンガルツール実行システムのプロンプトを構築
    
    Returns:
        バイリンガルツールプロンプト文字列
    """
    return """=== BILINGUAL TOOL EXECUTION SYSTEM ===

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
   - Provide results and summary in Japanese"""