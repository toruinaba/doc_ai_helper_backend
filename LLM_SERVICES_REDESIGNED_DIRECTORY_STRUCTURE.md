# LLM Services Redesigned Directory Structure

## Overview

This document presents a comprehensive directory structure for the redesigned LLM services architecture, implementing a 4-layer pattern that reduces complexity from 35 files to approximately 12-15 main implementation files while maintaining full functionality and testability.

## Architecture Layers

1. **Core Layer**: Essential interfaces, exceptions, and models
2. **Domain Layer**: Business logic, orchestration, and workflows
3. **Provider Layer**: LLM provider implementations (OpenAI, Mock, etc.)
4. **Infrastructure Layer**: External integrations, caching, and utilities

## Complete Directory Structure

```
doc_ai_helper_backend/
├── services/
│   └── llm/
│       # === CORE LAYER (Foundation) ===
│       ├── __init__.py                                    # Main package exports
│       ├── core/
│       │   ├── __init__.py                               # Core layer exports
│       │   ├── interfaces.py                            # Abstract base classes & protocols
│       │   ├── exceptions.py                            # LLM-specific exceptions
│       │   ├── models.py                                # Core data models & types
│       │   └── constants.py                             # Constants & enums
│       │
│       # === DOMAIN LAYER (Business Logic) ===
│       ├── domain/
│       │   ├── __init__.py                               # Domain layer exports
│       │   ├── orchestrator.py                          # Main business logic orchestration
│       │   ├── conversation.py                          # Conversation management
│       │   ├── functions.py                             # Function calling & tools
│       │   └── streaming.py                             # Streaming response handling
│       │
│       # === PROVIDER LAYER (LLM Implementations) ===
│       ├── providers/
│       │   ├── __init__.py                               # Provider layer exports
│       │   ├── factory.py                               # Provider factory & registration
│       │   ├── openai.py                                # OpenAI provider implementation
│       │   └── mock.py                                  # Mock provider for testing
│       │
│       # === INFRASTRUCTURE LAYER (External Dependencies) ===
│       ├── infrastructure/
│       │   ├── __init__.py                               # Infrastructure layer exports
│       │   ├── cache.py                                 # Caching implementations
│       │   ├── templates.py                             # Template management
│       │   └── utils.py                                 # Utility functions
│       │
│       # === MIGRATION SUPPORT ===
│       ├── migration/
│       │   ├── __init__.py                               # Migration utilities
│       │   ├── compatibility.py                         # Backward compatibility layer
│       │   ├── adapter.py                               # Legacy API adapter
│       │   └── migration_guide.md                       # Migration documentation
│       │
│       # === CONFIGURATION & DATA ===
│       ├── config/
│       │   ├── __init__.py                               # Configuration exports
│       │   ├── settings.py                              # LLM-specific settings
│       │   └── templates/                               # Template files
│       │       ├── basic.json                           # Basic prompt template
│       │       ├── function_calling.json                # Function calling template
│       │       └── system_prompts.json                  # System prompts
│       │
│       # === TYPE DEFINITIONS ===
│       └── types/
│           ├── __init__.py                               # Type exports
│           ├── protocols.py                             # Protocol definitions
│           └── stubs.py                                 # Type stubs for external libraries
│
# === TEST STRUCTURE ===
tests/
├── unit/
│   └── services/
│       └── llm/
│           # === CORE LAYER TESTS ===
│           ├── core/
│           │   ├── __init__.py
│           │   ├── test_interfaces.py                   # Interface & protocol tests
│           │   ├── test_exceptions.py                   # Exception handling tests
│           │   ├── test_models.py                       # Model validation tests
│           │   └── test_constants.py                    # Constants & enum tests
│           │
│           # === DOMAIN LAYER TESTS ===
│           ├── domain/
│           │   ├── __init__.py
│           │   ├── test_orchestrator.py                 # Orchestration logic tests
│           │   ├── test_conversation.py                 # Conversation management tests
│           │   ├── test_functions.py                    # Function calling tests
│           │   └── test_streaming.py                    # Streaming response tests
│           │
│           # === PROVIDER LAYER TESTS ===
│           ├── providers/
│           │   ├── __init__.py
│           │   ├── test_factory.py                      # Factory & registration tests
│           │   ├── test_openai.py                       # OpenAI provider tests
│           │   └── test_mock.py                         # Mock provider tests
│           │
│           # === INFRASTRUCTURE LAYER TESTS ===
│           ├── infrastructure/
│           │   ├── __init__.py
│           │   ├── test_cache.py                        # Caching tests
│           │   ├── test_templates.py                    # Template management tests
│           │   └── test_utils.py                        # Utility function tests
│           │
│           # === MIGRATION TESTS ===
│           ├── migration/
│           │   ├── __init__.py
│           │   ├── test_compatibility.py                # Compatibility layer tests
│           │   └── test_adapter.py                      # Legacy adapter tests
│           │
│           # === CONFIGURATION TESTS ===
│           ├── config/
│           │   ├── __init__.py
│           │   └── test_settings.py                     # Settings validation tests
│           │
│           # === INTEGRATION TESTS ===
│           ├── test_integration.py                      # Cross-layer integration tests
│           ├── test_performance.py                      # Performance benchmark tests
│           └── test_end_to_end.py                       # Full workflow tests
│
├── integration/
│   └── services/
│       └── llm/
│           ├── __init__.py
│           ├── test_openai_integration.py               # Real OpenAI API tests
│           ├── test_streaming_integration.py            # Streaming integration tests
│           └── test_function_calling_integration.py     # Function calling integration tests
│
└── fixtures/
    └── llm/
        ├── __init__.py
        ├── responses/                                   # Sample API responses
        │   ├── openai_chat_completion.json
        │   ├── openai_function_call.json
        │   └── openai_streaming_chunks.json
        ├── templates/                                   # Test templates
        │   ├── test_basic.json
        │   └── test_function_calling.json
        └── conversations/                               # Test conversation data
            ├── basic_conversation.json
            └── function_calling_conversation.json
```

## File Size and Responsibility Breakdown

### Core Layer (4 files, ~400-600 LOC each)

#### `core/interfaces.py` (~500 LOC)
- Abstract base classes for all LLM providers
- Protocol definitions for typing
- Core interface contracts

#### `core/exceptions.py` (~200 LOC)
- LLM-specific exception hierarchy
- Error mapping utilities
- Exception context managers

#### `core/models.py` (~600 LOC)
- Pydantic models for requests/responses
- Message, function call, and tool definitions
- Validation schemas

#### `core/constants.py` (~150 LOC)
- Provider constants and enums
- Default configurations
- API constants

### Domain Layer (4 files, ~600-800 LOC each)

#### `domain/orchestrator.py` (~800 LOC)
- Main business logic coordination
- Request/response orchestration
- Cross-cutting concerns

#### `domain/conversation.py` (~600 LOC)
- Conversation state management
- Message history handling
- Context optimization

#### `domain/functions.py` (~700 LOC)
- Function calling logic
- Tool execution coordination
- Parameter validation

#### `domain/streaming.py` (~500 LOC)
- Streaming response handling
- Chunk processing and aggregation
- Real-time response management

### Provider Layer (3 files, ~800-1200 LOC each)

#### `providers/factory.py` (~400 LOC)
- Provider registration and instantiation
- Configuration management
- Dynamic provider loading

#### `providers/openai.py` (~1200 LOC)
- Complete OpenAI API integration
- Authentication and error handling
- Provider-specific optimizations

#### `providers/mock.py` (~800 LOC)
- Comprehensive mock implementation
- Test data generation
- Development utilities

### Infrastructure Layer (3 files, ~300-500 LOC each)

#### `infrastructure/cache.py` (~400 LOC)
- Response caching implementation
- Cache key generation
- TTL and invalidation logic

#### `infrastructure/templates.py` (~300 LOC)
- Template loading and management
- Dynamic template rendering
- Template validation

#### `infrastructure/utils.py` (~500 LOC)
- Common utility functions
- Helper methods
- Shared functionality

## Migration Strategy Files

### `migration/compatibility.py` (~600 LOC)
```python
"""
Backward compatibility layer for smooth migration.

This module provides:
- Legacy API wrappers
- Deprecation warnings
- Gradual migration utilities
"""

# Example structure:
class LegacyLLMServiceWrapper:
    """Wraps new architecture for legacy API compatibility."""
    
    def __init__(self, new_service):
        self._service = new_service
        self._warn_deprecated()
    
    def _warn_deprecated(self):
        warnings.warn(
            "Legacy LLM service API is deprecated. "
            "Please migrate to the new 4-layer architecture.",
            DeprecationWarning,
            stacklevel=2
        )
```

### `migration/adapter.py` (~400 LOC)
```python
"""
Adapter pattern implementation for legacy integration.

Provides seamless integration between old and new architectures
during the migration period.
"""

class LegacyAPIAdapter:
    """Adapts legacy API calls to new architecture."""
    
    def __init__(self, orchestrator):
        self._orchestrator = orchestrator
    
    async def legacy_query(self, prompt: str, **kwargs) -> dict:
        """Convert legacy query format to new architecture."""
        # Transform legacy parameters to new format
        request = self._transform_legacy_request(prompt, **kwargs)
        
        # Execute via new architecture
        response = await self._orchestrator.process_request(request)
        
        # Transform response back to legacy format
        return self._transform_legacy_response(response)
```

## Configuration Structure

### `config/settings.py` (~300 LOC)
```python
"""
LLM-specific configuration management.

Centralizes all LLM service configuration in one place.
"""

from pydantic import BaseSettings, Field
from typing import Dict, Any, Optional

class LLMSettings(BaseSettings):
    """LLM service configuration."""
    
    # Provider configurations
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    openai_base_url: str = Field("https://api.openai.com/v1", env="OPENAI_BASE_URL")
    
    # Caching settings
    cache_enabled: bool = Field(True, env="LLM_CACHE_ENABLED")
    cache_ttl: int = Field(3600, env="LLM_CACHE_TTL")  # 1 hour
    
    # Streaming settings
    streaming_chunk_size: int = Field(1024, env="LLM_STREAMING_CHUNK_SIZE")
    streaming_timeout: int = Field(30, env="LLM_STREAMING_TIMEOUT")
    
    # Function calling settings
    max_function_calls: int = Field(10, env="LLM_MAX_FUNCTION_CALLS")
    function_timeout: int = Field(60, env="LLM_FUNCTION_TIMEOUT")

    class Config:
        env_file = ".env"
        env_prefix = "LLM_"
```

## Implementation Strategy

### Phase 1: Core Foundation (Week 1)
1. Implement core layer (interfaces, exceptions, models, constants)
2. Create basic test structure
3. Set up type definitions and protocols

### Phase 2: Domain Logic (Week 2)
1. Implement orchestrator with basic functionality
2. Add conversation management
3. Implement function calling logic
4. Add streaming support

### Phase 3: Provider Implementation (Week 3)
1. Implement provider factory
2. Create OpenAI provider
3. Implement comprehensive mock provider
4. Add provider-specific optimizations

### Phase 4: Infrastructure & Migration (Week 4)
1. Implement caching layer
2. Add template management
3. Create compatibility layer
4. Implement migration adapters
5. Complete test coverage

## Benefits of This Structure

### Reduced Complexity
- **From 35 to 12 files**: 65% reduction in main implementation files
- **Clear layer boundaries**: Each layer has specific responsibilities
- **Focused testing**: Tests map directly to implementation structure

### Improved Maintainability
- **Single responsibility**: Each file has a clear, focused purpose
- **Dependency injection**: Clean separation of concerns
- **Testable architecture**: Easy to mock and test individual components

### Migration Safety
- **Backward compatibility**: Legacy API continues to work
- **Gradual migration**: Can migrate components incrementally
- **Deprecation warnings**: Clear guidance for developers

### Developer Experience
- **Intuitive structure**: Easy to navigate and understand
- **Comprehensive testing**: 90%+ test coverage maintained
- **Clear documentation**: Each layer and file is well-documented

## File Dependencies

### Layer Dependencies (Top to Bottom)
```
Infrastructure Layer
    ↓
Provider Layer
    ↓
Domain Layer
    ↓
Core Layer
```

### Specific File Dependencies
```
orchestrator.py → interfaces.py, models.py, exceptions.py
openai.py → interfaces.py, models.py, utils.py
factory.py → interfaces.py, openai.py, mock.py
cache.py → models.py, constants.py
```

## Testing Strategy

### Unit Test Coverage Goals
- **Core Layer**: 95% coverage (critical foundation)
- **Domain Layer**: 90% coverage (business logic)
- **Provider Layer**: 85% coverage (external dependencies)
- **Infrastructure Layer**: 80% coverage (utility functions)

### Integration Test Focus
- **Provider Integration**: Real API calls with live services
- **Streaming Integration**: End-to-end streaming workflows
- **Function Calling**: Complete tool execution cycles

### Performance Test Requirements
- **Response Time**: < 100ms for cached responses
- **Memory Usage**: < 50MB baseline memory footprint
- **Concurrent Requests**: Support 100+ concurrent requests

## Conclusion

This redesigned directory structure provides:

1. **Significant complexity reduction**: From 35 to 12 main files
2. **Clear architectural boundaries**: 4-layer separation of concerns
3. **Comprehensive testing**: Full test coverage maintained
4. **Smooth migration path**: Backward compatibility preserved
5. **Future extensibility**: Easy to add new providers or features

The structure balances simplicity with functionality, making it easier to maintain while preserving all existing capabilities and providing a clear path for future enhancements.