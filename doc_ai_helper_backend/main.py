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
from doc_ai_helper_backend.db.database import init_db, close_db

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


# Application lifecycle events
@app.on_event("startup")
async def startup_event():
    """Initialize application on startup."""
    logger.info("Initializing application...")
    
    # Initialize database tables if they don't exist
    if settings.enable_repository_management:
        try:
            await init_db()
            logger.info("Database initialization completed")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}")
            raise
    else:
        logger.info("Repository management disabled - skipping database initialization")


@app.on_event("shutdown")
async def shutdown_event():
    """Clean up on application shutdown."""
    logger.info("Shutting down application...")
    
    if settings.enable_repository_management:
        try:
            await close_db()
            logger.info("Database connections closed")
        except Exception as e:
            logger.error(f"Error closing database connections: {e}")


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
