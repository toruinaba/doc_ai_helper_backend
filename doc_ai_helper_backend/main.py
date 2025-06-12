"""
Main application entry point.
"""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from doc_ai_helper_backend.api.api import router as api_router
from doc_ai_helper_backend.api.error_handlers import setup_error_handlers
from doc_ai_helper_backend.core.config import settings
from doc_ai_helper_backend.core.logging import setup_logging

# Set up logging
setup_logging()
logger = logging.getLogger("doc_ai_helper")

# Create FastAPI application
app = FastAPI(
    title="Document AI Helper API",
    description="API for Document AI Helper",
    version=settings.app_version,
    debug=settings.debug,
)

# Set up CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Modify in production to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Setup error handlers
setup_error_handlers(app)


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": f"Welcome to {settings.app_name} API",
        "version": settings.app_version,
        "environment": settings.environment,
    }


# Include API router
app.include_router(api_router)

# Run application
if __name__ == "__main__":
    import uvicorn

    logger.info(f"Starting {settings.app_name} application")
    uvicorn.run(
        "doc_ai_helper_backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
