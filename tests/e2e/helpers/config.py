"""
E2E test configuration management.

This module provides configuration management specifically for E2E tests,
integrating with the main application settings while providing E2E-specific
defaults and validation.
"""

import os
from typing import Optional

from doc_ai_helper_backend.core.config import settings


class E2EConfig:
    """E2E test configuration class."""
    
    def __init__(self):
        """Initialize E2E configuration with environment-based settings."""
        # LLM Provider - use E2E_LLM_PROVIDER if set, otherwise fall back to main setting
        self.llm_provider = settings.e2e_llm_provider or settings.default_llm_provider
        
        # API Base URL
        self.api_base_url = settings.e2e_api_base_url
        
        # GitHub configuration
        self.github_owner = settings.e2e_github_owner
        self.github_repo = settings.e2e_github_repo
        self.github_token = settings.github_token
        
        # Forgejo configuration  
        self.forgejo_owner = settings.e2e_forgejo_owner
        self.forgejo_repo = settings.e2e_forgejo_repo
        self.forgejo_token = settings.forgejo_token
        self.forgejo_base_url = settings.forgejo_base_url
        self.forgejo_username = settings.forgejo_username
        self.forgejo_password = settings.forgejo_password
        
        # Test identifiers
        self.test_issue_marker = "E2E-TEST"
        self.test_title_prefix = "[E2E Test]"
    
    @property
    def has_github_config(self) -> bool:
        """Check if GitHub configuration is available."""
        return bool(self.github_repo and self.github_token)
    
    @property
    def has_forgejo_config(self) -> bool:
        """Check if Forgejo configuration is available."""
        return bool(
            self.forgejo_repo and 
            self.forgejo_base_url and 
            (self.forgejo_token or (self.forgejo_username and self.forgejo_password))
        )
    
    @property
    def available_services(self) -> list[str]:
        """Get list of available Git services for testing."""
        services = []
        if self.has_github_config:
            services.append("github")
        if self.has_forgejo_config:
            services.append("forgejo")
        return services
    
    def get_repository_config(self, service: str) -> dict:
        """Get repository configuration for a specific service."""
        if service == "github":
            return {
                "service": "github",
                "owner": self.github_owner,
                "repo": self.github_repo,
                "token": self.github_token,
                "available": self.has_github_config
            }
        elif service == "forgejo":
            return {
                "service": "forgejo", 
                "owner": self.forgejo_owner,
                "repo": self.forgejo_repo,
                "base_url": self.forgejo_base_url,
                "token": self.forgejo_token,
                "username": self.forgejo_username,
                "password": self.forgejo_password,
                "available": self.has_forgejo_config
            }
        else:
            raise ValueError(f"Unknown service: {service}")
    
    def validate_config(self) -> list[str]:
        """Validate E2E configuration and return list of issues."""
        issues = []
        
        # Check if at least one Git service is configured
        if not self.available_services:
            issues.append("No Git services configured for E2E testing")
        
        # Validate GitHub config if provided
        if self.github_repo and not self.github_token:
            issues.append("GitHub repository configured but no GitHub token provided")
        
        # Validate Forgejo config if provided
        if self.forgejo_repo:
            if not self.forgejo_base_url:
                issues.append("Forgejo repository configured but no base URL provided")
            if not self.forgejo_token and not (self.forgejo_username and self.forgejo_password):
                issues.append("Forgejo repository configured but no authentication provided")
        
        # Check API base URL
        if not self.api_base_url:
            issues.append("API base URL not configured")
        
        return issues
    
    def print_config_summary(self):
        """Print configuration summary for debugging."""
        print("=== E2E Test Configuration ===")
        print(f"API Base URL: {self.api_base_url}")
        print(f"LLM Provider: {self.llm_provider}")
        print(f"Available Services: {', '.join(self.available_services)}")
        
        if self.has_github_config:
            print(f"GitHub: {self.github_owner}/{self.github_repo}")
        else:
            print("GitHub: Not configured")
        
        if self.has_forgejo_config:
            print(f"Forgejo: {self.forgejo_owner}/{self.forgejo_repo} at {self.forgejo_base_url}")
        else:
            print("Forgejo: Not configured")
        
        validation_issues = self.validate_config()
        if validation_issues:
            print("⚠️  Configuration Issues:")
            for issue in validation_issues:
                print(f"  - {issue}")
        else:
            print("✅ Configuration valid")
        print("===============================")


# Convenience function for test modules
def get_e2e_config() -> E2EConfig:
    """Get E2E configuration instance."""
    return E2EConfig()


# Environment validation helper
def check_e2e_environment() -> bool:
    """Check if E2E environment is properly configured."""
    config = E2EConfig()
    return len(config.validate_config()) == 0