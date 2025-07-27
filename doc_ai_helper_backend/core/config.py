"""
Configuration settings for the application.
"""

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

    # API settings
    api_prefix: str = Field(default="/api/v1", alias="API_PREFIX")

    # Git service settings
    github_token: Optional[str] = Field(default=None, alias="GITHUB_TOKEN")

    # Forgejo service settings
    forgejo_token: Optional[str] = Field(default=None, alias="FORGEJO_TOKEN")
    forgejo_base_url: Optional[str] = Field(default=None, alias="FORGEJO_BASE_URL")
    forgejo_username: Optional[str] = Field(default=None, alias="FORGEJO_USERNAME")
    forgejo_password: Optional[str] = Field(default=None, alias="FORGEJO_PASSWORD")

    # Git service management
    default_git_service: str = Field(default="github", alias="DEFAULT_GIT_SERVICE")

    # LLM service settings (OpenAI only - as currently implemented)
    openai_api_key: Optional[str] = Field(default=None, alias="OPENAI_API_KEY")
    openai_base_url: Optional[str] = Field(default=None, alias="OPENAI_BASE_URL")
    default_openai_model: str = Field(
        default="gpt-3.5-turbo", alias="DEFAULT_OPENAI_MODEL"
    )

    # LLM configuration
    default_llm_provider: str = Field(default="openai", alias="DEFAULT_LLM_PROVIDER")
    llm_cache_ttl: int = Field(default=3600, alias="LLM_CACHE_TTL")  # 1 hour in seconds

    # Database settings
    database_url: str = Field(default="sqlite:///./app.db", alias="DATABASE_URL")
    database_echo: bool = Field(default=False, alias="DATABASE_ECHO")  # SQL ログ出力
    
    # Repository management feature flags
    enable_repository_management: bool = Field(default=False, alias="ENABLE_REPOSITORY_MANAGEMENT")
    enable_repository_context_integration: bool = Field(default=False, alias="ENABLE_REPO_CONTEXT_INTEGRATION")

    # Server settings
    server_host: str = Field(default="0.0.0.0", alias="HOST")
    server_port: int = Field(default=8000, alias="PORT")

    # E2E Test settings - minimal additions for test target repositories
    e2e_github_owner: str = Field(default="octocat", alias="E2E_GITHUB_OWNER")
    e2e_github_repo: str = Field(default="Hello-World", alias="E2E_GITHUB_REPO")
    e2e_forgejo_owner: str = Field(default="", alias="E2E_FORGEJO_OWNER")
    e2e_forgejo_repo: str = Field(default="", alias="E2E_FORGEJO_REPO")
    e2e_llm_provider: str = Field(default="", alias="E2E_LLM_PROVIDER")
    e2e_api_base_url: str = Field(default="http://localhost:8000", alias="E2E_API_BASE_URL")

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
        "extra": "ignore",  # 追加の設定項目を無視する
    }


settings = Settings()
