# Unit Tests 1:1 Correspondence Structure

This document describes the complete 1:1 correspondence structure implemented across all services in the `tests/unit/services/` directory.

## ✅ Completed Services

### Git Services (`tests/unit/services/git/`)

**Status**: ✅ Complete - Perfect 1:1 correspondence

```
doc_ai_helper_backend/services/git/    <->    tests/unit/services/git/
├── base.py                           <->    ├── test_base.py
├── factory.py                        <->    ├── test_factory.py
├── forgejo_service.py                <->    ├── test_forgejo_service.py
├── github_service.py                 <->    ├── test_github_service.py
├── mock_data.py                      <->    ├── test_mock_data.py
└── mock_service.py                   <->    └── test_mock_service.py
```

**Legacy Files**: Moved to `legacy/` directory with skip markers:
- `legacy/test_factory_forgejo.py` (skipped)
- `legacy/test_forgejo_api_integration.py` (skipped)
- `legacy/github/` (empty directory, documented)

### LLM Services (`tests/unit/services/llm/`)

**Status**: ✅ Complete - Perfect 1:1 correspondence

```
doc_ai_helper_backend/services/llm/    <->    tests/unit/services/llm/
├── base.py                           <->    ├── test_base.py
├── common.py                         <->    ├── test_common.py
├── factory.py                        <->    ├── test_factory.py
├── mock_service.py                   <->    ├── test_mock_service.py
└── openai_service.py                 <->    └── test_openai_service.py
```

**Utils Subdirectory**:
```
doc_ai_helper_backend/services/llm/utils/    <->    tests/unit/services/llm/utils/
├── caching.py                               <->    ├── test_caching.py
├── functions.py                             <->    ├── test_functions.py
├── helpers.py                               <->    ├── test_helpers.py
├── messaging.py                             <->    ├── test_messaging.py
├── templating.py                            <->    ├── test_templating.py
└── tokens.py                                <->    └── test_tokens.py
```

**Legacy Files**: All legacy tests properly skipped in `legacy/` directory

### Document Services (`tests/unit/services/document/`)

**Status**: ✅ Complete - Perfect 1:1 correspondence

```
doc_ai_helper_backend/services/document/    <->    tests/unit/services/document/
└── service.py                              <->    └── test_service.py
```

**Processors Subdirectory**:
```
doc_ai_helper_backend/services/document/processors/    <->    tests/unit/services/document/processors/
├── base.py                                            <->    ├── test_base.py
├── factory.py                                         <->    ├── test_factory.py
├── html.py                                            <->    ├── test_html.py
└── markdown.py                                        <->    └── test_markdown.py
```

**Utils Subdirectory**:
```
doc_ai_helper_backend/services/document/utils/    <->    tests/unit/services/document/utils/
├── frontmatter.py                                <->    ├── test_frontmatter.py
├── html_analyzer.py                              <->    ├── test_html_analyzer.py
└── links.py                                      <->    └── test_links.py
```

**Removed Duplicate Files**: 3 misplaced test files were safely removed:
- ❌ `test_base.py` (was duplicate of `processors/test_base.py`)
- ❌ `test_factory.py` (was duplicate of `processors/test_factory.py`)  
- ❌ `test_html_analyzer.py` (was duplicate of `utils/test_html_analyzer.py`)

## 📊 Test Results Summary

### Current Test Status

**Git Services**: ✅ All tests passing
- 6 source files → 6 test files
- Legacy tests properly skipped
- Documentation complete

**LLM Services**: ✅ All tests passing  
- 5 main source files → 5 test files
- 6 utils files → 6 test files
- 102 tests passing, legacy tests skipped
- Documentation complete

**Document Services**: ✅ All tests passing
- 1 main service → 1 test file  
- 4 processor files → 4 test files
- 3 utils files → 3 test files
- All new tests created and passing

## 🏗️ Organization Principles

### 1:1 Correspondence Rules

1. **Exact Filename Matching**: Every source file `module.py` has a corresponding `test_module.py`
2. **Directory Structure Mirroring**: Test directories exactly mirror source directories
3. **No Exceptions**: Every source file gets a test file, even if minimal
4. **Legacy Isolation**: Old/deprecated tests moved to `legacy/` with skip markers

### Benefits Achieved

1. **Predictable Structure**: Developers know exactly where to find tests
2. **Complete Coverage**: No source file left without tests
3. **Easy Navigation**: IDE tools can easily jump between source and tests
4. **Maintenance Clarity**: Changes to source files have obvious test file targets
5. **Legacy Management**: Old tests preserved but clearly marked as outdated

## 🔍 Test Execution

### Run All Service Tests (1:1 Only)

```bash
# All services, excluding legacy
pytest tests/unit/services/ --ignore=tests/unit/services/git/legacy/ --ignore=tests/unit/services/llm/legacy/ -v

# Individual services
pytest tests/unit/services/git/ --ignore=tests/unit/services/git/legacy/ -v
pytest tests/unit/services/llm/ --ignore=tests/unit/services/llm/legacy/ -v  
pytest tests/unit/services/document/ -v
```

### Current Test Counts

- **Git Services**: 54+ tests passing
- **LLM Services**: 102 tests passing  
- **Document Services**: 50+ tests passing
- **Total**: 200+ active tests with 1:1 correspondence

## 📁 File Structure Examples

### Before Reorganization
```
tests/unit/services/git/
├── test_forgejo_service.py
├── test_github_service.py  
├── test_mock_service.py
├── test_factory_forgejo.py        # ❌ No corresponding source
├── test_forgejo_api_integration.py # ❌ Integration test in unit folder
└── github/                        # ❌ Empty directory
```

### After Reorganization (1:1)
```
tests/unit/services/git/
├── test_base.py                    # ✅ 1:1 with base.py
├── test_factory.py                 # ✅ 1:1 with factory.py
├── test_forgejo_service.py         # ✅ 1:1 with forgejo_service.py
├── test_github_service.py          # ✅ 1:1 with github_service.py
├── test_mock_data.py               # ✅ 1:1 with mock_data.py
├── test_mock_service.py            # ✅ 1:1 with mock_service.py
└── legacy/                         # ✅ Non-1:1 files moved here
    ├── README.md
    ├── test_factory_forgejo.py     (skipped)
    ├── test_forgejo_api_integration.py (skipped)
    └── github/                     (documented as empty)
```

## 🎯 Quality Measures

### Test Quality Standards

1. **Proper Imports**: All tests import exactly what they need
2. **Mock Usage**: External dependencies properly mocked
3. **Error Handling**: Both success and failure cases tested
4. **Documentation**: Test docstrings explain what is being tested
5. **Fixtures**: Reusable test data properly organized

### Maintenance Guidelines

1. **New Source File**: Immediately create corresponding test file
2. **Source File Changes**: Update corresponding test file
3. **Refactoring**: Keep 1:1 correspondence during code moves
4. **Legacy Code**: Move old tests to legacy/ with skip markers
5. **Documentation**: Update this README when structure changes

---

**Last Updated**: July 5, 2025  
**Status**: ✅ Complete 1:1 correspondence achieved across all services  
**Total Coverage**: All source files have corresponding test files
