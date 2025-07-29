"""
LLM service factory.

このモジュールはLLMサービスインスタンスを作成するためのファクトリーを提供します。
オーケストレータとの統合により、キャッシュサービスも含めて
完全に構成されたLLMサービスを提供します。
"""

from typing import Dict, Type, Optional

from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.core.exceptions import ServiceNotFoundError


class LLMServiceFactory:
    """
    Factory for creating LLM service instances.

    This factory maintains a registry of available LLM services and provides
    methods to create instances of these services.
    """

    # Registry of available LLM services
    _services: Dict[str, Type[LLMServiceBase]] = {}

    @classmethod
    def register(cls, provider_name: str, service_class: Type[LLMServiceBase]) -> None:
        """
        Register an LLM service implementation.

        Args:
            provider_name: The name of the LLM provider
            service_class: The service class for the provider
        """
        cls._services[provider_name.lower()] = service_class

    @classmethod
    def create(cls, provider: str, **config) -> LLMServiceBase:
        """
        Create an LLM service instance.

        Args:
            provider: The name of the LLM provider
            **config: Configuration options for the service

        Returns:
            LLMServiceBase: An instance of the requested LLM service

        Raises:
            ServiceNotFoundError: If the requested provider is not registered
        """
        provider = provider.lower()
        if provider not in cls._services:
            available_providers = list(cls._services.keys())
            raise ServiceNotFoundError(
                f"LLM provider '{provider}' not found. Available providers: {available_providers}"
            )

        service_class = cls._services[provider]
        return service_class(**config)

    @classmethod
    def create_with_orchestrator(
        cls, provider: str, cache_service=None, enable_mcp: bool = True, **config
    ) -> tuple[LLMServiceBase, 'LLMOrchestrator']:
        """
        オーケストレータと共にLLMサービスインスタンスを作成
        
        Args:
            provider: LLMプロバイダーの名前
            cache_service: キャッシュサービス（指定されない場合はデフォルトを使用）
            enable_mcp: FastMCP統合を有効にするか
            **config: サービスの設定オプション

        Returns:
            tuple: (LLMサービスインスタンス, LLMオーケストレータ)

        Raises:
            ServiceNotFoundError: 要求されたプロバイダーが登録されていない場合
        """
        # LLMサービス作成
        service = cls.create(provider, **config)

        # MCP統合
        if enable_mcp:
            try:
                from doc_ai_helper_backend.services.mcp.server import mcp_server
                if hasattr(service, "set_mcp_server"):
                    service.set_mcp_server(mcp_server)
            except ImportError:
                pass

        # キャッシュサービスの取得またはデフォルト作成
        if cache_service is None:
            try:
                from doc_ai_helper_backend.services.llm.caching import MemoryLLMCache
                cache_service = MemoryLLMCache()
            except ImportError:
                # キャッシュサービスが利用できない場合、簡単なメモリキャッシュを使用
                cache_service = {}

        # オーケストレータ作成
        from doc_ai_helper_backend.services.llm.orchestrator import LLMOrchestrator
        orchestrator = LLMOrchestrator(cache_service)

        return service, orchestrator

    @classmethod
    def create_with_mcp(
        cls, provider: str, enable_mcp: bool = True, **config
    ) -> LLMServiceBase:
        """
        FastMCP統合でLLMサービスインスタンスを作成（後方互換性のため）

        Args:
            provider: LLMプロバイダーの名前
            enable_mcp: FastMCP統合を有効にするか
            **config: サービスの設定オプション

        Returns:
            LLMServiceBase: FastMCP統合付きの要求されたLLMサービスのインスタンス

        Raises:
            ServiceNotFoundError: 要求されたプロバイダーが登録されていない場合
        """
        service = cls.create(provider, **config)

        if enable_mcp:
            try:
                from doc_ai_helper_backend.services.mcp.server import mcp_server
                if hasattr(service, "set_mcp_server"):
                    service.set_mcp_server(mcp_server)
            except ImportError:
                pass

        return service

    @classmethod
    def get_available_providers(cls) -> list[str]:
        """
        Get a list of available LLM providers.

        Returns:
            list[str]: List of registered provider names
        """
        return list(cls._services.keys())


# デフォルトLLMサービスの登録
def _register_default_services():
    """デフォルトLLMサービス実装を登録"""
    try:
        from doc_ai_helper_backend.services.llm.providers.openai_service import OpenAIService
        LLMServiceFactory.register("openai", OpenAIService)
    except ImportError:
        pass

    try:
        from doc_ai_helper_backend.services.llm.providers.mock_service import MockLLMService
        LLMServiceFactory.register("mock", MockLLMService)
    except ImportError:
        pass


# Register services when module is imported
_register_default_services()
