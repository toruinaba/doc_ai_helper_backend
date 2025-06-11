"""
API router for the application.
"""

from fastapi import APIRouter

from doc_ai_helper_backend.core.config import settings

router = APIRouter(prefix=settings.api_prefix)


@router.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok", "version": settings.app_version}
