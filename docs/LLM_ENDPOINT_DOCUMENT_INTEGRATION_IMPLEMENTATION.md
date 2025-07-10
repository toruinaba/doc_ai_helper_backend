# LLM Endpoint Document Integration Implementation Guide

## Overview

This implementation guide details the development of automatic document integration functionality for `/llm/query` and `/llm/stream` endpoints. This feature enables users to interact with LLMs while referencing repository documents seamlessly.

## Background & Objectives

### Current Issues
1. **Unused document_content parameter**: Parameter is received but not actually utilized
2. **Partial repository_context usage**: Only basic information used, no automatic document content retrieval  
3. **Insufficient information sharing with MCP tools**: Document content not accessible to MCP tools

### Objectives
- Naturally integrate document content into LLM conversations
- Enable MCP tools to access document content
- Simple and efficient implementation (no session management)
- Maintain backward compatibility with existing APIs

## Design Principles

1. **Conversation History Based**: Inject document content into conversation history
2. **Simplicity First**: No complex session management
3. **Leverage Existing Features**: Maintain MCP's repository_context auto-injection
4. **Backward Compatibility**: Do not break existing APIs
5. **Opt-in Approach**: New features explicitly enabled

## Technical Specifications

### API Model Changes

#### LLMQueryRequest Extension

```python
# Modified file: doc_ai_helper_backend/models/llm.py

class LLMQueryRequest(BaseModel):
    # Existing fields (maintained)
    prompt: str = Field(..., description="The prompt to send to the LLM")
    conversation_history: Optional[List[MessageItem]] = Field(default=None)
    repository_context: Optional["RepositoryContext"] = Field(default=None)
    document_metadata: Optional["DocumentMetadata"] = Field(default=None)
    enable_tools: bool = Field(default=False)
    tool_choice: Optional[str] = Field(default="auto")
    provider: str = Field(default="openai")
    model: Optional[str] = Field(default=None)
    options: Dict[str, Any] = Field(default_factory=dict)
    disable_cache: bool = Field(default=False)
    
    # New addition
    auto_include_document: bool = Field(
        default=True,
        description="Whether to automatically fetch document content from repository_context and include in conversation history for initial requests"
    )
    
    # Deprecated (gradual removal)
    # document_content: Optional[str] - Not used, future removal
    # include_document_in_system_prompt: bool - Replaced by conversation history
    # system_prompt_template: str - Replaced by conversation history
```

### New Component Design

#### ConversationManager

```python
# New file: doc_ai_helper_backend/services/llm/conversation_manager.py

class ConversationManager:
    """Document integration management via conversation history"""
    
    MAX_DOCUMENT_LENGTH = 8000  # Token limit consideration
    
    def __init__(self, git_service_factory):
        self.git_service_factory = git_service_factory
    
    async def create_document_aware_conversation(
        self,
        repository_context: "RepositoryContext",
        initial_prompt: str,
        document_metadata: Optional["DocumentMetadata"] = None
    ) -> List[MessageItem]:
        """
        Generate conversation history including document content
        
        Returns:
            Conversation history in the following format:
            1. SYSTEM: Context information (repository, file info)
            2. ASSISTANT: Document content presentation
            3. USER: User's question
        """
    
    def is_initial_request(
        self, 
        conversation_history: Optional[List[MessageItem]],
        repository_context: Optional["RepositoryContext"]
    ) -> bool:
        """Determine if this is an initial request"""
    
    def _fetch_document_content(self, repository_context: "RepositoryContext") -> str:
        """Fetch document content using GitService"""
    
    def _create_fallback_conversation(
        self, 
        repository_context: "RepositoryContext", 
        initial_prompt: str, 
        error_message: str
    ) -> List[MessageItem]:
        """Create fallback conversation for error cases"""
```

## Implementation Plan

### Phase 1: Foundation Implementation (1-2 weeks)

#### 1.1 ConversationManager Implementation

**File**: `doc_ai_helper_backend/services/llm/conversation_manager.py`

**Implementation Requirements**:
- Document retrieval using Git Service Factory
- Token limit handling (8000 character truncation)
- Error handling (fallback for Git fetch failures)
- Proper logging
- Complete type annotations

**Implementation Details**:
```python
async def create_document_aware_conversation(
    self,
    repository_context: "RepositoryContext",
    initial_prompt: str,
    document_metadata: Optional["DocumentMetadata"] = None
) -> List[MessageItem]:
    """
    Processing flow:
    1. Generate system prompt (including repository info)
    2. Fetch document content via GitService
    3. Format and truncate document content
    4. Generate conversation history array
    5. Handle fallback processing for errors
    """
```

**Error Handling Requirements**:
- Git API call failures
- Authentication errors
- File not found
- Network errors
- Rate limit errors

#### 1.2 Dependency Injection Setup

**File**: `doc_ai_helper_backend/api/dependencies.py`

**Added Function**:
```python
def get_conversation_manager(
    git_service_factory = Depends(get_git_service_factory)
) -> ConversationManager:
    """ConversationManager dependency injection"""
    return ConversationManager(git_service_factory)
```

#### 1.3 Basic Test Implementation

**Test File**: `tests/unit/services/llm/test_conversation_manager.py`

**Test Cases**:
- Normal case: Generate conversation history with document content
- Error case: Fallback when Git fetch fails
- Boundary case: Truncation of large documents
- Logic test: Initial request determination

### Phase 2: Endpoint Integration (2-3 weeks)

#### 2.1 /llm/query Endpoint Modification

**File**: `doc_ai_helper_backend/api/endpoints/llm.py`

**Modification Strategy**:
1. Add new features via conditional branching (only when `auto_include_document=True`)
2. Do not change existing logic
3. Test and verify incrementally

**Implementation Location**:
```python
@router.post("/query", response_model=LLMResponse)
async def query_llm(
    request: LLMQueryRequest,
    llm_service: LLMServiceBase = Depends(get_llm_service),
    conversation_manager: ConversationManager = Depends(get_conversation_manager),
):
    # Add initial request determination and document integration processing
    # Maintain existing tool processing and normal query processing
```

**Processing Flow**:
1. Request validation
2. Initial request determination
3. Document integration (when applicable)
4. Continue with existing LLM processing
5. Return response

#### 2.2 /llm/stream Endpoint Modification

**File**: `doc_ai_helper_backend/api/endpoints/llm.py`

**Additional Requirements**:
- Document loading progress notifications
- Proper error handling in async processes
- Appropriate handling of streaming interruptions

**Streaming Events**:
```json
{"status": "document_loading", "message": "Loading document: README.md"}
{"status": "document_loaded", "message": "Document loaded successfully"}  
{"status": "tools_processing", "message": "Analyzing request..."}
{"text": "Actual response content"}
{"done": true}
```

#### 2.3 Integration Test Implementation

**Test Files**: 
- `tests/integration/api/test_llm_document_integration.py`
- `tests/integration/api/test_llm_streaming_document.py`

**Test Scenarios**:
1. Complete flow: Initial request → Continuation request
2. MCP tool integration behavior
3. Streaming functionality
4. Proper error responses
5. Large document processing

### Phase 3: Optimization & Cleanup (1-2 weeks)

#### 3.1 Existing Feature Cleanup

**File**: `doc_ai_helper_backend/services/llm/messaging/prompt_manager.py`

**Work Items**:
- Add warning logs for unused document_content
- Gradual deprecation notices for unnecessary parameters
- Documentation updates

#### 3.2 Documentation & Sample Updates

**Files to Create**:
- `docs/API_USAGE_EXAMPLES.md`
- `docs/DOCUMENT_INTEGRATION_GUIDE.md`
- Update `CLAUDE.md`

**Content**:
- New feature usage instructions
- Migration guide
- Best practices
- Troubleshooting

## MCP Integration

### Leveraging Existing MCP Integration

**Current Behavior**:
1. LLM endpoint receives `repository_context`
2. Set `repository_context` in MCP server
3. Automatically inject `repository_context` during Git tool execution

**Integration with New Features**:
1. Document content included in conversation history
2. LLM extracts document_content from conversation history during Function Call
3. MCP tools automatically receive document_content

**Behavior Example**:
```
Conversation History: [
  {"role": "assistant", "content": "Document content: # README\nThis is a sample..."},
  {"role": "user", "content": "Analyze this document"}
]

LLM-generated Function Call:
{
  "name": "analyze_document_structure",
  "arguments": {
    "document_content": "# README\nThis is a sample...",  // Extracted from conversation history
    "analysis_depth": "detailed"
  }
}
```

## Usage Examples

### Initial Request (Automatic Document Loading)

```json
POST /api/v1/llm/query
{
  "prompt": "Please summarize the main content of this document",
  "repository_context": {
    "service": "github",
    "owner": "microsoft", 
    "repo": "vscode",
    "current_path": "README.md",
    "ref": "main"
  },
  "auto_include_document": true,
  "enable_tools": true
}
```

### Continuation Request (Conversation Continuation)

```json
POST /api/v1/llm/query
{
  "prompt": "Please create an issue related to this document",
  "conversation_history": [
    {"role": "system", "content": "Document assistant..."},
    {"role": "assistant", "content": "README.md content: [document content]"},
    {"role": "user", "content": "Please summarize the main content of this document"},
    {"role": "assistant", "content": "This document is..."}
  ],
  "enable_tools": true
}
```

## Risk Management

### Risk Factors and Countermeasures

| Risk | Impact | Countermeasure |
|------|--------|----------------|
| Breaking existing APIs | High | Feature flags, maintain backward compatibility |
| Performance degradation | Medium | Incremental testing, truncation functionality |
| Git API limits | Medium | Rate limit handling, error handling |
| Large documents | Low | 8000 character limit, warning messages |

### Rollback Strategy

1. **Feature Flags**: Disable anytime with `auto_include_document=false`
2. **Gradual Disabling**: Disable specific features when issues occur
3. **Environment Variable Control**: Feature control via configuration files
4. **No Database Impact**: Safe changes to conversation history only

## Success Metrics

### Functional Metrics
- Initial document loading success rate > 95%
- Fallback behavior during errors 100%
- MCP tool integration normal operation rate > 95%

### Performance Metrics  
- Document loading time < 2 seconds
- Memory usage increase < 20%
- Impact on existing API response time < 10%

### Usability Metrics
- Document conversation success rate measurement
- Increased MCP tool usage frequency
- User feedback collection

## Implementation Checklist

### Phase 1: Foundation Implementation
- [ ] ConversationManager class implementation
- [ ] create_document_aware_conversation method
- [ ] is_initial_request method
- [ ] Error handling implementation
- [ ] Document truncation functionality
- [ ] LLMQueryRequest extension
- [ ] Dependency injection setup
- [ ] Basic unit test implementation

### Phase 2: Endpoint Integration
- [ ] /llm/query endpoint modification
- [ ] /llm/stream endpoint modification
- [ ] Streaming progress notifications
- [ ] Integration test implementation
- [ ] Performance testing
- [ ] Error case testing

### Phase 3: Optimization & Completion
- [ ] Existing feature cleanup
- [ ] Warning log addition
- [ ] Documentation creation
- [ ] Sample code creation
- [ ] E2E test implementation
- [ ] Production deployment preparation

## Important Notes

### Key Implementation Points

1. **Backward Compatibility**: Do not remove existing API parameters
2. **Error Handling**: Proper operation even when Git fetch fails
3. **Performance**: Appropriate handling of large documents
4. **Security**: Proper management of authentication information
5. **Logging**: Record information necessary for debugging

### Implementation Order Importance

- Each phase waits for completion of the previous phase
- Testing proceeds in parallel with implementation
- Integration testing conducted in each phase
- Production rollout implemented incrementally

### Quality Assurance

- All code includes complete type annotations
- Maintain test coverage above 90%
- Conduct code reviews
- Synchronize documentation updates

Follow this implementation guide to develop safe and efficient document integration functionality.