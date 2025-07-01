# Forgejo Server Integration Checklist

## 🎯 **Overview**
This checklist ensures proper configuration for connecting to your Forgejo server.

## ✅ **Pre-requisites**

### Forgejo Server Requirements
- [ ] Forgejo server is running and accessible
- [ ] You have user account access
- [ ] Server supports API access (v1 API)
- [ ] Network connectivity from your application server

### Authentication Requirements
Choose ONE of the following:

**Option A: Access Token (Recommended)**
- [ ] Access token created in Forgejo
- [ ] Token has required permissions (`repository:read`, `contents:read`)
- [ ] Token is not expired

**Option B: Basic Authentication**
- [ ] Username and password available
- [ ] Account has repository access permissions

## 🔧 **Environment Configuration**

### Required Environment Variables

```bash
# Base URL (REQUIRED)
FORGEJO_BASE_URL=https://your-forgejo-server.com

# Authentication (choose one method)
# Method 1: Access Token (RECOMMENDED)
FORGEJO_TOKEN=your_forgejo_access_token_here

# Method 2: Basic Auth (alternative)
FORGEJO_USERNAME=your_username
FORGEJO_PASSWORD=your_password
```

### Optional Environment Variables

```bash
# SSL Certificate Verification
FORGEJO_VERIFY_SSL=True  # Set to False for self-signed certificates

# Connection Settings
FORGEJO_TIMEOUT=30       # Connection timeout in seconds
FORGEJO_MAX_RETRIES=3    # Maximum retry attempts

# Service Configuration
DEFAULT_GIT_SERVICE=forgejo                        # Set Forgejo as default
SUPPORTED_GIT_SERVICES=["github", "forgejo", "mock"]  # Enable Forgejo support
```

## 🔑 **Creating Forgejo Access Token**

### Step-by-Step Instructions

1. **Log into Forgejo**
   - [ ] Navigate to your Forgejo server
   - [ ] Sign in with your credentials

2. **Access Token Settings**
   - [ ] Go to **User Settings** (click your avatar)
   - [ ] Navigate to **Applications** tab
   - [ ] Find **Access Tokens** section

3. **Create New Token**
   - [ ] Click **Create Token** or **Generate Token**
   - [ ] Enter token name: `doc_ai_helper_backend`
   - [ ] Select required scopes:
     - [ ] `repository` or `repo` (repository access)
     - [ ] `read:repository` (read repository contents)
     - [ ] `metadata:read` (read metadata)

4. **Save Token**
   - [ ] Copy the generated token immediately
   - [ ] Store securely (it won't be shown again)
   - [ ] Add to your `.env` file as `FORGEJO_TOKEN`

## 🌐 **Network Configuration**

### URL Format Validation
- [ ] Base URL is accessible via HTTP/HTTPS
- [ ] URL format: `https://your-server.com` (no trailing slash)
- [ ] API endpoint available at: `https://your-server.com/api/v1`

### SSL/TLS Configuration
- [ ] Valid SSL certificate (for HTTPS)
- [ ] OR `FORGEJO_VERIFY_SSL=False` for self-signed certificates

### Firewall/Network Access
- [ ] Outbound HTTPS (443) or HTTP (80) access allowed
- [ ] No proxy blocking Git API endpoints
- [ ] DNS resolution working for your Forgejo server

## 🧪 **Testing Configuration**

### Automated Tests

```bash
# Quick connection test
python examples/test_forgejo_connection.py

# Step-by-step setup guide
python examples/setup_forgejo_step_by_step.py
```

### Manual Verification Steps

1. **Test Base URL**
   ```bash
   curl https://your-forgejo-server.com/api/v1/version
   ```
   - [ ] Returns version information

2. **Test Authentication**
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
        https://your-forgejo-server.com/api/v1/user
   ```
   - [ ] Returns user information

3. **Test Repository Access**
   ```bash
   curl -H "Authorization: token YOUR_TOKEN" \
        https://your-forgejo-server.com/api/v1/repos/OWNER/REPO
   ```
   - [ ] Returns repository information

## 🐛 **Troubleshooting Common Issues**

### Connection Issues
- **Problem**: Connection timeout or refused
- **Solutions**:
  - [ ] Verify `FORGEJO_BASE_URL` is correct
  - [ ] Check network connectivity
  - [ ] Verify Forgejo server is running
  - [ ] Check firewall rules

### Authentication Issues
- **Problem**: 401 Unauthorized or 403 Forbidden
- **Solutions**:
  - [ ] Verify token is correct and not expired
  - [ ] Check token permissions/scopes
  - [ ] Regenerate access token
  - [ ] Try basic auth as alternative

### API Issues
- **Problem**: API endpoints not found (404)
- **Solutions**:
  - [ ] Verify Forgejo version supports v1 API
  - [ ] Check URL format (no extra paths)
  - [ ] Confirm API is enabled on server

### SSL/Certificate Issues
- **Problem**: SSL verification errors
- **Solutions**:
  - [ ] Set `FORGEJO_VERIFY_SSL=False` for testing
  - [ ] Install proper SSL certificates
  - [ ] Use HTTP instead of HTTPS (if appropriate)

## 📚 **Integration Examples**

### Python Code Example
```python
from doc_ai_helper_backend.services.git.factory import GitServiceFactory

# Create Forgejo service
service = GitServiceFactory.create("forgejo")

# Test connection
connection_result = await service.test_connection()
print(f"Status: {connection_result['status']}")

# Access repository
document = await service.get_document("owner", "repo", "README.md")
print(f"Document: {document.name}")
```

### Configuration Example
```bash
# Copy the example file and customize
cp .env.example .env

# Production configuration
FORGEJO_BASE_URL=https://git.company.com
FORGEJO_TOKEN=glpat-xxxxxxxxxxxxxxxxxxxx
FORGEJO_VERIFY_SSL=True
FORGEJO_TIMEOUT=30

# Development configuration
FORGEJO_BASE_URL=http://localhost:3000
FORGEJO_TOKEN=test_token_here
FORGEJO_VERIFY_SSL=False
FORGEJO_TIMEOUT=10
```

## ✅ **Final Verification**

After completing all steps:
- [ ] All environment variables set correctly
- [ ] Authentication working
- [ ] Basic API calls successful
- [ ] Repository access confirmed
- [ ] Integration tests passing

## 📞 **Support Resources**

- **Forgejo Documentation**: https://forgejo.org/docs/
- **API Documentation**: https://your-forgejo-server.com/api/swagger
- **Project Issues**: Create issue in doc_ai_helper_backend repository
