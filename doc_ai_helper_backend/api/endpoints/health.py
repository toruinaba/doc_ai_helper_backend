"""
Health check API endpoints.
"""

import logging
from typing import Dict

from fastapi import APIRouter

from doc_ai_helper_backend.core.config import settings

# Logger
logger = logging.getLogger("doc_ai_helper")

# Router
router = APIRouter(tags=["health"])


@router.get(
    "/",
    response_model=Dict[str, str],
    summary="Health check",
    description="Check if the API is up and running",
)
async def health_check():
    """
    Perform a health check.

    Returns:
        Dict[str, str]: Health status information
    """
    from datetime import datetime

    logger.debug("Health check requested")
    return {
        "status": "ok",
        "version": settings.app_version,
        "timestamp": datetime.now().isoformat(),
    }
