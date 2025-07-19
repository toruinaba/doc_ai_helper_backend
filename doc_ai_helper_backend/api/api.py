"""
API router for the application.
"""

from fastapi import APIRouter

from doc_ai_helper_backend.api.endpoints.documents import router as documents_router
from doc_ai_helper_backend.api.endpoints.health import router as health_router
from doc_ai_helper_backend.api.endpoints.search import router as search_router
from doc_ai_helper_backend.api.endpoints.llm import router as llm_router
from doc_ai_helper_backend.api.endpoints.repositories import router as repositories_router
from doc_ai_helper_backend.core.config import settings

router = APIRouter(prefix=settings.api_prefix)

# Include routers for different endpoints
router.include_router(health_router, prefix="/health")
router.include_router(documents_router, prefix="/documents")
router.include_router(search_router, prefix="/search")
router.include_router(llm_router, prefix="/llm")
router.include_router(repositories_router)  # prefix already defined in router
