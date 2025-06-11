"""
Logging configuration for the application.
"""

import logging
import os
import sys
from typing import List, Tuple

from doc_ai_helper_backend.core.config import settings


def setup_logging() -> None:
    """Set up logging configuration."""
    log_level = getattr(logging, settings.log_level.upper(), logging.INFO)
    log_format = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

    # Configure basic logging
    logging.basicConfig(
        level=log_level,
        format=log_format,
        handlers=[
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.access").setLevel(logging.WARNING)
    logging.getLogger("uvicorn.error").setLevel(logging.ERROR)

    # Create logger
    logger = logging.getLogger("doc_ai_helper")
    logger.setLevel(log_level)

    # Log startup information
    logger.info(
        f"Starting application in {settings.environment} mode with debug={settings.debug}"
    )
