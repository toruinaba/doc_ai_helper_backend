# API Reference

Complete API reference for doc_ai_helper_backend, including REST endpoints, MCP tools, and frontend integration examples.

## Table of Contents

- [Base Configuration](#base-configuration)
- [Document API](#document-api)
- [LLM API](#llm-api)
- [MCP Tools API](#mcp-tools-api)
- [Git Tools Integration](#git-tools-integration)
- [Frontend Integration](#frontend-integration)
- [Error Handling](#error-handling)

## Base Configuration

### API Base URL
```
http://localhost:8000/api/v1
```

### Authentication
Currently, authentication is handled via environment variables. No API key is required for client requests.

### Content Type
All requests should use `Content-Type: application/json` for POST/PUT requests.

## Document API

### Get Document Content

Retrieve document content from Git repositories with optional link transformation.

**Endpoint**: `GET /documents/contents/{service}/{owner}/{repo}/{path:path}`

**Parameters**:
- `service`: Git service (`github`, `forgejo`, `mock`)
- `owner`: Repository owner
- `repo`: Repository name  
- `path`: Document path

**Query Parameters**:
- `ref`: Branch or tag name (default: `main`)
- `transform_links`: Transform relative links to absolute (default: `true`)
- `base_url`: Base URL for link transformation

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/contents/github/octocat/Hello-World/README.md?ref=main&transform_links=true"
```

**Response**:
```json
{
  "path": "README.md",
  "name": "README.md",
  "type": "markdown",
  "content": {
    "content": "# Hello World\\n\\nThis is a sample repository.",
    "encoding": "utf-8"
  },
  "metadata": {
    "size": 42,
    "last_modified": "2024-01-01T12:00:00Z",
    "content_type": "text/markdown",
    "sha": "abc123def456",
    "download_url": "https://github.com/octocat/Hello-World/raw/main/README.md",
    "frontmatter": {
      "title": "Hello World",
      "description": "Sample repository"
    },
    "title": "Hello World",
    "description": "Sample repository",
    "author": null,
    "date": null,
    "tags": []
  },
  "repository": "Hello-World",
  "owner": "octocat",
  "service": "github",
  "ref": "main",
  "links": [
    {
      "text": "documentation",
      "url": "https://github.com/octocat/Hello-World/blob/main/docs",
      "is_image": false,
      "position": [45, 70],
      "is_external": false
    }
  ],
  "transformed_content": "# Hello World\\n\\nThis is a sample repository with [documentation](https://github.com/octocat/Hello-World/blob/main/docs)."
}
```

### Get Repository Structure

Retrieve the file structure of a repository.

**Endpoint**: `GET /documents/structure/{service}/{owner}/{repo}`

**Query Parameters**:
- `ref`: Branch or tag name (default: `main`)
- `recursive`: Include subdirectories (default: `true`)

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/documents/structure/github/octocat/Hello-World?ref=main&recursive=true"
```

**Response**:
```json
{
  "files": [
    {
      "path": "README.md",
      "name": "README.md",
      "type": "file",
      "size": 42,
      "download_url": "https://github.com/octocat/Hello-World/raw/main/README.md"
    },
    {
      "path": "docs",
      "name": "docs",
      "type": "dir",
      "size": null,
      "download_url": null
    }
  ],
  "repository": "Hello-World",
  "owner": "octocat",
  "service": "github",
  "ref": "main"
}
```

## LLM API

### Basic LLM Query

Send queries to LLM providers with optional tool execution.

**Endpoint**: `POST /llm/query`

**Request Body**:
```json
{
  "prompt": "Your question or instruction",
  "provider": "openai",
  "enable_tools": false,
  "tool_choice": "auto",
  "model": "gpt-3.5-turbo",
  "temperature": 0.7,
  "max_tokens": 1000,
  "conversation_history": []
}
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Hello, how are you?",
    "provider": "openai",
    "enable_tools": false
  }'
```

**Response**:
```json
{
  "content": "Hello! I'm doing well, thank you for asking. How can I help you today?",
  "model": "gpt-3.5-turbo",
  "provider": "openai",
  "usage": {
    "prompt_tokens": 12,
    "completion_tokens": 25,
    "total_tokens": 37
  },
  "tool_calls": null,
  "tool_execution_results": null
}
```

### LLM Query with Tools

Execute LLM queries with MCP tool integration.

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Analyze this document structure: # Title\\n\\n## Section 1\\n\\nContent here.",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "auto"
  }'
```

**Response with Tool Execution**:
```json
{
  "content": "I've analyzed the document structure. It has a clear hierarchy with a main title and one section.",
  "model": "gpt-3.5-turbo",
  "provider": "openai",
  "usage": {
    "prompt_tokens": 45,
    "completion_tokens": 30,
    "total_tokens": 75
  },
  "tool_calls": [
    {
      "id": "call_123456",
      "type": "function",
      "function": {
        "name": "analyze_document_structure",
        "arguments": "{\\"document_content\\": \\"# Title\\\\n\\\\n## Section 1\\\\n\\\\nContent here.\\", \\"analysis_type\\": \\"basic\\"}"
      }
    }
  ],
  "tool_execution_results": [
    {
      "tool_call_id": "call_123456",
      "function_name": "analyze_document_structure",
      "result": "{\\"success\\": true, \\"structure\\": {\\"title\\": \\"Title\\", \\"sections\\": 1, \\"headings\\": [\\"Title\\", \\"Section 1\\"]}}"
    }
  ]
}
```

### Streaming LLM Query

Get real-time streaming responses from LLM providers.

**Endpoint**: `POST /llm/stream`

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/llm/stream" \\
  -H "Content-Type: application/json" \\
  -H "Accept: text/event-stream" \\
  -d '{
    "prompt": "Count from 1 to 5",
    "provider": "openai",
    "enable_tools": true
  }'
```

**Response (Server-Sent Events)**:
```
data: {"text": "1", "done": false}

data: {"text": ", 2", "done": false}

data: {"text": ", 3", "done": false}

data: {"text": ", 4", "done": false}

data: {"text": ", 5", "done": false}

data: {"done": true, "usage": {"total_tokens": 15}}
```

## MCP Tools API

### List Available Tools

Get information about all available MCP tools.

**Endpoint**: `GET /llm/tools`

**Example Request**:
```bash
curl -X GET "http://localhost:8000/api/v1/llm/tools"
```

**Response**:
```json
{
  "tools": [
    {
      "name": "analyze_document_structure",
      "description": "Analyze the structure and organization of a document",
      "parameters": [
        {
          "name": "document_content",
          "type": "str",
          "description": "Content of the document to analyze",
          "required": true,
          "default": null
        },
        {
          "name": "analysis_type",
          "type": "str",
          "description": "Type of analysis to perform",
          "required": false,
          "default": "basic"
        }
      ],
      "category": "document",
      "enabled": true
    }
  ],
  "total_tools": 12,
  "categories": {
    "document": 3,
    "feedback": 2,
    "analysis": 2,
    "git": 4,
    "utility": 1
  }
}
```

### Available Tool Categories

#### Document Tools
- `analyze_document_structure`: Analyze document hierarchy and organization
- `extract_document_context`: Extract key information and context
- `optimize_document_content`: Improve document structure and content

#### Feedback Tools  
- `generate_feedback_from_conversation`: Generate feedback from conversation history
- `analyze_conversation_quality`: Analyze conversation quality and effectiveness

#### Analysis Tools
- `analyze_text_sentiment`: Perform sentiment analysis on text
- `extract_key_topics`: Extract main topics and themes from text

#### Git Tools
- `get_repository_info`: Get repository information and metadata
- `get_file_content`: Retrieve file content from Git repositories
- `create_issue`: Create issues in Git repositories
- `create_pull_request`: Create pull requests in Git repositories

#### Utility Tools
- `calculate`: Perform mathematical calculations
- `format_text`: Format text (uppercase, lowercase, title case, etc.)

## Git Tools Integration

### Repository Operations

#### Get Repository Information

**Usage in LLM Query**:
```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Get information about the octocat/Hello-World repository on GitHub",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "get_repository_info"
  }'
```

#### Create GitHub Issue

**Usage in LLM Query**:
```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Create an issue in octocat/Hello-World repository with title '\''Bug Report'\'' and description '\''Found a bug in the documentation'\''",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "create_issue"
  }'
```

### Forgejo-Specific Usage

For Forgejo repositories, ensure your environment is configured with:

```env
FORGEJO_BASE_URL=https://your-forgejo-server.com
FORGEJO_TOKEN=your_access_token
```

**Example Request**:
```bash
curl -X POST "http://localhost:8000/api/v1/llm/query" \\
  -H "Content-Type: application/json" \\
  -d '{
    "prompt": "Get the README.md content from myuser/myproject repository on Forgejo",
    "provider": "openai",
    "enable_tools": true,
    "tool_choice": "get_file_content"
  }'
```

## Frontend Integration

### JavaScript/TypeScript Examples

#### Basic LLM Query Function

```typescript
interface LLMResponse {
  content: string;
  model: string;
  provider: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  };
  tool_calls?: any[];
  tool_execution_results?: any[];
}

async function queryLLM(
  prompt: string, 
  enableTools: boolean = false,
  toolChoice: string = 'auto'
): Promise<LLMResponse> {
  const response = await fetch('/api/v1/llm/query', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      prompt,
      provider: 'openai',
      enable_tools: enableTools,
      tool_choice: toolChoice
    })
  });

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
```

#### Streaming Response Handler

```typescript
async function streamLLMQuery(
  prompt: string,
  onChunk: (text: string) => void,
  onComplete: (usage?: any) => void,
  onError: (error: string) => void
) {
  try {
    const response = await fetch('/api/v1/llm/stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Accept': 'text/event-stream'
      },
      body: JSON.stringify({
        prompt,
        provider: 'openai',
        enable_tools: true,
        tool_choice: 'auto'
      })
    });

    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }

    const reader = response.body?.getReader();
    const decoder = new TextDecoder();

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
            onComplete(data.usage);
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
```

#### Document Content Fetcher

```typescript
interface DocumentResponse {
  path: string;
  name: string;
  type: string;
  content: {
    content: string;
    encoding: string;
  };
  metadata: any;
  repository: string;
  owner: string;
  service: string;
  ref: string;
  links: any[];
  transformed_content?: string;
}

async function getDocument(
  service: string,
  owner: string,
  repo: string,
  path: string,
  ref: string = 'main',
  transformLinks: boolean = true
): Promise<DocumentResponse> {
  const params = new URLSearchParams({
    ref,
    transform_links: transformLinks.toString()
  });

  const response = await fetch(
    `/api/v1/documents/contents/${service}/${owner}/${repo}/${path}?${params}`,
    {
      method: 'GET',
      headers: {
        'Accept': 'application/json',
      }
    }
  );

  if (!response.ok) {
    throw new Error(`HTTP error! status: ${response.status}`);
  }

  return await response.json();
}
```

### React Hook Example

```tsx
import { useState, useCallback } from 'react';

export function useLLMQuery() {
  const [loading, setLoading] = useState(false);
  const [response, setResponse] = useState<LLMResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  const queryWithTools = useCallback(async (
    prompt: string,
    enableTools: boolean = true,
    toolChoice: string = 'auto'
  ) => {
    setLoading(true);
    setError(null);

    try {
      const result = await queryLLM(prompt, enableTools, toolChoice);
      setResponse(result);
      return result;
    } catch (err) {
      const errorMsg = err instanceof Error ? err.message : 'Unknown error';
      setError(errorMsg);
      throw err;
    } finally {
      setLoading(false);
    }
  }, []);

  return { queryWithTools, loading, response, error };
}

// Usage in component
function DocumentAnalyzer() {
  const { queryWithTools, loading, response, error } = useLLMQuery();

  const analyzeDocument = async (content: string) => {
    await queryWithTools(
      `Analyze this document structure: ${content}`,
      true,
      'analyze_document_structure'
    );
  };

  return (
    <div>
      {loading && <div>Analyzing...</div>}
      {error && <div>Error: {error}</div>}
      {response && (
        <div>
          <h3>Analysis Result:</h3>
          <p>{response.content}</p>
          {response.tool_execution_results && (
            <pre>{JSON.stringify(response.tool_execution_results, null, 2)}</pre>
          )}
        </div>
      )}
    </div>
  );
}
```

## Error Handling

### HTTP Status Codes

| Status Code | Description | Common Causes |
|-------------|-------------|---------------|
| 200 | Success | Request completed successfully |
| 400 | Bad Request | Invalid request parameters or body |
| 401 | Unauthorized | Missing or invalid authentication |
| 403 | Forbidden | Insufficient permissions |
| 404 | Not Found | Resource not found |
| 429 | Too Many Requests | Rate limit exceeded |
| 500 | Internal Server Error | Server-side error |

### Error Response Format

```json
{
  "detail": "Error message",
  "error_type": "ValidationError",
  "status_code": 400
}
```

### Common Error Scenarios

#### 1. Authentication Errors
```bash
# Response
{
  "detail": "GitHub authentication failed",
  "error_type": "AuthenticationError",
  "status_code": 401
}
```

#### 2. Repository Not Found
```bash
# Response  
{
  "detail": "Repository 'owner/repo' not found",
  "error_type": "NotFoundError",
  "status_code": 404
}
```

#### 3. Tool Execution Errors
```json
{
  "content": "I encountered an error while executing the tool.",
  "tool_calls": [...],
  "tool_execution_results": [
    {
      "tool_call_id": "call_123",
      "function_name": "analyze_document_structure",
      "error": "Invalid document format"
    }
  ]
}
```

### Error Handling Best Practices

1. **Always check HTTP status codes**
2. **Handle rate limiting with exponential backoff**
3. **Validate request parameters before sending**
4. **Implement proper retry logic for transient errors**
5. **Log errors for debugging and monitoring**

## Rate Limiting

### Current Limits

- **LLM API**: Limited by provider (OpenAI, etc.)
- **Git API**: Limited by service (GitHub: 5000/hour, Forgejo: varies)
- **Document API**: No explicit limits (depends on Git API)

### Rate Limit Headers

Responses include rate limit information:

```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1640995200
```

### Handling Rate Limits

```typescript
async function handleRateLimitedRequest<T>(
  requestFn: () => Promise<T>,
  maxRetries: number = 3
): Promise<T> {
  for (let attempt = 0; attempt < maxRetries; attempt++) {
    try {
      return await requestFn();
    } catch (error) {
      if (error.status === 429) {
        const retryAfter = error.headers?.['retry-after'] || Math.pow(2, attempt);
        await new Promise(resolve => setTimeout(resolve, retryAfter * 1000));
        continue;
      }
      throw error;
    }
  }
  throw new Error('Max retries exceeded');
}
```

## Additional Resources

- [Setup Guide](./SETUP_GUIDE.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [Development Guide](./DEVELOPMENT.md)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [GitHub API Documentation](https://docs.github.com/en/rest)
- [Forgejo API Documentation](https://forgejo.org/docs/latest/api/)
