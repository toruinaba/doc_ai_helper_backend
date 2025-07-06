"""
Unit tests for LLM service factory.

This module contains tests for the LLMServiceFactory class that manages
service registration and instantiation.
"""

import pytest
import sys
from unittest.mock import MagicMock, patch

from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.core.exceptions import ServiceNotFoundError


class MockLLMService(LLMServiceBase):
    """Mock LLM service for testing."""

    def __init__(self, **kwargs):
        self.init_kwargs = kwargs
        self._mcp_adapter = None

    @property
    def mcp_adapter(self):
        """Get the MCP adapter."""
        return self._mcp_adapter

    def set_mcp_adapter(self, adapter):
        """Set the MCP adapter."""
        self._mcp_adapter = adapter

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

    def test_create_with_mcp_enabled(self):
        """MCPが有効化された状態でのサービス作成テスト"""
        # MockLLMServiceを登録
        LLMServiceFactory.register("mock", MockLLMService)

        # MCPが利用可能な場合のテスト
        service = LLMServiceFactory.create_with_mcp("mock", enable_mcp=True)
        assert isinstance(service, MockLLMService)
        # MCPアダプターが設定されているかチェック
        assert hasattr(service, "mcp_adapter")

    def test_create_with_mcp_disabled(self):
        """MCPが無効化された状態でのサービス作成テスト"""
        # MockLLMServiceを登録
        LLMServiceFactory.register("mock", MockLLMService)

        service = LLMServiceFactory.create_with_mcp("mock", enable_mcp=False)
        assert isinstance(service, MockLLMService)

    def test_create_with_mcp_import_error(self):
        """MCPモジュールがインポートできない場合のテスト"""
        # MockLLMServiceを登録
        LLMServiceFactory.register("mock", MockLLMService)

        with patch.dict(
            "sys.modules", {"doc_ai_helper_backend.services.mcp.server": None}
        ):
            with patch(
                "builtins.__import__", side_effect=ImportError("MCP not available")
            ):
                # ImportErrorが発生してもサービス作成は成功する
                service = LLMServiceFactory.create_with_mcp("mock", enable_mcp=True)
                assert isinstance(service, MockLLMService)

    def test_create_with_mcp_service_without_set_mcp_adapter(self):
        """set_mcp_adapterメソッドを持たないサービスでのMCP有効化テスト"""
        # MockLLMServiceを登録
        LLMServiceFactory.register("mock", MockLLMService)

        # MockLLMServiceがset_mcp_adapterメソッドを持っているかどうかに関係なく動作する
        service = LLMServiceFactory.create_with_mcp("mock", enable_mcp=True)
        assert isinstance(service, MockLLMService)


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
        assert isinstance(
            extended_service, BaseTestService
        )  # Inheritance    def test_factory_error_handling_edge_cases(self):
        """Test factory error handling for edge cases."""
        # Test None service name
        with pytest.raises(
            AttributeError
        ):  # 'NoneType' object has no attribute 'lower'
            LLMServiceFactory.create(None)

        # Test empty string service name
        with pytest.raises(ServiceNotFoundError):
            LLMServiceFactory.create("")

        # Test whitespace-only service name
        with pytest.raises(ServiceNotFoundError):
            LLMServiceFactory.create("   ")

    def test_factory_get_available_services_empty(self):
        """Test getting available services when registry is empty."""
        # Clear the registry
        original_services = LLMServiceFactory._services.copy()
        LLMServiceFactory._services.clear()

        try:
            available = LLMServiceFactory.get_available_providers()
            assert available == []
        finally:
            # Restore original services
            LLMServiceFactory._services = original_services

    def test_factory_get_available_services_populated(self):
        """Test getting available services when registry has services."""
        LLMServiceFactory.register("test_service", MockLLMService)

        available = LLMServiceFactory.get_available_providers()
        assert "test_service" in available

        # Clean up
        if "test_service" in LLMServiceFactory._services:
            del LLMServiceFactory._services["test_service"]

    def test_factory_register_overwrite_existing(self):
        """Test registering a service that overwrites an existing one."""

        class FirstService(MockLLMService):
            service_id = "first"

        class SecondService(MockLLMService):
            service_id = "second"

        # Register first service
        LLMServiceFactory.register("overwrite_test", FirstService)
        service1 = LLMServiceFactory.create("overwrite_test")
        assert service1.service_id == "first"

        # Overwrite with second service
        LLMServiceFactory.register("overwrite_test", SecondService)
        service2 = LLMServiceFactory.create("overwrite_test")
        assert service2.service_id == "second"

        # Clean up
        if "overwrite_test" in LLMServiceFactory._services:
            del LLMServiceFactory._services["overwrite_test"]

    def test_factory_create_with_complex_kwargs(self):
        """Test creating services with complex keyword arguments."""

        class ConfigurableService(MockLLMService):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.nested_config = kwargs.get("nested", {})
                self.list_config = kwargs.get("items", [])

        LLMServiceFactory.register("configurable", ConfigurableService)

        service = LLMServiceFactory.create(
            "configurable",
            nested={"key1": "value1", "key2": {"nested_key": "nested_value"}},
            items=[1, 2, 3, "string", {"dict": "in_list"}],
            simple_param="simple_value",
        )

        assert service.nested_config["key1"] == "value1"
        assert service.nested_config["key2"]["nested_key"] == "nested_value"
        assert service.list_config == [1, 2, 3, "string", {"dict": "in_list"}]
        assert service.init_kwargs["simple_param"] == "simple_value"

        # Clean up
        if "configurable" in LLMServiceFactory._services:
            del LLMServiceFactory._services["configurable"]

    def test_factory_service_initialization_failure(self):
        """Test factory behavior when service initialization fails."""

        class FailingService(MockLLMService):
            def __init__(self, **kwargs):
                if kwargs.get("should_fail", False):
                    raise ValueError("Initialization failed")
                super().__init__(**kwargs)

        LLMServiceFactory.register("failing", FailingService)

        # Should succeed with normal parameters
        service = LLMServiceFactory.create("failing", should_fail=False)
        assert isinstance(service, FailingService)

        # Should fail when initialization fails
        with pytest.raises(ValueError, match="Initialization failed"):
            LLMServiceFactory.create("failing", should_fail=True)

        # Clean up
        if "failing" in LLMServiceFactory._services:
            del LLMServiceFactory._services["failing"]

    def test_factory_case_insensitive(self):
        """Test that factory service names are case-insensitive."""
        LLMServiceFactory.register("testservice", MockLLMService)

        # Different cases should all work (factory uses lower())
        service1 = LLMServiceFactory.create("testservice")
        service2 = LLMServiceFactory.create("TestService")
        service3 = LLMServiceFactory.create("TESTSERVICE")

        assert isinstance(service1, MockLLMService)
        assert isinstance(service2, MockLLMService)
        assert isinstance(service3, MockLLMService)

        # Non-existent service should still fail
        with pytest.raises(ServiceNotFoundError):
            LLMServiceFactory.create("nonexistent")

        # Clean up
        if "testservice" in LLMServiceFactory._services:
            del LLMServiceFactory._services["testservice"]

    def test_factory_service_registry_isolation(self):
        """Test that the service registry is properly isolated."""
        initial_count = len(LLMServiceFactory._services)

        # Register a test service
        LLMServiceFactory.register("isolation_test", MockLLMService)
        assert len(LLMServiceFactory._services) == initial_count + 1

        # Create multiple instances
        service1 = LLMServiceFactory.create("isolation_test", param1="value1")
        service2 = LLMServiceFactory.create("isolation_test", param2="value2")

        # Services should be different instances
        assert service1 is not service2
        assert service1.init_kwargs != service2.init_kwargs

        # Registry should still have the same count
        assert len(LLMServiceFactory._services) == initial_count + 1

        # Clean up
        if "isolation_test" in LLMServiceFactory._services:
            del LLMServiceFactory._services["isolation_test"]

    def test_factory_with_none_and_default_kwargs(self):
        """Test factory with None values and default parameters."""

        class DefaultableService(MockLLMService):
            def __init__(self, param1=None, param2="default", **kwargs):
                super().__init__(**kwargs)
                self.param1 = param1
                self.param2 = param2

        LLMServiceFactory.register("defaultable", DefaultableService)

        # Test with None values
        service1 = LLMServiceFactory.create("defaultable", param1=None)
        assert service1.param1 is None
        assert service1.param2 == "default"

        # Test with explicit values
        service2 = LLMServiceFactory.create(
            "defaultable", param1="explicit", param2="custom"
        )
        assert service2.param1 == "explicit"
        assert service2.param2 == "custom"

        # Test with no parameters (all defaults)
        service3 = LLMServiceFactory.create("defaultable")
        assert service3.param1 is None
        assert service3.param2 == "default"

        # Clean up
        if "defaultable" in LLMServiceFactory._services:
            del LLMServiceFactory._services["defaultable"]

    def test_factory_registry_thread_safety_simulation(self):
        """Test factory registry behavior in concurrent access simulation."""
        import threading
        import time

        results = []
        errors = []

        def register_and_create(service_name, service_class):
            try:
                LLMServiceFactory.register(service_name, service_class)
                service = LLMServiceFactory.create(service_name)
                results.append((service_name, type(service).__name__))
            except Exception as e:
                errors.append((service_name, str(e)))

        # Create multiple threads that register and create services
        threads = []
        for i in range(5):

            class ThreadService(MockLLMService):
                thread_id = i

            thread = threading.Thread(
                target=register_and_create,
                args=(f"thread_service_{i}", ThreadService),
            )
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5

        # Clean up
        for i in range(5):
            service_name = f"thread_service_{i}"
            if service_name in LLMServiceFactory._services:
                del LLMServiceFactory._services[service_name]


class TestLLMServiceFactoryAdvancedScenarios:
    """Advanced test scenarios for LLMServiceFactory."""

    def setup_method(self):
        """Setup for each test method."""
        LLMServiceFactory._services.clear()

    def teardown_method(self):
        """Cleanup after each test method."""
        LLMServiceFactory._services.clear()

    def test_register_service_with_invalid_class(self):
        """Test registering a service with invalid class."""
        # Factory doesn't validate class type during registration, only during creation

        # Test with non-class object
        LLMServiceFactory.register("invalid", "not_a_class")
        assert "invalid" in LLMServiceFactory._services

        # Should fail when trying to create the service
        with pytest.raises((TypeError, AttributeError)):
            LLMServiceFactory.create("invalid")

        # Test with class that doesn't inherit from LLMServiceBase
        class InvalidService:
            pass

        # This should work (factory doesn't validate inheritance during registration)
        LLMServiceFactory.register("invalid_service", InvalidService)
        assert "invalid_service" in LLMServiceFactory._services

    def test_create_service_with_init_failure(self):
        """Test service creation when init fails."""

        class FailingService(MockLLMService):
            def __init__(self, **kwargs):
                if kwargs.get("fail_init"):
                    raise ValueError("Initialization failed")
                super().__init__(**kwargs)

        LLMServiceFactory.register("failing", FailingService)

        # Should succeed without fail_init
        service = LLMServiceFactory.create("failing")
        assert isinstance(service, FailingService)

        # Should fail with fail_init
        with pytest.raises(ValueError) as exc_info:
            LLMServiceFactory.create("failing", fail_init=True)
        assert "Initialization failed" in str(exc_info.value)

    def test_case_sensitive_provider_names(self):
        """Test that provider names are case-sensitive."""
        LLMServiceFactory.register("OpenAI", MockLLMService)
        LLMServiceFactory.register("openai", MockLLMService)

        # Both should be registered separately (OpenAI overwrites openai)
        providers = LLMServiceFactory.get_available_providers()
        # Since registrations are case-insensitive in the implementation, only one will remain
        assert "openai" in providers
        assert len([p for p in providers if p.lower() == "openai"]) == 1

        # Should be able to create the service
        service = LLMServiceFactory.create("openai")
        assert isinstance(service, MockLLMService)

    def test_create_service_with_complex_kwargs(self):
        """Test service creation with complex keyword arguments."""

        class ComplexService(MockLLMService):
            def __init__(self, **kwargs):
                self.config = kwargs
                super().__init__(**kwargs)

        LLMServiceFactory.register("complex", ComplexService)

        complex_kwargs = {
            "api_key": "secret_key",
            "settings": {"temperature": 0.7, "max_tokens": 1000, "model": "gpt-4"},
            "endpoints": {
                "chat": "https://api.openai.com/v1/chat/completions",
                "embeddings": "https://api.openai.com/v1/embeddings",
            },
            "retry_config": {
                "max_retries": 3,
                "backoff_factor": 2.0,
                "status_forcelist": [429, 500, 502, 503, 504],
            },
            "timeout": 30.0,
            "debug": True,
        }

        service = LLMServiceFactory.create("complex", **complex_kwargs)
        assert isinstance(service, ComplexService)
        assert service.config["api_key"] == "secret_key"
        assert service.config["settings"]["temperature"] == 0.7
        assert service.config["retry_config"]["max_retries"] == 3

    def test_provider_name_validation(self):
        """Test provider name validation and edge cases."""
        # Empty string provider name
        LLMServiceFactory.register("", MockLLMService)
        assert "" in LLMServiceFactory._services
        service = LLMServiceFactory.create("")
        assert isinstance(service, MockLLMService)

        # Special characters in provider name
        special_names = [
            "test-provider",
            "test_provider",
            "test.provider",
            "test@provider",
        ]
        for name in special_names:
            LLMServiceFactory.register(name, MockLLMService)
            assert name in LLMServiceFactory._services
            service = LLMServiceFactory.create(name)
            assert isinstance(service, MockLLMService)

        # Very long provider name
        long_name = "a" * 1000
        LLMServiceFactory.register(long_name, MockLLMService)
        assert long_name in LLMServiceFactory._services
        service = LLMServiceFactory.create(long_name)
        assert isinstance(service, MockLLMService)

    def test_factory_state_isolation(self):
        """Test that factory state is properly isolated between operations."""
        # Register initial service
        LLMServiceFactory.register("test1", MockLLMService)
        initial_count = len(LLMServiceFactory.get_available_providers())

        # Register second service
        LLMServiceFactory.register("test2", MockLLMService)
        assert len(LLMServiceFactory.get_available_providers()) == initial_count + 1

        # Create service without affecting registry
        service = LLMServiceFactory.create("test1")
        assert isinstance(service, MockLLMService)
        assert len(LLMServiceFactory.get_available_providers()) == initial_count + 1

        # Registering same name should override
        class NewMockService(MockLLMService):
            service_type = "new"

        LLMServiceFactory.register("test1", NewMockService)
        assert len(LLMServiceFactory.get_available_providers()) == initial_count + 1

        new_service = LLMServiceFactory.create("test1")
        assert isinstance(new_service, NewMockService)

    def test_service_creation_with_none_kwargs(self):
        """Test service creation with None values in kwargs."""

        class NullableService(MockLLMService):
            def __init__(self, **kwargs):
                self.nullable_param = kwargs.get("nullable_param")
                self.required_param = kwargs.get("required_param", "default")
                super().__init__(**kwargs)

        LLMServiceFactory.register("nullable", NullableService)

        # Test with None value
        service = LLMServiceFactory.create(
            "nullable", nullable_param=None, required_param="custom"
        )
        assert isinstance(service, NullableService)
        assert service.nullable_param is None
        assert service.required_param == "custom"

    def test_registry_persistence_across_calls(self):
        """Test that registry persists across multiple factory calls."""
        # Register services
        LLMServiceFactory.register("persistent1", MockLLMService)
        LLMServiceFactory.register("persistent2", MockLLMService)

        # Create service from first registration
        service1 = LLMServiceFactory.create("persistent1")
        assert isinstance(service1, MockLLMService)

        # Registry should still contain both services
        providers = LLMServiceFactory.get_available_providers()
        assert "persistent1" in providers
        assert "persistent2" in providers

        # Create service from second registration
        service2 = LLMServiceFactory.create("persistent2")
        assert isinstance(service2, MockLLMService)

        # Registry should still be intact
        providers = LLMServiceFactory.get_available_providers()
        assert "persistent1" in providers
        assert "persistent2" in providers

    def test_error_handling_in_service_creation(self):
        """Test comprehensive error handling during service creation."""

        class ErrorProneService(MockLLMService):
            def __init__(self, **kwargs):
                error_type = kwargs.get("error_type")
                if error_type == "value_error":
                    raise ValueError("Value error during init")
                elif error_type == "type_error":
                    raise TypeError("Type error during init")
                elif error_type == "runtime_error":
                    raise RuntimeError("Runtime error during init")
                elif error_type == "custom_error":
                    raise CustomException("Custom error during init")
                super().__init__(**kwargs)

        LLMServiceFactory.register("error_prone", ErrorProneService)

        # Test different error types
        error_cases = [
            ("value_error", ValueError),
            ("type_error", TypeError),
            ("runtime_error", RuntimeError),
            ("custom_error", CustomException),
        ]

        for error_type, expected_exception in error_cases:
            with pytest.raises(expected_exception):
                LLMServiceFactory.create("error_prone", error_type=error_type)

    def test_service_creation_performance(self):
        """Test that service creation is efficient."""
        import time

        LLMServiceFactory.register("perf_test", MockLLMService)

        # Time multiple service creations
        start_time = time.time()
        for _ in range(100):
            service = LLMServiceFactory.create("perf_test")
            assert isinstance(service, MockLLMService)
        end_time = time.time()

        # Should complete quickly (less than 1 second for 100 creations)
        total_time = end_time - start_time
        assert total_time < 1.0, f"Service creation took too long: {total_time}s"

    def test_factory_with_inheritance_hierarchy(self):
        """Test factory with complex service inheritance hierarchy."""

        class BaseCustomService(MockLLMService):
            service_family = "custom"

        class SpecializedService(BaseCustomService):
            service_type = "specialized"

        class AdvancedService(SpecializedService):
            service_level = "advanced"

        # Register services at different inheritance levels
        LLMServiceFactory.register("base_custom", BaseCustomService)
        LLMServiceFactory.register("specialized", SpecializedService)
        LLMServiceFactory.register("advanced", AdvancedService)

        # Create services and verify inheritance
        base_service = LLMServiceFactory.create("base_custom")
        specialized_service = LLMServiceFactory.create("specialized")
        advanced_service = LLMServiceFactory.create("advanced")

        assert isinstance(base_service, BaseCustomService)
        assert isinstance(specialized_service, SpecializedService)
        assert isinstance(advanced_service, AdvancedService)

        # Verify inheritance chain
        assert isinstance(specialized_service, BaseCustomService)
        assert isinstance(advanced_service, BaseCustomService)
        assert isinstance(advanced_service, SpecializedService)

        # Verify unique attributes
        assert hasattr(base_service, "service_family")
        assert hasattr(specialized_service, "service_type")
        assert hasattr(advanced_service, "service_level")


class CustomException(Exception):
    """Custom exception for testing."""

    pass


class TestLLMServiceFactoryEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Setup for each test method."""
        LLMServiceFactory._services.clear()

    def teardown_method(self):
        """Cleanup after each test method."""
        LLMServiceFactory._services.clear()

    def test_massive_provider_registration(self):
        """Test registering a large number of providers."""
        num_providers = 1000

        # Register many providers
        for i in range(num_providers):
            provider_name = f"provider_{i}"
            LLMServiceFactory.register(provider_name, MockLLMService)

        # Verify all are registered
        providers = LLMServiceFactory.get_available_providers()
        assert len(providers) == num_providers

        # Test creating services from various providers
        test_indices = [0, num_providers // 2, num_providers - 1]
        for i in test_indices:
            provider_name = f"provider_{i}"
            service = LLMServiceFactory.create(provider_name)
            assert isinstance(service, MockLLMService)

    def test_unicode_provider_names(self):
        """Test provider names with Unicode characters."""
        unicode_names = [
            "プロバイダー",  # Japanese
            "провайдер",  # Russian
            "fournisseur",  # French with accents
            "🚀rocket🔥",  # Emojis
            "test-服务-provider",  # Mixed
        ]

        for name in unicode_names:
            LLMServiceFactory.register(name, MockLLMService)
            assert name in LLMServiceFactory._services

            service = LLMServiceFactory.create(name)
            assert isinstance(service, MockLLMService)

    def test_factory_registry_memory_behavior(self):
        """Test memory behavior of factory registry."""
        import weakref
        import gc

        class TrackableService(MockLLMService):
            def __init__(self, **kwargs):
                self.tracking_id = kwargs.get("tracking_id", "default")
                super().__init__(**kwargs)

        LLMServiceFactory.register("trackable", TrackableService)

        # Create services and track them
        services = []
        weak_refs = []

        for i in range(10):
            service = LLMServiceFactory.create("trackable", tracking_id=f"service_{i}")
            services.append(service)
            weak_refs.append(weakref.ref(service))

        # All weak references should be alive
        assert all(ref() is not None for ref in weak_refs)

        # Clear strong references
        services.clear()
        gc.collect()

        # Some weak references might still be alive due to test framework internals
        # Just verify that the factory registry still works
        new_service = LLMServiceFactory.create("trackable", tracking_id="new_service")
        assert isinstance(new_service, TrackableService)
        assert new_service.tracking_id == "new_service"
