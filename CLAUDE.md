# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**doc_ai_helper_backend** is a FastAPI-based backend service that provides document retrieval and processing capabilities from Git repositories, with integrated LLM functionality and MCP (Model Context Protocol) support. The project follows a staged implementation approach:

- **Phase 1 (Complete)**: Markdown document processing with frontmatter parsing, link transformation, and metadata extraction
- **Phase 2 (Complete)**: LLM integration (OpenAI), streaming responses, MCP server, and Git service abstraction (GitHub, Forgejo)
- **Phase 3 (Planned)**: HTML processing, repository management, and search functionality

## Common Development Commands

### Development Server
```bash
# Start development server with hot reload
uvicorn doc_ai_helper_backend.main:app --reload --host 0.0.0.0 --port 8000

# Start with debug logging
uvicorn doc_ai_helper_backend.main:app --reload --log-level debug
```

### Testing
```bash
# Run all unit tests (recommended for daily development)
pytest tests/unit/ -v

# Run tests with coverage
pytest tests/unit/ --cov=doc_ai_helper_backend --cov-report=html

# Run integration tests (requires API keys)
pytest tests/integration/ -v

# Run specific test modules
pytest tests/unit/services/llm/ -v
pytest tests/unit/api/ -v
pytest tests/unit/services/document/ -v

# Run MCP-related tests
pytest -m mcp -v

# Run streaming functionality tests
pytest -m streaming -v
```

### Code Quality
```bash
# Format code with Black
black doc_ai_helper_backend/

# Sort imports
isort doc_ai_helper_backend/

# Type checking
mypy doc_ai_helper_backend/

# Lint code
flake8 doc_ai_helper_backend/
```

## Architecture Overview

### High-Level Structure
```
FastAPI Application
├── API Layer (api/)              # HTTP endpoints and routing
├── Service Layer (services/)     # Business logic and orchestration
├── Model Layer (models/)         # Data structures and validation
└── Core Layer (core/)           # Configuration and utilities
```

### Key Service Abstractions

#### Git Services (`services/git/`)
- **GitServiceBase**: Abstract interface for Git providers
- **GitHubService**: GitHub API integration
- **ForgejoService**: Forgejo API integration  
- **MockGitService**: Testing and development mock
- **GitServiceFactory**: Provider selection and instantiation

#### LLM Services (`services/llm/`)
- **LLMServiceBase**: Abstract interface for LLM providers
- **OpenAIService**: OpenAI API integration with streaming support
- **MockLLMService**: Testing mock
- **LLMServiceFactory**: Provider selection
- **Function Manager**: Tool execution coordination for MCP

#### Document Processing (`services/document/`)
- **DocumentService**: Orchestrates document retrieval and processing
- **MarkdownProcessor**: Markdown-specific processing
- **HTMLProcessor**: HTML processing (planned)
- **LinkTransformer**: Link analysis and transformation
- **FrontmatterParser**: YAML/JSON frontmatter extraction

#### MCP Integration (`services/mcp/`)
- **MCPServer**: FastMCP server implementation
- **Tools**: Individual tool implementations (document, feedback, analysis, git)
- **FunctionAdapter**: Tool execution and response formatting

### Data Models (`models/`)
- **DocumentResponse**: Complete document with metadata and links
- **RepositoryStructure**: Repository file structure
- **LinkInfo**: Link extraction and transformation data
- **LLMQueryRequest/Response**: LLM interaction models
- **Frontmatter**: Parsed frontmatter data structures

## Key Implementation Patterns

### Factory Pattern
Used extensively for provider abstraction:
```python
# Git service creation
git_service = GitServiceFactory.create("github", access_token=token)

# LLM service creation  
llm_service = LLMServiceFactory.create("openai", api_key=key)
```

### Dependency Injection
FastAPI dependency system for service injection:
```python
@router.get("/documents/contents/{service}/{owner}/{repo}/{path:path}")
async def get_document(
    # ... path parameters ...
    document_service: DocumentService = Depends(get_document_service),
):
```

### Async/Await Pattern
All I/O operations use asyncio:
```python
async def get_file_content(self, owner: str, repo: str, path: str) -> str:
    async with httpx.AsyncClient() as client:
        response = await client.get(url)
        return response.text
```

### Error Handling
Custom exceptions with HTTP status mapping:
```python
try:
    content = await git_service.get_file_content(owner, repo, path)
except GitServiceException as e:
    raise HTTPException(status_code=404, detail=str(e))
```

## Important Implementation Details

### Document Processing Pipeline
1. **Git Service** retrieves raw file content
2. **Document Processor** (Markdown/HTML) processes content
3. **Frontmatter Parser** extracts metadata
4. **Link Transformer** converts relative links to absolute
5. **Response Builder** creates final DocumentResponse

### LLM Integration Flow
1. **Request Validation** via Pydantic models
2. **Provider Selection** via LLMServiceFactory
3. **Context Preparation** with MCP adapter
4. **Tool Registration** for function calling
5. **Streaming Response** via SSE (Server-Sent Events)
6. **Caching** for performance optimization

### MCP Tool Execution
1. **Function Registration** in tool registry
2. **Parameter Validation** against tool schemas
3. **Tool Execution** with error handling
4. **Result Formatting** for LLM consumption

## Configuration and Environment

### Required Environment Variables
```bash
# LLM Integration
OPENAI_API_KEY=your_openai_key

# Git Services  
GITHUB_TOKEN=your_github_token
FORGEJO_BASE_URL=https://your-forgejo-instance.com
FORGEJO_TOKEN=your_forgejo_token

# Application Settings
DEBUG=True
LOG_LEVEL=DEBUG
```

### Configuration Management
Settings managed via Pydantic Settings with environment variable support:
```python
from doc_ai_helper_backend.core.config import settings

# Access configuration
api_key = settings.openai_api_key
debug_mode = settings.debug
```

## Testing Strategy

### Three-Tier Testing Approach

#### Unit Tests (`tests/unit/`)
- **External Dependencies**: Mocked/eliminated
- **Focus**: Individual component behavior
- **Speed**: Fast execution for development workflow
- **Usage**: `pytest tests/unit/ -v`

#### Integration Tests (`tests/integration/`)
- **External APIs**: Real GitHub, OpenAI, Forgejo services
- **Focus**: Service integration and API compatibility
- **Requirements**: Valid API keys and network access
- **Usage**: `pytest tests/integration/ -v`

#### End-to-End Tests (`tests/e2e/`)
- **Full System**: Complete request-response cycles
- **Focus**: User workflow scenarios
- **Usage**: `pytest tests/e2e/ -v`

### Test Markers
```bash
# Run specific test categories
pytest -m llm -v           # LLM-related tests
pytest -m git -v           # Git service tests
pytest -m mcp -v           # MCP tool tests
pytest -m streaming -v     # Streaming functionality
pytest -m performance -v   # Performance tests
```

## Development Workflow

### Adding New Features
1. **Write Tests First**: Create unit tests for new functionality
2. **Implement Service Layer**: Add business logic in appropriate service
3. **Add API Endpoints**: Create FastAPI endpoints with proper validation
4. **Update Documentation**: Add docstrings and update relevant docs
5. **Run Full Test Suite**: Ensure no regressions

### Adding New Git Provider
1. **Extend GitServiceBase**: Implement abstract methods
2. **Register in Factory**: Add to GitServiceFactory._services
3. **Add Configuration**: Environment variables and settings
4. **Write Tests**: Unit and integration tests
5. **Update Documentation**: Provider-specific setup instructions

### Adding New LLM Provider
1. **Extend LLMServiceBase**: Implement query, stream_query, etc.
2. **Register in Factory**: Add to LLMServiceFactory._services  
3. **Add Configuration**: API keys and provider settings
4. **Test Integration**: Verify tool calling and streaming support
5. **Update Documentation**: Configuration and usage examples

## Code Style and Quality

### Formatting Standards
- **Black**: Primary code formatter
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

### Type Hints
All functions must include comprehensive type hints:
```python
async def get_document(
    service: str,
    owner: str, 
    repo: str,
    path: str,
    ref: Optional[str] = None
) -> DocumentResponse:
```

### Docstring Format
Use Google-style docstrings:
```python
async def process_document(self, content: str, path: str) -> DocumentResponse:
    """Process document content and extract metadata.
    
    Args:
        content: Raw document content
        path: Document file path
        
    Returns:
        Processed document with metadata and transformed links
        
    Raises:
        DocumentProcessingException: If processing fails
    """
```

### Error Handling
- **Custom Exceptions**: Use domain-specific exceptions
- **HTTP Status Codes**: Map exceptions to appropriate HTTP status
- **Logging**: Log errors with context for debugging
- **User-Friendly Messages**: Provide clear error messages

## Current Implementation Status

### Completed Features ✅
- Markdown document processing with frontmatter and link transformation
- Git service abstraction (GitHub, Forgejo, Mock)
- LLM integration with OpenAI and streaming support
- MCP server with tool execution (document, feedback, analysis, git tools)
- Comprehensive test suite (230+ unit tests passing)
- Function calling and tool execution framework
- Conversation history management
- Response caching and performance optimization

### In Progress 🔄
- HTML document processing (Quarto preparation)
- Enhanced error handling and logging
- Performance optimization and monitoring

### Planned Features 📋
- Database layer implementation
- Repository management API
- Search functionality
- Additional LLM providers (Ollama, Anthropic)
- Quarto document support

## Troubleshooting Common Issues

### Integration Tests Failing
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $GITHUB_TOKEN

# Verify configuration
python -c "
from doc_ai_helper_backend.core.config import settings
print(f'OpenAI configured: {bool(settings.openai_api_key)}')
print(f'GitHub configured: {bool(settings.github_token)}')
"
```

### Import/Module Errors
```bash
# Ensure proper Python path
export PYTHONPATH=/home/ec2-user/doc_ai_helper_backend:$PYTHONPATH

# Install in development mode
pip install -e .
```

### Performance Issues
```bash
# Run unit tests only for faster development
pytest tests/unit/ -v

# Use parallel test execution
pytest tests/unit/ -n auto
```

## Security Considerations

- **API Keys**: Never commit API keys to repository
- **Environment Variables**: Use .env files for local development
- **Input Validation**: All API inputs validated via Pydantic models
- **Rate Limiting**: Respect external service rate limits
- **Error Sanitization**: Avoid exposing sensitive data in error messages

## API Documentation

Once the server is running, comprehensive API documentation is available at:
- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## Additional Resources

- **Architecture Guide**: docs/ARCHITECTURE.md
- **Development Guide**: docs/DEVELOPMENT.md  
- **Setup Guide**: docs/SETUP_GUIDE.md
- **API Reference**: docs/API_REFERENCE.md