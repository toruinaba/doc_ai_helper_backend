"""
ドキュメントプロセッサーのファクトリーを提供するモジュール。
"""

from typing import Dict, Type

from doc_ai_helper_backend.core.exceptions import DocumentParsingException
from doc_ai_helper_backend.models.document import DocumentType
from doc_ai_helper_backend.services.document_processors.base_processor import (
    DocumentProcessorBase,
)
from doc_ai_helper_backend.services.document_processors.markdown_processor import (
    MarkdownProcessor,
)


class DocumentProcessorFactory:
    """ドキュメントタイプに応じたプロセッサーを生成するファクトリークラス。"""

    # 利用可能なプロセッサー
    _processors: Dict[DocumentType, Type[DocumentProcessorBase]] = {
        DocumentType.MARKDOWN: MarkdownProcessor,
        # 将来的にQuartoやHTMLを追加
        # DocumentType.QUARTO: QuartoProcessor,
        # DocumentType.HTML: HTMLProcessor,
    }

    @classmethod
    def create(cls, document_type: DocumentType) -> DocumentProcessorBase:
        """
        ドキュメントタイプに応じたプロセッサーを生成する。

        Args:
            document_type: ドキュメントタイプ

        Returns:
            適切なドキュメントプロセッサーインスタンス

        Raises:
            DocumentParsingException: サポートされていないドキュメントタイプの場合
        """
        processor_class = cls._processors.get(document_type)

        if not processor_class:
            raise DocumentParsingException(
                f"Unsupported document type: {document_type}"
            )

        return processor_class()
