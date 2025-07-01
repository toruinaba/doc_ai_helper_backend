"""
Configuration settings for the application.
"""

import os
from typing import List, Optional

from pydantic import Field, HttpUrl
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Basic settings
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="production", env="ENVIRONMENT")
    log_level: str = Field(default="INFO", env="LOG_LEVEL")

    # Application settings
    app_name: str = Field(default="doc_ai_helper", env="APP_NAME")
    app_version: str = Field(default="0.1.0", env="APP_VERSION")
    secret_key: str = Field(env="SECRET_KEY")

    # API settings
    api_prefix: str = Field(default="/api/v1", env="API_PREFIX")  # Database settings
    database_url: str = Field(default="sqlite:///./data/app.db", env="DATABASE_URL")

    # Git service settings
    github_token: Optional[str] = Field(default=None, env="GITHUB_TOKEN")

    # Forgejo service settings
    forgejo_token: Optional[str] = Field(default=None, env="FORGEJO_TOKEN")
    forgejo_base_url: Optional[str] = Field(default=None, env="FORGEJO_BASE_URL")
    forgejo_username: Optional[str] = Field(default=None, env="FORGEJO_USERNAME")
    forgejo_password: Optional[str] = Field(default=None, env="FORGEJO_PASSWORD")

    # GitLab settings (将来拡張用)
    gitlab_token: Optional[str] = Field(default=None, env="GITLAB_TOKEN")
    gitlab_base_url: Optional[str] = Field(
        default="https://gitlab.com", env="GITLAB_BASE_URL"
    )

    # Git service management
    default_git_service: str = Field(default="github", env="DEFAULT_GIT_SERVICE")
    supported_git_services: List[str] = Field(
        default=["github", "forgejo", "mock"], env="SUPPORTED_GIT_SERVICES"
    )

    # LLM service settings
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, env="OPENAI_BASE_URL")
    anthropic_api_key: Optional[str] = Field(default=None, env="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    default_llm_provider: str = Field(default="openai", env="DEFAULT_LLM_PROVIDER")
    default_openai_model: str = Field(
        default="gpt-3.5-turbo", env="DEFAULT_OPENAI_MODEL"
    )
    default_anthropic_model: str = Field(
        default="claude-3-sonnet-20240229", env="DEFAULT_ANTHROPIC_MODEL"
    )
    default_gemini_model: str = Field(default="gemini-pro", env="DEFAULT_GEMINI_MODEL")
    llm_cache_ttl: int = Field(
        default=3600, env="LLM_CACHE_TTL"
    )  # Cache TTL in seconds
    llm_rate_limit: int = Field(default=60, env="LLM_RATE_LIMIT")  # Requests per minute

    # Cache settings
    cache_enabled: bool = Field(default=True, env="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, env="CACHE_TTL")  # Default: 1 hour
    redis_url: Optional[str] = Field(default=None, env="REDIS_URL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
