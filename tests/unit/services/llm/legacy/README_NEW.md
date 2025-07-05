# Legacy Test Files

This directory contains legacy test files that have been superseded by the new OptionA (1:1 correspondence) test structure.

## ⚠️ All tests in this directory are SKIPPED

All test files in this directory have `pytestmark = pytest.mark.skip()` to prevent them from running during normal test execution. They are preserved for historical reference only.

## Current Test Structure (OptionA - 1:1 Correspondence)

The current tests follow a 1:1 correspondence between source files and test files:

```
Source File                 → Test File
─────────────────────────────────────────────────
base.py                     → test_base.py
common.py                   → test_common.py  
factory.py                  → test_factory.py
mock_service.py             → test_mock_service.py
openai_service.py           → test_openai_service.py
utils/tokens.py             → utils/test_tokens.py
utils/caching.py            → utils/test_caching.py
utils/templating.py         → utils/test_templating.py
utils/messaging.py          → utils/test_messaging.py
utils/functions.py          → utils/test_functions.py
utils/helpers.py            → utils/test_helpers.py
```

## Legacy Files and Migration

| Legacy File | Functionality Moved To | Reason |
|-------------|------------------------|---------|
| `test_common_old.py` | `test_common.py` | Simplified to match actual `LLMServiceCommon` implementation |
| `test_llm_services.py` | `test_mock_service.py`, `test_factory.py` | Split into service-specific tests |
| `test_streaming.py` | `test_mock_service.py`, `test_openai_service.py` | Integrated into service-specific tests |
| `test_mock_service_isolation.py` | `test_mock_service.py` | Consolidated into main mock service tests |
| `test_complete_function_calling_flow.py` | `utils/test_functions.py` | Moved to composition-based implementation |
| `test_openai_service_legacy.py` | `test_openai_service.py` | Updated for composition-based architecture |

## Usage

These legacy tests are automatically skipped. To run only current tests:

```bash
# Run all current LLM tests (excluding legacy)
pytest tests/unit/services/llm/ --ignore=tests/unit/services/llm/legacy

# Run all current tests including legacy (will show skipped tests)
pytest tests/unit/services/llm/
```

## Migration Benefits

1. **Clear 1:1 Structure**: Each source file has a corresponding test file
2. **Reduced Duplication**: Eliminated overlapping test coverage
3. **Simplified Maintenance**: Tests are located where you'd expect them
4. **Better Organization**: utils tests are properly grouped
5. **Composition-Based**: Tests match the new composition-based architecture

For more details, see: `docs/LLM_OPTIONA_COMPLETION_REPORT.md`
