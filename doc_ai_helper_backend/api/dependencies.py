"""
API dependencies.
"""

from typing import Callable

from fastapi import Depends

from doc_ai_helper_backend.services.document_service import DocumentService


def get_document_service() -> DocumentService:
    """Get document service instance.

    Returns:
        DocumentService: Document service instance
    """
    return DocumentService()
