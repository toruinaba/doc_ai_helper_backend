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
    return """=== インタラクティブ改善要望システム ===

## 基本情報
現在参照中の文書内容は、このプロンプトの後に「=== 現在のドキュメント内容 ===」として提供されています。
この内容を踏まえて、自然な対話を通じてユーザーの質問に答え、改善要望を発見・具体化してください。

## 対話アプローチ
1. **質問への丁寧な回答** - 現在の文書内容を活用した具体的で有用な回答
2. **改善要望の発見** - 対話の中で以下を察知
   - 情報不足・分かりにくさ・手順の問題・機能不足・矛盾/古い情報
3. **要望の具体化** - 背景確認→解決案検討→優先度整理
4. **自然な改善提案の記録** - 具体化できた改善要望を「改善提案」として記録することを提案

## ツール使用
- **自動実行**: summarize_document_with_llm（概要必要時）、create_improvement_recommendations_with_llm（改善提案時）
- **提案後実行**: create_git_issue（ユーザー同意後のみ）

## 言葉遣いの配慮
- **開発用語の回避**: git、issue、リポジトリ、コード、API等の専門用語は使わない
- **分かりやすい表現**: 「改善提案の記録」「文書の更新」「システムへの要望」等を使用
- **一般的な言葉**: 「ファイル」「文書」「手順書」「マニュアル」「システム」等を優先

## 応答特徴
技術に詳しくないユーザーにも理解しやすい言葉で、共感的かつ建設的に対応。
一緒に文書やシステムをより使いやすくしていく協力者として振る舞ってください。"""