# Development Guide

Developer documentation for contributing to and maintaining doc_ai_helper_backend.

## Table of Contents

- [Development Environment](#development-environment)
- [Testing Strategy](#testing-strategy)
- [Code Quality](#code-quality)
- [Frontend Development](#frontend-development)
- [Debugging](#debugging)
- [Contributing Guidelines](#contributing-guidelines)

## Development Environment

### Prerequisites

- Python 3.8+
- Git
- Code editor (VS Code recommended)
- Network access for external APIs

### Initial Setup

1. **Clone Repository**:
```bash
git clone <repository-url>
cd doc_ai_helper_backend
```

2. **Create Virtual Environment**:
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. **Install Dependencies**:
```bash
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies
```

4. **Environment Configuration**:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. **Verify Installation**:
```bash
python -m pytest tests/unit/ -v
```

### Running the Application

#### Development Server
```bash
# Standard uvicorn
uvicorn doc_ai_helper_backend.main:app --reload --host 0.0.0.0 --port 8000

# With detailed logging
uvicorn doc_ai_helper_backend.main:app --reload --log-level debug

# Production-like
uvicorn doc_ai_helper_backend.main:app --host 0.0.0.0 --port 8000
```

#### Docker Development
```bash
# Build development image
docker build -t doc_ai_helper_backend:dev .

# Run with development settings
docker-compose up -d

# View logs
docker-compose logs -f
```

## Testing Strategy

### Test Organization

```
tests/
├── unit/                    # Unit tests (fast, isolated)
│   ├── api/                # API endpoint tests
│   ├── services/           # Service layer tests
│   └── models/             # Model validation tests
├── integration/            # Integration tests (slower, external deps)
│   ├── github/             # GitHub API integration
│   ├── openai/             # OpenAI API integration
│   └── mcp/                # MCP tool integration
└── conftest.py             # Test configuration and fixtures
```

### Running Tests

#### Daily Development Tests
```bash
# All unit tests (recommended for daily development)
pytest tests/unit/ -v

# Specific module tests
pytest tests/unit/services/llm/ -v
pytest tests/unit/api/ -v
pytest tests/unit/services/document/ -v

# With coverage
pytest tests/unit/ --cov=doc_ai_helper_backend --cov-report=html
```

#### Feature-Specific Tests
```bash
# LLM-related tests
pytest tests/unit/services/llm/ tests/unit/api/test_llm.py -v

# Document processing tests
pytest tests/unit/services/document/ tests/unit/api/test_documents.py -v

# API endpoint tests
pytest tests/unit/api/ -v

# Error handling tests
pytest tests/unit/ -k "error" -v
```

#### Performance Tests
```bash
# Performance tests (if available)
pytest tests/unit/ -m "performance" -v

# Benchmark tests with detailed output
pytest tests/unit/ -m "benchmark" --benchmark-verbose
```

### Integration Tests (Pre-deployment)

**⚠️ Requires API keys and network access**

#### Environment Setup
```bash
# Required environment variables
export OPENAI_API_KEY=your_openai_api_key
export GITHUB_TOKEN=your_github_token
export FORGEJO_BASE_URL=your_forgejo_url
export FORGEJO_TOKEN=your_forgejo_token
```

#### Running Integration Tests
```bash
# All integration tests
pytest tests/integration/ -v

# Timeout for slow tests
pytest tests/integration/ --timeout=60 -v

# Specific service integration
pytest tests/integration/github/ -v
pytest tests/integration/openai/ -v
pytest tests/integration/mcp/ -v
```

#### Full Test Suite
```bash
# Unit tests + Integration tests
pytest tests/ -v

# With coverage report
pytest tests/ --cov=doc_ai_helper_backend --cov-report=html

# Generate coverage badge
coverage-badge -o coverage.svg
```

### Test Results Interpretation

#### Success Output Example
```
========================= test session starts =========================
tests/unit/services/llm/test_openai_service.py::test_query_success PASSED
tests/unit/services/llm/test_cache_service.py::test_cache_hit PASSED
tests/unit/api/test_documents.py::test_get_document_success PASSED

========================= 329 passed in 45.67s =========================
```

#### Failure Handling

When tests fail:

1. **Read the error message carefully**
2. **Check environment variables**
3. **Verify external service connectivity**
4. **Run individual failing tests for isolation**

```bash
# Run specific failing test
pytest tests/unit/services/llm/test_openai_service.py::test_query_success -v -s

# Debug mode with print statements
pytest tests/unit/services/llm/test_openai_service.py::test_query_success -v -s --pdb
```

## Code Quality

### Code Formatting

#### Black (Primary Formatter)
```bash
# Format all code
black doc_ai_helper_backend/

# Check formatting without changes
black --check doc_ai_helper_backend/

# Format specific files
black doc_ai_helper_backend/services/llm/
```

#### Import Sorting
```bash
# Sort imports
isort doc_ai_helper_backend/

# Check import order
isort --check-only doc_ai_helper_backend/
```

### Type Checking

```bash
# Type checking with mypy
mypy doc_ai_helper_backend/

# Specific module
mypy doc_ai_helper_backend/services/llm/
```

### Linting

```bash
# Lint with flake8
flake8 doc_ai_helper_backend/

# Lint with pylint
pylint doc_ai_helper_backend/
```

### Pre-commit Hooks

Set up pre-commit hooks for automatic code quality:

```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Code Review Checklist

- [ ] All tests pass
- [ ] Code is formatted with Black
- [ ] Imports are sorted with isort
- [ ] Type hints are provided
- [ ] Docstrings are present for public APIs
- [ ] Error handling is appropriate
- [ ] Security considerations addressed
- [ ] Performance implications considered

## Frontend Development

### API Integration Patterns

#### Basic HTTP Client Setup
```typescript
// api-client.ts
const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000/api/v1';

class ApiClient {
  private baseURL: string;

  constructor(baseURL: string = API_BASE_URL) {
    this.baseURL = baseURL;
  }

  async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const url = `${this.baseURL}${endpoint}`;
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    return response.json();
  }
}

export const apiClient = new ApiClient();
```

#### Document Service Integration
```typescript
// services/document-service.ts
import { apiClient } from '../api-client';

export interface DocumentResponse {
  path: string;
  name: string;
  type: string;
  content: {
    content: string;
    encoding: string;
  };
  metadata: any;
  transformed_content?: string;
}

export class DocumentService {
  async getDocument(
    service: string,
    owner: string,
    repo: string,
    path: string,
    ref: string = 'main'
  ): Promise<DocumentResponse> {
    return apiClient.request(
      `/documents/contents/${service}/${owner}/${repo}/${path}?ref=${ref}`
    );
  }

  async getRepositoryStructure(
    service: string,
    owner: string,
    repo: string,
    ref: string = 'main'
  ) {
    return apiClient.request(
      `/documents/structure/${service}/${owner}/${repo}?ref=${ref}`
    );
  }
}
```

#### LLM Service Integration
```typescript
// services/llm-service.ts
export interface LLMQueryRequest {
  prompt: string;
  provider: string;
  enable_tools: boolean;
  tool_choice?: string;
  model?: string;
  temperature?: number;
  max_tokens?: number;
}

export class LLMService {
  async query(request: LLMQueryRequest): Promise<any> {
    return apiClient.request('/llm/query', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  async streamQuery(
    request: LLMQueryRequest,
    onChunk: (text: string) => void,
    onComplete: () => void,
    onError: (error: string) => void
  ) {
    const response = await fetch(`${API_BASE_URL}/llm/stream`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify(request),
    });

    if (!response.ok) {
      onError(`HTTP error! status: ${response.status}`);
      return;
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

    try {
      while (true) {
        const { done, value } = await reader!.read();
        if (done) break;

        const chunk = decoder.decode(value);
        const lines = chunk.split('\\n');

        for (const line of lines) {
          if (line.startsWith('data: ')) {
            const data = JSON.parse(line.slice(6));
            
            if (data.text) {
              onChunk(data.text);
            } else if (data.done) {
              onComplete();
              return;
            } else if (data.error) {
              onError(data.error);
              return;
            }
          }
        }
      }
    } catch (error) {
      onError(error instanceof Error ? error.message : 'Unknown error');
    }
  }
}
```

### React Integration Examples

#### Document Viewer Component
```tsx
// components/DocumentViewer.tsx
import React, { useState, useEffect } from 'react';
import { DocumentService, DocumentResponse } from '../services/document-service';

interface DocumentViewerProps {
  service: string;
  owner: string;
  repo: string;
  path: string;
}

export const DocumentViewer: React.FC<DocumentViewerProps> = ({
  service,
  owner,
  repo,
  path,
}) => {
  const [document, setDocument] = useState<DocumentResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const loadDocument = async () => {
      try {
        const documentService = new DocumentService();
        const doc = await documentService.getDocument(service, owner, repo, path);
        setDocument(doc);
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Unknown error');
      } finally {
        setLoading(false);
      }
    };

    loadDocument();
  }, [service, owner, repo, path]);

  if (loading) return <div>Loading...</div>;
  if (error) return <div>Error: {error}</div>;
  if (!document) return <div>No document found</div>;

  return (
    <div className="document-viewer">
      <h1>{document.name}</h1>
      <div className="metadata">
        <p>Size: {document.metadata.size} bytes</p>
        <p>Last modified: {document.metadata.last_modified}</p>
      </div>
      <div className="content">
        <pre>{document.content.content}</pre>
      </div>
    </div>
  );
};
```

#### LLM Chat Component
```tsx
// components/LLMChat.tsx
import React, { useState } from 'react';
import { LLMService, LLMQueryRequest } from '../services/llm-service';

export const LLMChat: React.FC = () => {
  const [messages, setMessages] = useState<Array<{ role: string; content: string }>>([]);
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [streaming, setStreaming] = useState('');

  const llmService = new LLMService();

  const sendMessage = async () => {
    if (!input.trim()) return;

    const userMessage = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setLoading(true);
    setStreaming('');

    const request: LLMQueryRequest = {
      prompt: input,
      provider: 'openai',
      enable_tools: true,
      tool_choice: 'auto',
    };

    try {
      await llmService.streamQuery(
        request,
        (text) => {
          setStreaming(prev => prev + text);
        },
        () => {
          setMessages(prev => [...prev, { role: 'assistant', content: streaming }]);
          setStreaming('');
          setLoading(false);
        },
        (error) => {
          console.error('Streaming error:', error);
          setLoading(false);
        }
      );
    } catch (error) {
      console.error('Chat error:', error);
      setLoading(false);
    }
  };

  return (
    <div className="llm-chat">
      <div className="messages">
        {messages.map((message, index) => (
          <div key={index} className={`message ${message.role}`}>
            <strong>{message.role}:</strong> {message.content}
          </div>
        ))}
        {streaming && (
          <div className="message assistant streaming">
            <strong>assistant:</strong> {streaming}
          </div>
        )}
      </div>
      <div className="input-area">
        <input
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyPress={(e) => e.key === 'Enter' && sendMessage()}
          disabled={loading}
        />
        <button onClick={sendMessage} disabled={loading}>
          {loading ? 'Sending...' : 'Send'}
        </button>
      </div>
    </div>
  );
};
```

### State Management

#### React Context for Global State
```tsx
// contexts/AppContext.tsx
import React, { createContext, useContext, useReducer } from 'react';

interface AppState {
  currentRepository: {
    service: string;
    owner: string;
    repo: string;
  } | null;
  settings: {
    llmProvider: string;
    enableTools: boolean;
  };
}

const initialState: AppState = {
  currentRepository: null,
  settings: {
    llmProvider: 'openai',
    enableTools: true,
  },
};

const AppContext = createContext<{
  state: AppState;
  dispatch: React.Dispatch<any>;
} | null>(null);

export const useAppContext = () => {
  const context = useContext(AppContext);
  if (!context) {
    throw new Error('useAppContext must be used within AppProvider');
  }
  return context;
};

export const AppProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [state, dispatch] = useReducer(appReducer, initialState);

  return (
    <AppContext.Provider value={{ state, dispatch }}>
      {children}
    </AppContext.Provider>
  );
};
```

## Debugging

### Backend Debugging

#### Enable Debug Logging
```bash
# Environment variable
export DEBUG=True
export LOG_LEVEL=DEBUG

# Or in .env file
DEBUG=True
LOG_LEVEL=DEBUG
```

#### Python Debugger
```python
# Insert breakpoint in code
import pdb; pdb.set_trace()

# Or use built-in breakpoint() (Python 3.7+)
breakpoint()
```

#### FastAPI Debug Mode
```python
# main.py
app = FastAPI(debug=True)

# Or via environment
if settings.debug:
    app.debug = True
```

#### API Testing with curl
```bash
# Test basic endpoint
curl -X GET "http://localhost:8000/api/v1/health" -v

# Test with authentication
curl -X GET "http://localhost:8000/api/v1/documents/structure/github/octocat/Hello-World" -v

# Test LLM endpoint
curl -X POST "http://localhost:8000/api/v1/llm/query" \\
  -H "Content-Type: application/json" \\
  -d '{"prompt": "Hello", "provider": "openai", "enable_tools": false}' -v
```

### Common Issues and Solutions

#### 1. Integration Tests Skipped
**Problem**: Tests marked as skipped due to missing API keys

**Solution**:
```bash
# Check environment variables
echo $OPENAI_API_KEY
echo $GITHUB_TOKEN

# Set missing variables
export OPENAI_API_KEY=your_key_here
export GITHUB_TOKEN=your_token_here

# Verify in Python
python -c "
from doc_ai_helper_backend.core.config import settings
print(f'OpenAI: {bool(settings.openai_api_key)}')
print(f'GitHub: {bool(settings.github_token)}')
"
```

#### 2. Tests Running Slowly
**Problem**: Integration tests taking too long

**Solution**:
```bash
# Run only unit tests for development
pytest tests/unit/ -v

# Use parallel execution
pytest tests/unit/ -n auto

# Set timeout for slow tests
pytest tests/integration/ --timeout=30
```

#### 3. Coverage Issues
**Problem**: Low test coverage

**Check coverage**:
```bash
pytest tests/unit/ --cov=doc_ai_helper_backend --cov-report=term-missing

# Focus on specific modules
pytest tests/unit/services/llm/ --cov=doc_ai_helper_backend.services.llm --cov-report=html
```

#### 4. Mock Service Issues
**Problem**: Mock services not behaving as expected

**Debug**:
```python
# Test mock service directly
from doc_ai_helper_backend.services.git.mock_service import MockGitService

service = MockGitService()
result = await service.get_file_content("test", "test", "README.md")
print(result)
```

### Performance Debugging

#### Profile API Endpoints
```python
# Add profiling to specific endpoints
import cProfile
import pstats

def profile_endpoint():
    profiler = cProfile.Profile()
    profiler.enable()
    
    # Your endpoint code here
    
    profiler.disable()
    stats = pstats.Stats(profiler)
    stats.sort_stats('cumulative')
    stats.print_stats()
```

#### Memory Usage Monitoring
```python
import psutil
import os

def log_memory_usage():
    process = psutil.Process(os.getpid())
    memory_info = process.memory_info()
    print(f"Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB")
```

## Contributing Guidelines

### Code Style

1. **Follow PEP 8** with Black formatting
2. **Use type hints** for all function parameters and return values
3. **Write docstrings** for all public functions and classes
4. **Keep functions small** and focused on single responsibility
5. **Use meaningful variable names**

### Commit Messages

Follow conventional commit format:
```
type(scope): description

[optional body]

[optional footer]
```

Examples:
```
feat(llm): add streaming response support
fix(git): handle authentication errors gracefully
docs(api): update endpoint documentation
test(mcp): add integration tests for git tools
```

### Pull Request Process

1. **Create feature branch** from main
2. **Write tests** for new functionality
3. **Ensure all tests pass**
4. **Update documentation** if needed
5. **Submit pull request** with clear description

### Issue Reporting

When reporting issues, include:
- **Environment details** (Python version, OS, etc.)
- **Steps to reproduce**
- **Expected vs actual behavior**
- **Error messages and logs**
- **Configuration details** (sanitized)

## Additional Resources

- [Setup Guide](./SETUP_GUIDE.md)
- [API Reference](./API_REFERENCE.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [Project History](./PROJECT_HISTORY.md)
- [Python Testing Documentation](https://docs.python.org/3/library/unittest.html)
- [FastAPI Testing](https://fastapi.tiangolo.com/tutorial/testing/)
- [Pytest Documentation](https://docs.pytest.org/)
