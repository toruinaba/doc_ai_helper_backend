# Forgejo Setup Guide

This guide provides step-by-step instructions for setting up Forgejo connectivity with the doc_ai_helper_backend.

## Prerequisites

- Forgejo server running and accessible
- Admin access to create access tokens
- Python environment with required dependencies

## Step 1: Environment Configuration

### 1.1 Create Environment File

Copy the example environment file:
```bash
cp .env.example .env
```

### 1.2 Configure Required Variables

Edit the `.env` file with your Forgejo server details:

```env
# Forgejo Configuration
FORGEJO_BASE_URL=https://your-forgejo-server.com
FORGEJO_TOKEN=your_access_token_here

# Alternative: Basic Authentication (if token not available)
# FORGEJO_USERNAME=your_username
# FORGEJO_PASSWORD=your_password
```

### 1.3 Required Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `FORGEJO_BASE_URL` | Forgejo server base URL | Yes |
| `FORGEJO_TOKEN` | Forgejo access token | Yes* |
| `FORGEJO_USERNAME` | Username for basic auth | Optional* |
| `FORGEJO_PASSWORD` | Password for basic auth | Optional* |

*Either token OR username/password combination is required.

## Step 2: Create Forgejo Access Token

### 2.1 Access Token Creation

1. Log into your Forgejo instance
2. Go to **Settings** → **Applications** → **Access Tokens**
3. Click **Generate New Token**
4. Configure token permissions:
   - **Repository**: Read, Write (for file operations)
   - **Issues**: Read, Write (for issue creation)
   - **Pull Requests**: Read, Write (for PR creation)
5. Copy the generated token to your `.env` file

### 2.2 Token Permissions

Ensure your token has the following scopes:
- `repo` - Full repository access
- `write:issue` - Create and modify issues
- `write:pull_request` - Create and modify pull requests

## Step 3: Test Connection

### 3.1 Basic Connection Test

Run the connection test script:
```bash
cd examples
python setup_forgejo_step_by_step.py
```

### 3.2 Manual Testing

Test the connection manually using the service:

```python
from doc_ai_helper_backend.services.git.forgejo_service import ForgejoService
from doc_ai_helper_backend.core.config import settings

# Create service instance
service = ForgejoService(
    base_url=settings.forgejo_base_url,
    access_token=settings.forgejo_token,
    username=settings.forgejo_username,
    password=settings.forgejo_password,
)

# Test basic connectivity
try:
    # Test user info
    user_info = await service.get_user_info()
    print(f"Connected as: {user_info.get('login', 'Unknown')}")
    
    # Test repository listing
    repos = await service.list_repositories()
    print(f"Found {len(repos)} repositories")
    
except Exception as e:
    print(f"Connection failed: {e}")
```

## Step 4: Repository Access Test

### 4.1 Test Repository Operations

Test basic repository operations:

```python
# Test repository structure
try:
    structure = await service.get_repository_structure("owner", "repo")
    print(f"Repository structure retrieved: {len(structure.files)} files")
except Exception as e:
    print(f"Repository access failed: {e}")
```

### 4.2 Test File Content Access

```python
# Test file content retrieval
try:
    content = await service.get_file_content("owner", "repo", "README.md")
    print(f"File content retrieved: {len(content)} characters")
except Exception as e:
    print(f"File access failed: {e}")
```

## Step 5: MCP Integration Test

### 5.1 Test MCP Tools with Forgejo

```python
from doc_ai_helper_backend.services.mcp.tools.git_tools import (
    get_repository_info,
    get_file_content,
    create_issue,
    create_pull_request
)

# Test repository information
repo_info = await get_repository_info(
    service="forgejo",
    owner="your-owner",
    repository="your-repo",
    forgejo_base_url="https://your-forgejo-server.com",
    forgejo_token="your-token"
)
print(f"Repository info: {repo_info}")
```

## Step 6: Troubleshooting

### 6.1 Common Issues

#### Connection Refused
- **Issue**: Cannot connect to Forgejo server
- **Solution**: Check if FORGEJO_BASE_URL is correct and server is accessible

#### Authentication Failed
- **Issue**: 401 Unauthorized error
- **Solution**: Verify access token or username/password in .env file

#### Permission Denied
- **Issue**: 403 Forbidden error
- **Solution**: Check token permissions and repository access rights

#### SSL Certificate Issues
- **Issue**: SSL verification failed
- **Solution**: For self-hosted instances, you may need to configure SSL settings

### 6.2 Debug Mode

Enable debug logging for detailed error information:

```python
import logging
logging.getLogger("doc_ai_helper_backend").setLevel(logging.DEBUG)
```

### 6.3 Manual API Testing

Test Forgejo API directly using curl:

```bash
# Test API access
curl -H "Authorization: token YOUR_TOKEN" \
     https://your-forgejo-server.com/api/v1/user

# Test repository access
curl -H "Authorization: token YOUR_TOKEN" \
     https://your-forgejo-server.com/api/v1/repos/OWNER/REPO
```

## Step 7: Production Configuration

### 7.1 Security Considerations

- Store tokens securely (use environment variables or secret management)
- Use tokens with minimal required permissions
- Regularly rotate access tokens
- Monitor token usage and access logs

### 7.2 Performance Optimization

- Enable caching for frequently accessed repositories
- Use connection pooling for multiple requests
- Configure appropriate timeout values

### 7.3 Monitoring

Set up monitoring for:
- API rate limits
- Connection errors
- Token expiration
- Repository access patterns

## Additional Resources

- [Forgejo API Documentation](https://forgejo.org/docs/latest/api/)
- [Access Token Management](https://forgejo.org/docs/latest/user/oauth2-provider/)
- [MCP Integration Guide](./MCP_GIT_ABSTRACTION_DESIGN.md)
- [Git Tools Documentation](./MCP_GIT_TOOLS_MIGRATION_GUIDE.md)
