"""
API dependencies.
"""

from typing import Callable

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from doc_ai_helper_backend.services.document import DocumentService
from doc_ai_helper_backend.services.llm import LLMServiceBase, LLMServiceFactory
from doc_ai_helper_backend.services.llm.orchestrator import LLMOrchestrator
from doc_ai_helper_backend.services.git.factory import GitServiceFactory
from doc_ai_helper_backend.services.repository_service import RepositoryService
from doc_ai_helper_backend.db.database import get_db
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
    # Use the default provider from settings - no automatic mock fallback
    provider = settings.default_llm_provider

    # Configure provider-specific settings
    config = {}
    if provider == "openai":
        config["api_key"] = settings.openai_api_key
        config["default_model"] = settings.default_openai_model
        if settings.openai_base_url:
            config["base_url"] = settings.openai_base_url
    elif provider == "anthropic":
        config["api_key"] = settings.anthropic_api_key
    elif provider == "gemini":
        config["api_key"] = settings.gemini_api_key

    # Create service instance with MCP integration
    # If API keys are missing, the factory will raise an appropriate error
    return LLMServiceFactory.create(provider, **config)


def get_git_service_factory() -> GitServiceFactory:
    """Get Git service factory instance.

    Returns:
        GitServiceFactory: Git service factory instance
    """
    return GitServiceFactory()


def get_llm_orchestrator() -> LLMOrchestrator:
    """Get LLMOrchestrator instance.

    Returns:
        LLMOrchestrator: LLMOrchestrator instance
    """
    # 簡単なdictベースのキャッシュサービスを提供
    # 本格的なキャッシュが必要な場合は、Redis等を使用
    cache_service = {}
    return LLMOrchestrator(cache_service)


def get_llm_orchestrator_with_document_service(
    document_service: DocumentService = Depends(get_document_service)
) -> LLMOrchestrator:
    """Get LLMOrchestrator instance with DocumentService integration.

    Args:
        document_service: DocumentService dependency
        
    Returns:
        LLMOrchestrator: LLMOrchestrator instance with DocumentService
    """
    # 簡単なdictベースのキャッシュサービスを提供
    cache_service = {}
    orchestrator = LLMOrchestrator(cache_service)
    orchestrator.document_service = document_service
    return orchestrator


def get_repository_service(db: AsyncSession = Depends(get_db)) -> RepositoryService:
    """
    Get repository service instance.
    
    Args:
        db: Database session dependency
        
    Returns:
        RepositoryService: Repository service instance
    """
    return RepositoryService(db)
