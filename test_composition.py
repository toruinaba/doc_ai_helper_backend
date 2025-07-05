#!/usr/bin/env python3
"""Test script for the new composition-based OpenAI service."""

import asyncio
import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


async def test_composition_service():
    """Test the new composition-based OpenAI service."""
    try:
        # Direct import to avoid circular import issues
        from doc_ai_helper_backend.services.llm.openai_service import OpenAIService

        print("🧪 Testing New Composition-Based OpenAI Service...")

        # Create service instance
        service = OpenAIService(api_key="test-key", default_model="gpt-3.5-turbo")
        print(f"✓ Created OpenAI service: {type(service).__name__}")

        # Check composition pattern
        print(f"✓ Has _common attribute: {hasattr(service, '_common')}")
        print(f"✓ Has cache_service property: {hasattr(service, 'cache_service')}")
        print(
            f"✓ Has template_manager property: {hasattr(service, 'template_manager')}"
        )
        print(
            f"✓ Has function_handler property: {hasattr(service, 'function_handler')}"
        )

        # Test backward compatibility properties
        print(f"✓ cache_service type: {type(service.cache_service).__name__}")
        print(f"✓ template_manager type: {type(service.template_manager).__name__}")
        print(f"✓ function_handler type: {type(service.function_handler).__name__}")

        # Test capabilities
        capabilities = await service.get_capabilities()
        print(f"✓ Got capabilities: {capabilities['provider']}")

        # Test token estimation
        tokens = await service.estimate_tokens("Hello, world!")
        print(f"✓ Token estimation: {tokens} tokens")

        print("\n✅ All composition-based service tests passed!")
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(test_composition_service())
    sys.exit(0 if success else 1)
