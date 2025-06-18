"""
API dependencies.
"""

from typing import Callable

from fastapi import Depends

from doc_ai_helper_backend.services.document_service import DocumentService
from doc_ai_helper_backend.services.llm import LLMServiceBase, LLMServiceFactory
from doc_ai_helper_backend.core.config import settings


def get_document_service() -> DocumentService:
    """Get document service instance.

    Returns:
        DocumentService: Document service instance
    """
    return DocumentService()


def get_llm_service() -> LLMServiceBase:
    """Get LLM service instance.

    Returns:
        LLMServiceBase: LLM service instance
    """
    # Use the default provider from settings
    provider = settings.default_llm_provider

    # In development/testing mode, use mock service
    if settings.environment.lower() in ["development", "testing"]:
        provider = "mock"  # Configure provider-specific settings
    config = {}
    if provider == "openai":
        config["api_key"] = settings.openai_api_key
        config["default_model"] = settings.default_openai_model
        if settings.openai_base_url:
            config["base_url"] = settings.openai_base_url

    # Create service instance
    return LLMServiceFactory.create(provider, **config)
