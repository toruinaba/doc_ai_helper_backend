"""
Unit tests for LLM service factory.

This module contains tests for the LLMServiceFactory class that manages
service registration and instantiation.
"""

import pytest
from unittest.mock import MagicMock

from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.core.exceptions import ServiceNotFoundError


class MockLLMService(LLMServiceBase):
    """Mock LLM service for testing."""

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs

    async def get_capabilities(self):
        pass

    async def estimate_tokens(self, text: str) -> int:
        return len(text) // 4

    async def _prepare_provider_options(self, prompt: str, **kwargs):
        return {"prompt": prompt}

    async def _call_provider_api(self, options):
        return {"response": "mock"}

    async def _stream_provider_api(self, options):
        yield "mock"

    async def _convert_provider_response(self, raw_response, options):
        from doc_ai_helper_backend.models.llm import LLMResponse, LLMUsage

        return LLMResponse(
            content="mock response",
            provider="mock",
            model="mock-model",
            usage=LLMUsage(prompt_tokens=1, completion_tokens=1, total_tokens=2),
        )


class TestLLMServiceFactory:
    """Test the LLM service factory."""

    def setup_method(self):
        """Setup for each test method."""
        # Clear the registry before each test
        LLMServiceFactory._services.clear()

    def teardown_method(self):
        """Cleanup after each test method."""
        # Clear the registry after each test
        LLMServiceFactory._services.clear()

    def test_register_service(self):
        """Test service registration."""
        # Register a mock service
        LLMServiceFactory.register("mock", MockLLMService)

        # Check that it's registered
        assert "mock" in LLMServiceFactory._services
        assert LLMServiceFactory._services["mock"] == MockLLMService

    def test_register_multiple_services(self):
        """Test registering multiple services."""

        class AnotherMockService(MockLLMService):
            pass

        LLMServiceFactory.register("mock1", MockLLMService)
        LLMServiceFactory.register("mock2", AnotherMockService)

        assert len(LLMServiceFactory._services) == 2
        assert LLMServiceFactory._services["mock1"] == MockLLMService
        assert LLMServiceFactory._services["mock2"] == AnotherMockService

    def test_register_override_service(self):
        """Test that registering a service with the same name overrides the previous one."""

        class NewMockService(MockLLMService):
            pass

        # Register initial service
        LLMServiceFactory.register("mock", MockLLMService)
        assert LLMServiceFactory._services["mock"] == MockLLMService

        # Override with new service
        LLMServiceFactory.register("mock", NewMockService)
        assert LLMServiceFactory._services["mock"] == NewMockService

    def test_create_service_success(self):
        """Test successful service creation."""
        LLMServiceFactory.register("mock", MockLLMService)

        # Create service instance
        service = LLMServiceFactory.create(
            "mock", api_key="test_key", model="test_model"
        )

        assert isinstance(service, MockLLMService)
        assert service.init_kwargs["api_key"] == "test_key"
        assert service.init_kwargs["model"] == "test_model"

    def test_create_service_not_found(self):
        """Test service creation with unregistered provider."""
        with pytest.raises(ServiceNotFoundError) as exc_info:
            LLMServiceFactory.create("nonexistent")

        assert "nonexistent" in str(exc_info.value)

    def test_create_service_with_no_args(self):
        """Test service creation with no additional arguments."""
        LLMServiceFactory.register("mock", MockLLMService)

        service = LLMServiceFactory.create("mock")

        assert isinstance(service, MockLLMService)
        assert service.init_kwargs == {}

    def test_create_service_with_kwargs(self):
        """Test service creation with keyword arguments."""
        LLMServiceFactory.register("mock", MockLLMService)

        kwargs = {
            "api_key": "secret_key",
            "base_url": "https://api.example.com",
            "timeout": 30,
            "max_retries": 3,
        }

        service = LLMServiceFactory.create("mock", **kwargs)

        assert isinstance(service, MockLLMService)
        for key, value in kwargs.items():
            assert service.init_kwargs[key] == value

    def test_get_available_providers(self):
        """Test getting list of available providers."""
        # Initially empty
        providers = LLMServiceFactory.get_available_providers()
        assert providers == []

        # Register services
        LLMServiceFactory.register("openai", MockLLMService)
        LLMServiceFactory.register("anthropic", MockLLMService)

        providers = LLMServiceFactory.get_available_providers()
        assert set(providers) == {"openai", "anthropic"}

    def test_provider_registration_workflow(self):
        """Test the complete provider registration workflow."""
        # Check initial state
        providers = LLMServiceFactory.get_available_providers()
        initial_count = len(providers)

        # Register service
        LLMServiceFactory.register("test_provider", MockLLMService)

        try:
            # Check registration
            providers = LLMServiceFactory.get_available_providers()
            assert len(providers) == initial_count + 1
            assert "test_provider" in providers

            # Create service
            service = LLMServiceFactory.create("test_provider")
            assert isinstance(service, MockLLMService)

        finally:
            # Cleanup
            if "test_provider" in LLMServiceFactory._services:
                del LLMServiceFactory._services["test_provider"]

    def test_registry_management(self):
        """Test registry management functionality."""
        # Record initial state
        initial_count = len(LLMServiceFactory.get_available_providers())

        # Add test providers
        LLMServiceFactory.register("mock1", MockLLMService)
        LLMServiceFactory.register("mock2", MockLLMService)

        try:
            # Check providers were added
            providers = LLMServiceFactory.get_available_providers()
            assert len(providers) == initial_count + 2
            assert "mock1" in providers
            assert "mock2" in providers

        finally:
            # Manual cleanup since clear_registry doesn't exist
            for provider in ["mock1", "mock2"]:
                if provider in LLMServiceFactory._services:
                    del LLMServiceFactory._services[provider]

    def test_service_creation_with_invalid_class(self):
        """Test service creation behavior with various classes."""

        class InvalidService:
            """Not a subclass of LLMServiceBase."""

            pass

        # Register the invalid service
        LLMServiceFactory.register("invalid", InvalidService)

        try:
            # Creation may succeed but the instance won't have required methods
            service = LLMServiceFactory.create("invalid")
            # The service won't have the required LLMServiceBase interface
            assert not hasattr(service, "query") or not hasattr(service, "stream_query")

        finally:
            # Cleanup
            if "invalid" in LLMServiceFactory._services:
                del LLMServiceFactory._services["invalid"]


class TestLLMServiceFactoryIntegration:
    """Integration tests for the factory with real service scenarios."""

    def setup_method(self):
        """Setup for each test method."""
        LLMServiceFactory._services.clear()

    def teardown_method(self):
        """Cleanup after each test method."""
        LLMServiceFactory._services.clear()

    def test_factory_workflow(self):
        """Test complete factory workflow."""
        # 1. Register multiple services
        LLMServiceFactory.register("service1", MockLLMService)
        LLMServiceFactory.register("service2", MockLLMService)

        # 2. Check availability
        providers = LLMServiceFactory.get_available_providers()
        assert len(providers) == 2

        # 3. Create instances
        service1 = LLMServiceFactory.create("service1", config="test1")
        service2 = LLMServiceFactory.create("service2", config="test2")

        assert service1.init_kwargs["config"] == "test1"
        assert service2.init_kwargs["config"] == "test2"

        # 4. Test service functionality
        assert len(providers) == 2
        assert "service1" in providers
        assert "service2" in providers

    def test_factory_with_service_inheritance(self):
        """Test factory with service inheritance hierarchy."""

        class BaseTestService(MockLLMService):
            service_type = "base"

        class ExtendedTestService(BaseTestService):
            service_type = "extended"

        LLMServiceFactory.register("base", BaseTestService)
        LLMServiceFactory.register("extended", ExtendedTestService)

        base_service = LLMServiceFactory.create("base")
        extended_service = LLMServiceFactory.create("extended")

        assert base_service.service_type == "base"
        assert extended_service.service_type == "extended"
        assert isinstance(extended_service, BaseTestService)  # Inheritance
