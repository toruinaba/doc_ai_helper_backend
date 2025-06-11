"""
Configuration settings for the application.
"""

import os
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Basic settings
    debug: bool = Field(False, env="DEBUG")
    environment: str = Field("production", env="ENVIRONMENT")
    log_level: str = Field("INFO", env="LOG_LEVEL")

    # Application settings
    app_name: str = Field("doc_ai_helper", env="APP_NAME")
    app_version: str = Field("0.1.0", env="APP_VERSION")
    secret_key: str = Field(..., env="SECRET_KEY")

    # API settings
    api_prefix: str = Field("/api/v1", env="API_PREFIX")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False
    }


settings = Settings()
