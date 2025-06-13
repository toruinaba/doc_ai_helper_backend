"""
API endpoints initialization.
"""

from fastapi import APIRouter

from doc_ai_helper_backend.api.endpoints.documents import router as documents_router
from doc_ai_helper_backend.api.endpoints.health import router as health_router
from doc_ai_helper_backend.api.endpoints.repositories import (
    router as repositories_router,
)
from doc_ai_helper_backend.api.endpoints.search import router as search_router
