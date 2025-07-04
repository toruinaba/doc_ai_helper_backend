# Setup Guide

このガイドでは、doc_ai_helper_backendの環境構築とセットアップ方法を説明します。

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Configuration](#environment-configuration)
- [Git Service Setup](#git-service-setup)
- [LLM Provider Setup](#llm-provider-setup)
- [Testing Configuration](#testing-configuration)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- Python 3.8 or higher
- Git (for repository operations)
- Network access to Git services (GitHub, Forgejo, etc.)
- Valid API keys for LLM providers (OpenAI, etc.)

### Supported Services

| Service Type | Providers | Status |
|--------------|-----------|---------|
| **Git Hosting** | GitHub, Forgejo, Mock | ✅ Supported |
| **LLM Providers** | OpenAI, Mock | ✅ Supported |
| **MCP Tools** | Document, Feedback, Analysis, Git | ✅ Supported |

## Environment Configuration

### 1. Create Environment File

Copy the example environment file:

```bash
cp .env.example .env
```

### 2. Basic Application Settings

```env
# Application Configuration
DEBUG=True
ENVIRONMENT=development
LOG_LEVEL=INFO
APP_NAME=doc_ai_helper_backend
API_PREFIX=/api/v1

# Security
SECRET_KEY=your-secret-key-here
```

### 3. Database Configuration

```env
# Database (SQLite for development)
DATABASE_URL=sqlite:///./data/app.db
```

## Git Service Setup

### GitHub Configuration

#### Option A: Access Token (Recommended)

1. **Create GitHub Personal Access Token**:
   - Go to GitHub Settings → Developer settings → Personal access tokens
   - Click "Generate new token (classic)"
   - Select scopes: `repo`, `read:user`
   - Copy the generated token

2. **Environment Configuration**:
```env
# GitHub Settings
GITHUB_TOKEN=your_github_token_here
DEFAULT_GIT_SERVICE=github
SUPPORTED_GIT_SERVICES=["github", "forgejo", "mock"]
```

### Forgejo Configuration

#### Step 1: Forgejo Server Requirements

- [ ] Forgejo server running and accessible
- [ ] User account with repository access
- [ ] API v1 support enabled
- [ ] Network connectivity from application server

#### Step 2: Create Forgejo Access Token

1. **Access Token Creation**:
   - Log into your Forgejo instance
   - Go to **Settings** → **Applications** → **Access Tokens**
   - Click **Generate New Token**
   - Token name: `doc_ai_helper_backend`
   - Required permissions:
     - `repository` - Repository access
     - `read:repository` - Read repository contents
     - `metadata:read` - Read metadata

2. **Environment Configuration**:
```env
# Forgejo Settings
FORGEJO_BASE_URL=https://your-forgejo-server.com
FORGEJO_TOKEN=your_forgejo_token_here

# Optional Settings
FORGEJO_VERIFY_SSL=True  # Set to False for self-signed certificates
FORGEJO_TIMEOUT=30       # Connection timeout in seconds
FORGEJO_MAX_RETRIES=3    # Maximum retry attempts

# Service Selection
DEFAULT_GIT_SERVICE=forgejo
SUPPORTED_GIT_SERVICES=["github", "forgejo", "mock"]
```

#### Step 3: Network Configuration

**URL Format**:
- Base URL: `https://your-server.com` (no trailing slash)
- API endpoint: `https://your-server.com/api/v1`

**SSL/TLS**:
- Valid SSL certificate for HTTPS
- For self-signed certificates: `FORGEJO_VERIFY_SSL=False`

**Firewall/Network**:
- Outbound HTTPS (443) or HTTP (80) access
- DNS resolution for Forgejo server
- No proxy blocking Git API endpoints

## LLM Provider Setup

### OpenAI Configuration

1. **Get OpenAI API Key**:
   - Visit [OpenAI API Keys](https://platform.openai.com/api-keys)
   - Create new secret key
   - Copy the key

2. **Environment Configuration**:
```env
# OpenAI Settings
OPENAI_API_KEY=your_openai_api_key_here
OPENAI_BASE_URL=https://api.openai.com/v1  # Optional, for custom endpoints
DEFAULT_LLM_PROVIDER=openai
DEFAULT_MODEL=gpt-3.5-turbo

# Optional: Alternative models
OPENAI_MODEL_GPT4=gpt-4
OPENAI_MODEL_GPT35=gpt-3.5-turbo
```

### LiteLLM Proxy (Optional)

For using LiteLLM proxy server:

```env
# LiteLLM Proxy Configuration
OPENAI_BASE_URL=http://localhost:4000/v1
OPENAI_API_KEY=your_litellm_api_key
```

## MCP Tools Configuration

### Enable MCP Features

```env
# MCP Configuration
MCP_SERVER_ENABLED=True
MCP_TOOLS_ENABLED=True

# Tool Categories
ENABLE_DOCUMENT_TOOLS=True
ENABLE_FEEDBACK_TOOLS=True
ENABLE_ANALYSIS_TOOLS=True
ENABLE_GIT_TOOLS=True

# GitHub Integration (optional)
ENABLE_GITHUB_TOOLS=True
```

### Available Tool Categories

| Category | Tools | Description |
|----------|-------|-------------|
| **Document** | analyze_structure, extract_context, optimize_content | Document analysis and optimization |
| **Feedback** | generate_feedback, analyze_quality | Conversation feedback and quality analysis |
| **Analysis** | sentiment_analysis, extract_topics | Text analysis and insights |
| **Git** | get_repository_info, get_file_content, create_issue | Git repository operations |

## Testing Configuration

### 1. Verify Environment Setup

```bash
# Check Python version
python --version

# Install dependencies
pip install -r requirements.txt

# Verify environment variables
python -c "
from doc_ai_helper_backend.core.config import settings
print(f'App: {settings.app_name}')
print(f'Git Service: {settings.default_git_service}')
print(f'LLM Provider: {settings.default_llm_provider}')
"
```

### 2. Test Git Service Connection

#### GitHub Test
```bash
python -c "
import asyncio
from doc_ai_helper_backend.services.git.github_service import GitHubService
from doc_ai_helper_backend.core.config import settings

async def test():
    service = GitHubService(settings.github_token)
    try:
        repos = await service.list_repositories()
        print(f'✅ GitHub: Found {len(repos)} repositories')
    except Exception as e:
        print(f'❌ GitHub: {e}')

asyncio.run(test())
"
```

#### Forgejo Test
```bash
python -c "
import asyncio
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService
from doc_ai_helper_backend.core.config import settings

async def test():
    service = ForgejoService(
        base_url=settings.forgejo_base_url,
        access_token=settings.forgejo_token
    )
    try:
        repos = await service.list_repositories()
        print(f'✅ Forgejo: Found {len(repos)} repositories')
    except Exception as e:
        print(f'❌ Forgejo: {e}')

asyncio.run(test())
"
```

### 3. Test LLM Provider

```bash
python -c "
import asyncio
from doc_ai_helper_backend.services.llm.openai_service import OpenAIService
from doc_ai_helper_backend.core.config import settings

async def test():
    service = OpenAIService(settings.openai_api_key)
    try:
        response = await service.query('Hello, test message')
        print(f'✅ OpenAI: {response.content[:50]}...')
    except Exception as e:
        print(f'❌ OpenAI: {e}')

asyncio.run(test())
"
```

### 4. Test MCP Tools

```bash
python -c "
import asyncio
from doc_ai_helper_backend.services.mcp.tools.document_tools import analyze_document_structure

async def test():
    try:
        result = await analyze_document_structure(
            '# Test Document\n\nThis is a test.',
            'basic'
        )
        print(f'✅ MCP Tools: {result[\"success\"]}')
    except Exception as e:
        print(f'❌ MCP Tools: {e}')

asyncio.run(test())
"
```

## Troubleshooting

### Common Issues

#### 1. Authentication Errors

**Symptoms**: 401 Unauthorized, 403 Forbidden errors

**Solutions**:
- Verify API keys are correctly set in `.env`
- Check token permissions and expiration
- For Forgejo: Ensure token has `repository` scope
- For GitHub: Ensure token has `repo` scope

#### 2. Connection Issues

**Symptoms**: Connection refused, timeout errors

**Solutions**:
- Verify network connectivity to service endpoints
- Check firewall settings
- For Forgejo: Verify `FORGEJO_BASE_URL` format
- Test with curl: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/user`

#### 3. SSL Certificate Issues

**Symptoms**: SSL verification failed

**Solutions**:
- For production: Ensure valid SSL certificates
- For development/self-signed: Set `FORGEJO_VERIFY_SSL=False`
- Update CA certificates: `pip install --upgrade certifi`

#### 4. MCP Tools Not Working

**Symptoms**: Tools not executing, function not found errors

**Solutions**:
- Verify `MCP_TOOLS_ENABLED=True`
- Check specific tool categories are enabled
- Restart application after config changes
- Review logs for detailed error messages

#### 5. Environment Variables Not Loading

**Symptoms**: Default values used instead of custom settings

**Solutions**:
- Verify `.env` file exists in project root
- Check file permissions (readable)
- No quotes around values unless necessary
- Restart application after changes

### Debug Mode

Enable detailed logging for troubleshooting:

```env
DEBUG=True
LOG_LEVEL=DEBUG
```

Check logs:
```bash
# View application logs
tail -f logs/app.log

# Or enable console logging
python -c "
import logging
logging.basicConfig(level=logging.DEBUG)
# Your test code here
"
```

### Manual API Testing

#### Test Forgejo API Access
```bash
curl -H "Authorization: token YOUR_TOKEN" \
     https://your-forgejo-server.com/api/v1/user
```

#### Test GitHub API Access
```bash
curl -H "Authorization: token YOUR_TOKEN" \
     https://api.github.com/user
```

#### Test OpenAI API Access
```bash
curl -H "Authorization: Bearer YOUR_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model": "gpt-3.5-turbo", "messages": [{"role": "user", "content": "Hello"}]}' \
     https://api.openai.com/v1/chat/completions
```

## Production Deployment

### Security Considerations

- Use strong `SECRET_KEY` (generate with `python -c "import secrets; print(secrets.token_urlsafe(32))"`)
- Store sensitive credentials in environment variables or secret management systems
- Use HTTPS in production
- Regularly rotate API keys and tokens
- Enable proper logging and monitoring

### Performance Optimization

- Set appropriate timeout values
- Enable caching for frequently accessed data
- Use connection pooling for external APIs
- Monitor rate limits for external services

### Monitoring

Set up monitoring for:
- API response times
- Error rates and types
- Token expiration
- Service availability
- Resource usage

## Additional Resources

- [API Reference](./API_REFERENCE.md)
- [Architecture Guide](./ARCHITECTURE.md)
- [Development Guide](./DEVELOPMENT.md)
- [Project History](./PROJECT_HISTORY.md)
