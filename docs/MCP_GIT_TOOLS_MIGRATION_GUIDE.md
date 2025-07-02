# MCP Git Tools Migration Guide

This guide helps you migrate from the legacy GitHub-only MCP tools to the new unified Git tools that support multiple Git hosting services (GitHub, Forgejo, and future services like GitLab).

## Overview

The MCP Git tools have been abstracted and unified to support multiple Git hosting services while maintaining backward compatibility. The new architecture provides:

- **Unified Interface**: Single set of tools (`create_git_issue`, `create_git_pull_request`, `check_git_repository_permissions`) that work with multiple Git services
- **Service Selection**: Choose your Git service through configuration or runtime parameters
- **Multiple Authentication Methods**: Support for tokens, username/password, and other authentication methods
- **Extensibility**: Easy to add support for new Git services in the future

## Breaking Changes

### Tool Names

The legacy GitHub-specific tools have been replaced with unified Git tools:

| Legacy Tool (Deprecated) | New Unified Tool |
|--------------------------|------------------|
| `create_github_issue` | `create_git_issue` |
| `create_github_pull_request` | `create_git_pull_request` |
| `check_github_repository_permissions` | `check_git_repository_permissions` |

### Function Signatures

The new unified tools have updated function signatures that support multiple services:

#### create_git_issue

**Old (GitHub-only):**
```python
await create_github_issue(
    title="Bug fix needed",
    description="Description of the issue",
    labels=["bug"],
    assignees=["user1"],
    github_token="ghp_xxx"
)
```

**New (Unified):**
```python
await create_git_issue(
    title="Bug fix needed",
    description="Description of the issue",
    labels=["bug"],
    assignees=["user1"],
    service_type="github",  # or "forgejo"
    github_token="ghp_xxx",  # For GitHub
    # OR for Forgejo:
    forgejo_token="forgejo_token",
    forgejo_username="username",
    forgejo_password="password"
)
```

#### create_git_pull_request

**Old (GitHub-only):**
```python
await create_github_pull_request(
    title="Feature update",
    description="Description of the PR",
    head_branch="feature-branch",
    base_branch="main",
    github_token="ghp_xxx"
)
```

**New (Unified):**
```python
await create_git_pull_request(
    title="Feature update",
    description="Description of the PR",
    head_branch="feature-branch",
    base_branch="main",
    service_type="github",  # or "forgejo"
    github_token="ghp_xxx",  # For GitHub
    # OR for Forgejo:
    forgejo_token="forgejo_token"
)
```

## Configuration Changes

### Environment Variables

The configuration has been extended to support multiple Git services:

**New required configuration:**
```bash
# Git Services Configuration
ENABLE_GITHUB_TOOLS=True
DEFAULT_GIT_SERVICE=github

# GitHub Configuration (existing)
GITHUB_TOKEN=ghp_xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
GITHUB_DEFAULT_LABELS=["documentation","enhancement","bug"]

# Forgejo Configuration (new)
FORGEJO_BASE_URL=https://git.yourcompany.com
FORGEJO_TOKEN=your_forgejo_token_here
FORGEJO_USERNAME=your_username  # Alternative to token
FORGEJO_PASSWORD=your_password  # Alternative to token
FORGEJO_DEFAULT_LABELS=["feature","improvement"]
```

### MCPConfig Class

The `MCPConfig` class has been extended with new fields:

```python
# New fields in MCPConfig
default_git_service: str = "github"  # Default service when not specified
forgejo_base_url: Optional[str] = None
forgejo_token: Optional[str] = None
forgejo_username: Optional[str] = None
forgejo_password: Optional[str] = None
forgejo_default_labels: List[str] = []
```

## Migration Steps

### 1. Update Configuration

Add the new Git service configuration to your `.env` file:

```bash
# Set your default Git service
DEFAULT_GIT_SERVICE=github  # or "forgejo"

# Add Forgejo configuration if needed
FORGEJO_BASE_URL=https://your-forgejo-instance.com
FORGEJO_TOKEN=your_forgejo_token
```

### 2. Update Function Calls

Replace legacy GitHub tool calls with unified Git tool calls:

**Before:**
```python
# Legacy GitHub-only function calls
result = await create_github_issue(title="Test", description="Test issue")
```

**After:**
```python
# New unified function calls
result = await create_git_issue(
    title="Test", 
    description="Test issue",
    service_type="github"  # Explicit service selection
)
# OR use default service (configured via DEFAULT_GIT_SERVICE)
result = await create_git_issue(title="Test", description="Test issue")
```

### 3. Update API Calls

If you're using the REST API, update your endpoint calls:

**Before:**
```bash
curl -X POST "/api/v1/mcp/tools/call" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "create_github_issue",
    "arguments": {
      "title": "Test Issue",
      "description": "Test description"
    }
  }'
```

**After:**
```bash
curl -X POST "/api/v1/mcp/tools/call" \
  -H "Content-Type: application/json" \
  -d '{
    "tool_name": "create_git_issue",
    "arguments": {
      "title": "Test Issue", 
      "description": "Test description",
      "service_type": "github"
    }
  }'
```

### 4. Update LLM Function Calling

Update your LLM prompts and function definitions:

**Before:**
```python
functions = [
    {
        "name": "create_github_issue",
        "description": "Create a GitHub issue"
    }
]
```

**After:**
```python
functions = [
    {
        "name": "create_git_issue", 
        "description": "Create an issue on GitHub, Forgejo, or other Git services",
        "parameters": {
            "properties": {
                "service_type": {
                    "type": "string",
                    "enum": ["github", "forgejo"],
                    "description": "The Git service to use"
                }
            }
        }
    }
]
```

## Service-Specific Features

### GitHub

- Full GitHub API support
- OAuth token authentication
- GitHub-specific features (labels, assignees, etc.)

```python
await create_git_issue(
    title="GitHub Issue",
    description="Issue on GitHub",
    service_type="github",
    github_token="ghp_xxx",
    labels=["bug", "high-priority"],
    assignees=["github-user"]
)
```

### Forgejo

- Gitea-compatible API support
- Token or username/password authentication
- Self-hosted Git service support

```python
# Token authentication (recommended)
await create_git_issue(
    title="Forgejo Issue",
    description="Issue on Forgejo",
    service_type="forgejo", 
    forgejo_token="forgejo_token"
)

# Username/password authentication
await create_git_issue(
    title="Forgejo Issue",
    description="Issue on Forgejo",
    service_type="forgejo",
    forgejo_username="username",
    forgejo_password="password"
)
```

## Backward Compatibility

### Legacy Tool Support

The legacy GitHub tools are deprecated but still available for backward compatibility:

- `create_github_issue` ❌ **Deprecated** → Use `create_git_issue`
- `create_github_pull_request` ❌ **Deprecated** → Use `create_git_pull_request`  
- `check_github_repository_permissions` ❌ **Deprecated** → Use `check_git_repository_permissions`

### Migration Timeline

- **Current Version**: Both legacy and unified tools are available
- **Next Major Version**: Legacy tools will be removed
- **Recommendation**: Migrate to unified tools immediately

## Advanced Configuration

### Runtime Service Selection

You can override the configured default service at runtime:

```python
# Use GitHub even if Forgejo is the default
await create_git_issue(
    title="Issue",
    description="Description", 
    service_type="github",
    github_token="runtime_token"
)
```

### Mixed Environment Setup

Configure both GitHub and Forgejo for different repositories:

```bash
# Configuration supports both services
DEFAULT_GIT_SERVICE=github
GITHUB_TOKEN=ghp_xxx
FORGEJO_BASE_URL=https://forgejo.internal.com
FORGEJO_TOKEN=forgejo_xxx
```

```python
# Use different services for different operations
await create_git_issue(service_type="github", github_token="ghp_xxx")
await create_git_issue(service_type="forgejo", forgejo_token="forgejo_xxx")
```

## Testing

### Unit Tests

Update your unit tests to use the new unified interface:

```python
# Test with GitHub
@pytest.mark.asyncio
async def test_create_issue_github():
    result = await create_git_issue(
        title="Test",
        description="Test issue",
        service_type="github",
        github_token="test_token"
    )
    assert "Issue created successfully" in result

# Test with Forgejo
@pytest.mark.asyncio  
async def test_create_issue_forgejo():
    result = await create_git_issue(
        title="Test",
        description="Test issue", 
        service_type="forgejo",
        forgejo_token="test_token"
    )
    assert "Issue created successfully" in result
```

### Integration Tests

Test with both GitHub and Forgejo environments:

```python
@pytest.mark.parametrize("service_type,credentials", [
    ("github", {"github_token": "test_token"}),
    ("forgejo", {"forgejo_token": "test_token"}),
])
async def test_git_operations(service_type, credentials):
    result = await create_git_issue(
        title="Test Issue",
        description="Test description",
        service_type=service_type,
        **credentials
    )
    assert "created successfully" in result
```

## Troubleshooting

### Common Issues

1. **"Unsupported service type" error**
   - Ensure you're using a supported service: `"github"` or `"forgejo"`
   - Check that the service is properly configured

2. **Authentication failures**
   - Verify your tokens/credentials are correct and have necessary permissions
   - For Forgejo, ensure the base URL is accessible

3. **Legacy tool not found**
   - Update to use unified tools (`create_git_issue` instead of `create_github_issue`)
   - Check the migration table above for correct tool names

### Debug Configuration

Enable debug logging to troubleshoot configuration issues:

```bash
DEBUG=True
LOG_LEVEL=DEBUG
```

### Verify Configuration

Use the permissions check tool to verify your setup:

```python
result = await check_git_repository_permissions(
    service_type="github",
    github_token="your_token"
)
print(result)  # Should show your permissions
```

## Getting Help

- Check the [API documentation](./API_DOCUMENTATION.md) for detailed parameter information
- Review [test examples](../examples/) for usage patterns
- Open an issue on GitHub for bugs or feature requests

## Next Steps

1. **Immediate**: Update your configuration and function calls
2. **Soon**: Test with your preferred Git services 
3. **Future**: Consider adding support for additional Git services (GitLab, Bitbucket, etc.)

The unified Git tools provide a solid foundation for multi-service Git operations while maintaining the simplicity and power of the original GitHub-only tools.
