"""
Configuration settings for the application.
"""

import os
from typing import List, Optional

from pydantic import Field
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application settings."""

    # Basic settings
    debug: bool = Field(default=False, alias="DEBUG")
    environment: str = Field(default="production", alias="ENVIRONMENT")
    log_level: str = Field(default="INFO", alias="LOG_LEVEL")

    # Application settings
    app_name: str = Field(default="doc_ai_helper", alias="APP_NAME")
    app_version: str = Field(default="0.1.0", alias="APP_VERSION")
    secret_key: str = Field(default="dev-secret-key", alias="SECRET_KEY")

    # API settings
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    # Database settings
    database_url: str = Field(default="sqlite:///./data/app.db", alias="DATABASE_URL")

    # Git service settings
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")

    # Forgejo service settings
    forgejo_token: Optional[str] = Field(default=None, alias="FORGEJO_TOKEN")
    forgejo_base_url: Optional[str] = Field(default=None, alias="FORGEJO_BASE_URL")
    forgejo_username: Optional[str] = Field(default=None, alias="FORGEJO_USERNAME")
    forgejo_password: Optional[str] = Field(default=None, alias="FORGEJO_PASSWORD")

    # GitLab settings (将来拡張用)
    gitlab_token: Optional[str] = Field(default=None, alias="GITLAB_TOKEN")
    gitlab_base_url: Optional[str] = Field(
        default="https://gitlab.com", alias="GITLAB_BASE_URL"
    )

    # Git service management
    default_git_service: str = Field(default="github", alias="DEFAULT_GIT_SERVICE")
    supported_git_services: List[str] = Field(
        default=["github", "forgejo", "mock"], alias="SUPPORTED_GIT_SERVICES"
    )

    # LLM service settings
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    anthropic_api_key: Optional[str] = Field(default=None, alias="ANTHROPIC_API_KEY")
    gemini_api_key: Optional[str] = Field(default=None, alias="GEMINI_API_KEY")
    default_llm_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    default_openai_model: str = Field(
        default="gpt-3.5-turbo", alias="DEFAULT_OPENAI_MODEL"
    )
    default_anthropic_model: str = Field(
        default="claude-3-sonnet-20240229", alias="DEFAULT_ANTHROPIC_MODEL"
    )
    default_gemini_model: str = Field(
        default="gemini-pro", alias="DEFAULT_GEMINI_MODEL"
    )
    llm_cache_ttl: int = Field(
        default=3600, alias="LLM_CACHE_TTL"
    )  # Cache TTL in seconds
    llm_rate_limit: int = Field(
        default=60, alias="LLM_RATE_LIMIT"
    )  # Requests per minute

    # Cache settings
    cache_enabled: bool = Field(default=True, alias="CACHE_ENABLED")
    cache_ttl: int = Field(default=3600, alias="CACHE_TTL")  # Default: 1 hour
    redis_url: Optional[str] = Field(default=None, alias="REDIS_URL")

    # E2E Test settings
    test_forgejo_owner: Optional[str] = Field(default=None, alias="TEST_FORGEJO_OWNER")
    test_forgejo_repo: Optional[str] = Field(default=None, alias="TEST_FORGEJO_REPO")
    backend_api_url: str = Field(
        default="http://localhost:8000", alias="BACKEND_API_URL"
    )
    test_llm_provider: str = Field(default="mock", alias="TEST_LLM_PROVIDER")
    test_llm_model: str = Field(default="gpt-3.5-turbo", alias="TEST_LLM_MODEL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


settings = Settings()
