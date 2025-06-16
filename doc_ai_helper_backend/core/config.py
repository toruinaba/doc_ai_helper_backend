"""
Configuration settings for the application.
"""

import os
from typing import Optional

from pydantic import Field, HttpUrl
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
    api_prefix: str = Field("/api/v1", env="API_PREFIX")  # Database settings
    database_url: str = Field("sqlite:///./data/app.db", env="DATABASE_URL")

    # Git service settings
    github_token: Optional[str] = Field(None, env="GITHUB_TOKEN")

    # LLM service settings
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(None, env="GEMINI_API_KEY")
    default_llm_provider: str = Field("openai", env="DEFAULT_LLM_PROVIDER")
    default_openai_model: str = Field("gpt-4", env="DEFAULT_OPENAI_MODEL")
    default_anthropic_model: str = Field(
        "claude-3-sonnet-20240229", env="DEFAULT_ANTHROPIC_MODEL"
    )
    default_gemini_model: str = Field("gemini-pro", env="DEFAULT_GEMINI_MODEL")
    llm_cache_ttl: int = Field(3600, env="LLM_CACHE_TTL")  # Cache TTL in seconds
    llm_rate_limit: int = Field(60, env="LLM_RATE_LIMIT")  # Requests per minute

    # Cache settings
    cache_enabled: bool = Field(True, env="CACHE_ENABLED")
    cache_ttl: int = Field(3600, env="CACHE_TTL")  # Default: 1 hour
    redis_url: Optional[str] = Field(None, env="REDIS_URL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
