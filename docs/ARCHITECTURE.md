# Architecture Guide

System architecture and design documentation for doc_ai_helper_backend.

## Table of Contents

- [System Overview](#system-overview)
- [Architecture Layers](#architecture-layers)
- [MCP Integration](#mcp-integration)
- [Git Service Abstraction](#git-service-abstraction)
- [Security Architecture](#security-architecture)
- [Performance Considerations](#performance-considerations)

## System Overview

doc_ai_helper_backend is a FastAPI-based backend service that provides:

1. **Document Processing**: Markdown/HTML document retrieval and processing
2. **LLM Integration**: OpenAI and other LLM provider integration
3. **MCP Tools**: Model Context Protocol tool execution
4. **Git Service Abstraction**: Unified interface for GitHub, Forgejo, and other Git services
5. **REST API**: RESTful endpoints for frontend integration

### High-Level Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Frontend Layer                       │
│              (React/Vue/Angular/etc.)                   │
└─────────────────────┬───────────────────────────────────┘
                      │ HTTP/REST API
┌─────────────────────▼───────────────────────────────────┐
│                 FastAPI Application                     │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ Document    │ │ LLM         │ │ MCP Tools           │ │
│  │ Endpoints   │ │ Endpoints   │ │ Integration         │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────┬───────────────────────────────────┘
                      │ Service Layer
┌─────────────────────▼───────────────────────────────────┐
│                  Service Layer                          │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ Document    │ │ LLM         │ │ MCP                 │ │
│  │ Service     │ │ Services    │ │ Server              │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────┬───────────────────────────────────┘
                      │ Provider Abstraction
┌─────────────────────▼───────────────────────────────────┐
│               Provider Implementations                   │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ Git         │ │ LLM         │ │ Tool                │ │
│  │ Services    │ │ Providers   │ │ Implementations     │ │
│  │ (GitHub,    │ │ (OpenAI,    │ │ (Document,          │ │
│  │  Forgejo)   │ │  Mock)      │ │  Feedback, etc.)    │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

## Architecture Layers

### 1. API Layer (`api/`)

**Responsibility**: HTTP endpoint definitions and request/response handling

**Components**:
- `endpoints/documents.py`: Document retrieval and processing
- `endpoints/llm.py`: LLM query and streaming endpoints
- `endpoints/health.py`: Health check and system status
- `api.py`: Router aggregation and configuration
- `dependencies.py`: Dependency injection setup
- `error_handlers.py`: Global error handling

**Key Patterns**:
- **Dependency Injection**: Services injected via FastAPI's dependency system
- **Request Validation**: Pydantic models for request/response validation
- **Error Handling**: Centralized error handling with custom exceptions

### 2. Service Layer (`services/`)

**Responsibility**: Business logic and orchestration between providers

#### Document Service (`services/document_service.py`)
- Orchestrates document retrieval and processing
- Manages document processors and link transformers
- Handles caching and metadata extraction

#### LLM Services (`services/llm/`)
- **Base Service** (`base.py`): Abstract interface for LLM providers
- **OpenAI Service** (`openai_service.py`): OpenAI API integration
- **Factory** (`factory.py`): Provider selection and instantiation
- **Cache Service** (`cache_service.py`): Response caching
- **Function Manager** (`function_manager.py`): Tool execution coordination

#### Git Services (`services/git/`)
- **Base Service** (`base.py`): Abstract interface for Git providers
- **GitHub Service** (`github_service.py`): GitHub API integration
- **Forgejo Service** (`forgejo_service.py`): Forgejo API integration
- **Factory** (`factory.py`): Provider selection based on service type

#### MCP Services (`services/mcp/`)
- **Server** (`server.py`): FastMCP server implementation
- **Tools** (`tools/`): Individual tool implementations
- **Adapter** (`adapter.py`): Tool execution and response formatting

### 3. Model Layer (`models/`)

**Responsibility**: Data structures and validation

**Components**:
- `document.py`: Document and metadata models
- `repository.py`: Repository structure models
- `frontmatter.py`: Frontmatter parsing models
- `link_info.py`: Link extraction and transformation models

### 4. Core Layer (`core/`)

**Responsibility**: Application configuration and utilities

**Components**:
- `config.py`: Environment-based configuration management
- `exceptions.py`: Custom exception definitions
- `logging.py`: Logging configuration

## MCP Integration

### MCP Architecture Overview

Model Context Protocol (MCP) integration provides standardized tool execution for LLM interactions.

```
┌─────────────────────────────────────────────────────────┐
│                 LLM Provider (OpenAI)                   │
└─────────────────────┬───────────────────────────────────┘
                      │ Function Calling
┌─────────────────────▼───────────────────────────────────┐
│               Function Manager                          │
│  ┌─────────────────────────────────────────────────────┐ │
│  │           Tool Registry                             │ │
│  │  • Document Tools  • Git Tools                     │ │
│  │  • Feedback Tools  • Analysis Tools                │ │
│  │  • Utility Tools                                   │ │
│  └─────────────────────────────────────────────────────┘ │
└─────────────────────┬───────────────────────────────────┘
                      │ Tool Execution
┌─────────────────────▼───────────────────────────────────┐
│                 MCP Server                              │
│  ┌─────────────┐ ┌─────────────┐ ┌─────────────────────┐ │
│  │ Document    │ │ Feedback    │ │ Git Tools           │ │
│  │ Tools       │ │ Tools       │ │                     │ │
│  └─────────────┘ └─────────────┘ └─────────────────────┘ │
└─────────────────────────────────────────────────────────┘
```

### Tool Categories

#### Document Tools
- **Purpose**: Document analysis and optimization
- **Implementation**: `services/mcp/tools/document_tools.py`
- **Functions**:
  - `analyze_document_structure`
  - `extract_document_context`
  - `optimize_document_content`

#### Feedback Tools
- **Purpose**: Conversation analysis and feedback generation
- **Implementation**: `services/mcp/tools/feedback_tools.py`
- **Functions**:
  - `generate_feedback_from_conversation`
  - `analyze_conversation_quality`

#### Git Tools
- **Purpose**: Git repository operations
- **Implementation**: `services/mcp/tools/git_tools.py`
- **Functions**:
  - `get_repository_info`
  - `get_file_content`
  - `create_issue`
  - `create_pull_request`

#### Analysis Tools
- **Purpose**: Text analysis and insights
- **Implementation**: `services/mcp/tools/analysis_tools.py`
- **Functions**:
  - `analyze_text_sentiment`
  - `extract_key_topics`

### Tool Execution Flow

1. **LLM Function Call**: LLM provider determines tool to execute
2. **Function Registry**: Maps function name to implementation
3. **Parameter Validation**: Validates tool parameters
4. **Tool Execution**: Executes tool with validated parameters
5. **Result Formatting**: Formats tool result for LLM consumption
6. **Response Integration**: Integrates tool result into LLM response

## Git Service Abstraction

### Unified Git Interface

The Git service abstraction provides a consistent interface across different Git hosting services.

```
┌─────────────────────────────────────────────────────────┐
│                GitServiceBase                           │
│  • get_file_content()    • list_repositories()         │
│  • get_repository_info() • get_user_info()             │
│  • create_issue()        • create_pull_request()       │
└─────────────────────┬───────────────────────────────────┘
                      │ Implementation
    ┌─────────────────┼─────────────────┐
    │                 │                 │
┌───▼──────┐ ┌────────▼─────┐ ┌─────────▼────┐
│ GitHub   │ │ Forgejo      │ │ Mock         │
│ Service  │ │ Service      │ │ Service      │
└──────────┘ └──────────────┘ └──────────────┘
```

### Service Selection

Services are selected via factory pattern based on configuration:

```python
# Environment Configuration
DEFAULT_GIT_SERVICE=forgejo
SUPPORTED_GIT_SERVICES=["github", "forgejo", "mock"]

# Service Creation
service = GitServiceFactory.create(
    service_type="forgejo",
    base_url=settings.forgejo_base_url,
    access_token=settings.forgejo_token
)
```

### Authentication Strategies

#### GitHub
- **Primary**: Personal Access Token
- **Scopes**: `repo`, `read:user`
- **Configuration**: `GITHUB_TOKEN`

#### Forgejo
- **Primary**: Access Token
- **Alternative**: Basic Authentication
- **Configuration**: `FORGEJO_TOKEN` or `FORGEJO_USERNAME`/`FORGEJO_PASSWORD`
- **Base URL**: `FORGEJO_BASE_URL`

#### Security Features
- **Token Validation**: Verify token permissions before use
- **Rate Limiting**: Respect service-specific rate limits
- **SSL Verification**: Configurable SSL certificate validation
- **Error Handling**: Graceful handling of authentication failures

## Security Architecture

### Authentication and Authorization

#### API Security
- **No Authentication Required**: Public API for demonstration
- **Environment Variables**: Sensitive credentials stored in environment
- **Token Management**: Secure token storage and rotation

#### External Service Security
- **GitHub**: OAuth token with minimal required permissions
- **Forgejo**: Access token or basic auth with HTTPS
- **OpenAI**: API key with usage monitoring

#### Data Security
- **No Persistent Storage**: Stateless operation
- **Memory-Only Caching**: Temporary response caching
- **Log Sanitization**: Sensitive data redacted from logs

### Input Validation

#### Request Validation
- **Pydantic Models**: Strong typing and validation
- **Parameter Sanitization**: Path traversal prevention
- **Content Validation**: Document content sanitization

#### LLM Input Safety
- **Prompt Injection Prevention**: Input sanitization
- **Content Filtering**: Inappropriate content detection
- **Tool Parameter Validation**: Strict parameter type checking

### Network Security

#### HTTPS Enforcement
- **External APIs**: All external communication over HTTPS
- **Certificate Validation**: Configurable SSL verification
- **Secure Headers**: Security headers in API responses

#### Rate Limiting
- **Provider Limits**: Respect external service rate limits
- **Circuit Breaker**: Failure detection and recovery
- **Retry Logic**: Exponential backoff for failed requests

## Performance Considerations

### Caching Strategy

#### LLM Response Caching
- **Cache Key**: Hash of prompt, options, and provider
- **TTL**: Configurable time-to-live
- **Memory Storage**: In-memory cache for development
- **Production**: Redis or similar for production deployments

#### Document Caching
- **Repository Metadata**: Cache repository structure
- **File Content**: Cache frequently accessed files
- **Link Processing**: Cache link transformation results

### Scalability

#### Horizontal Scaling
- **Stateless Design**: No server-side state
- **Load Balancing**: Multiple instance deployment
- **Database**: SQLite for development, PostgreSQL for production

#### Vertical Scaling
- **Async Operations**: AsyncIO for concurrent requests
- **Connection Pooling**: HTTP client connection reuse
- **Memory Management**: Efficient memory usage patterns

### Monitoring and Observability

#### Logging
- **Structured Logging**: JSON-formatted logs
- **Log Levels**: Configurable logging levels
- **Sensitive Data**: Redaction of sensitive information

#### Metrics
- **Response Times**: API endpoint performance
- **Error Rates**: Error frequency and types
- **External Services**: Third-party service health
- **Resource Usage**: Memory and CPU utilization

#### Health Checks
- **Liveness**: Application health status
- **Readiness**: Service dependency health
- **Deep Health**: External service connectivity

## Design Patterns

### Factory Pattern
Used for service creation and provider selection:
- `GitServiceFactory`: Git service instantiation
- `LLMServiceFactory`: LLM provider instantiation
- `DocumentProcessorFactory`: Document processor selection

### Adapter Pattern
Used for external service integration:
- `MCPAdapter`: Tool execution adaptation
- `LinkTransformer`: Link processing adaptation
- Service adapters for different Git providers

### Strategy Pattern
Used for configurable behavior:
- Document processing strategies
- Authentication strategies
- Caching strategies

### Dependency Injection
Used throughout the application:
- FastAPI dependency system
- Service layer dependencies
- Configuration injection

## Future Architecture Considerations

### Database Integration
- **Current**: Stateless, file-based operations
- **Future**: Database for user data, configuration, and caching
- **Migration**: Gradual migration from stateless to stateful

### Microservices
- **Current**: Monolithic FastAPI application
- **Future**: Potential microservice decomposition
- **Services**: Document service, LLM service, MCP service

### Event-Driven Architecture
- **Current**: Synchronous request-response
- **Future**: Event-driven processing for long-running operations
- **Benefits**: Better scalability and resilience

### AI/ML Model Integration
- **Current**: External LLM providers only
- **Future**: Local model hosting and inference
- **Considerations**: Resource requirements and latency

## Additional Resources

- [Setup Guide](./SETUP_GUIDE.md)
- [API Reference](./API_REFERENCE.md)
- [Development Guide](./DEVELOPMENT.md)
- [Project History](./PROJECT_HISTORY.md)
