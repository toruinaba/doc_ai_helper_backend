# MCP Tools API Usage Examples

This document provides examples of how to use the MCP Tools API endpoints.

## Overview

The MCP Tools API provides endpoints to:
1. Get a list of all available MCP tools with detailed information
2. Get specific information about individual tools
3. Understand tool parameters and usage

## Endpoints

### 1. Get All MCP Tools

**Endpoint:** `GET /api/v1/llm/tools`

**Description:** Returns a comprehensive list of all available MCP tools with their descriptions, parameters, and categorization.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/llm/tools" \
  -H "Accept: application/json"
```

**Example Response:**
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
    },
    {
      "name": "create_github_issue",
      "description": "Create a new GitHub issue in a repository",
      "parameters": [
        {
          "name": "repository",
          "type": "str",
          "description": "Repository in format 'owner/repo'",
          "required": true,
          "default": null
        },
        {
          "name": "title",
          "type": "str",
          "description": "Issue title",
          "required": true,
          "default": null
        },
        {
          "name": "description",
          "type": "str",
          "description": "Issue description",
          "required": true,
          "default": null
        }
      ],
      "category": "github",
      "enabled": true
    }
  ],
  "total_count": 16,
  "categories": ["analysis", "document", "feedback", "github", "utility"],
  "server_info": {
    "name": "Document AI Helper MCP Server",
    "version": "1.0.0",
    "description": "Document AI Helper MCP Server",
    "enabled_features": {
      "document_tools": true,
      "feedback_tools": true,
      "analysis_tools": true,
      "github_tools": true,
      "utility_tools": true
    }
  }
}
```

### 2. Get Specific Tool Information

**Endpoint:** `GET /api/v1/llm/tools/{tool_name}`

**Description:** Returns detailed information about a specific MCP tool.

**Example Request:**
```bash
curl -X GET "http://localhost:8000/api/v1/llm/tools/analyze_document_structure" \
  -H "Accept: application/json"
```

**Example Response:**
```json
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
```

## Tool Categories

The API organizes tools into the following categories:

### Document Tools
- `analyze_document_structure` - Analyze document structure and organization
- `extract_document_keywords` - Extract keywords and key phrases
- `check_document_links` - Check and validate document links
- `summarize_document_sections` - Generate section summaries

### Feedback Tools
- `collect_user_feedback` - Collect and store user feedback
- `generate_feedback_from_conversation` - Generate feedback from conversation history
- `create_improvement_proposal` - Create improvement proposals
- `analyze_conversation_patterns` - Analyze conversation patterns

### Analysis Tools
- `analyze_document_quality` - Analyze document quality
- `extract_document_topics` - Extract main topics from content
- `check_document_completeness` - Check document completeness

### GitHub Tools
- `create_github_issue` - Create GitHub issues
- `create_github_pull_request` - Create pull requests
- `check_github_repository_permissions` - Check repository permissions

### Utility Tools
- `get_current_time` - Get current date/time
- `count_text_characters` - Count text statistics
- `validate_email_format` - Validate email formats
- `generate_random_data` - Generate test data

## Frontend Integration Examples

### React/JavaScript Example

```javascript
// Get all tools
async function getAllMCPTools() {
  try {
    const response = await fetch('/api/v1/llm/tools');
    const data = await response.json();
    return data;
  } catch (error) {
    console.error('Error fetching MCP tools:', error);
    return null;
  }
}

// Get specific tool
async function getMCPTool(toolName) {
  try {
    const response = await fetch(`/api/v1/llm/tools/${toolName}`);
    const data = await response.json();
    return data;
  } catch (error) {
    console.error(`Error fetching tool ${toolName}:`, error);
    return null;
  }
}

// Display tools in UI
async function displayTools() {
  const toolsData = await getAllMCPTools();
  if (!toolsData) return;
  
  const toolsContainer = document.getElementById('tools-container');
  
  toolsData.categories.forEach(category => {
    const categoryTools = toolsData.tools.filter(tool => tool.category === category);
    
    const categoryDiv = document.createElement('div');
    categoryDiv.innerHTML = `
      <h3>${category.charAt(0).toUpperCase() + category.slice(1)} Tools</h3>
      <div class="tools-grid">
        ${categoryTools.map(tool => `
          <div class="tool-card">
            <h4>${tool.name}</h4>
            <p>${tool.description || 'No description available'}</p>
            <div class="parameters">
              <strong>Parameters:</strong>
              <ul>
                ${tool.parameters.map(param => `
                  <li>
                    <code>${param.name}</code> (${param.type})
                    ${param.required ? ' <span class="required">*</span>' : ''}
                    ${param.description ? ` - ${param.description}` : ''}
                  </li>
                `).join('')}
              </ul>
            </div>
          </div>
        `).join('')}
      </div>
    `;
    toolsContainer.appendChild(categoryDiv);
  });
}
```

### Python Client Example

```python
import requests

class MCPToolsClient:
    def __init__(self, base_url="http://localhost:8000"):
        self.base_url = base_url
    
    def get_all_tools(self):
        """Get all available MCP tools."""
        response = requests.get(f"{self.base_url}/api/v1/llm/tools")
        response.raise_for_status()
        return response.json()
    
    def get_tool(self, tool_name):
        """Get specific tool information."""
        response = requests.get(f"{self.base_url}/api/v1/llm/tools/{tool_name}")
        response.raise_for_status()
        return response.json()
    
    def get_tools_by_category(self, category):
        """Get tools filtered by category."""
        all_tools = self.get_all_tools()
        return [tool for tool in all_tools["tools"] if tool["category"] == category]
    
    def print_tool_summary(self):
        """Print a summary of available tools."""
        data = self.get_all_tools()
        
        print(f"MCP Server: {data['server_info']['name']}")
        print(f"Total Tools: {data['total_count']}")
        print(f"Categories: {', '.join(data['categories'])}")
        print()
        
        for category in data['categories']:
            category_tools = [t for t in data['tools'] if t['category'] == category]
            print(f"{category.upper()} ({len(category_tools)} tools):")
            for tool in category_tools:
                print(f"  - {tool['name']}: {tool['description']}")
            print()

# Usage
client = MCPToolsClient()
client.print_tool_summary()

# Get specific tool
document_analyzer = client.get_tool("analyze_document_structure")
print(f"Tool: {document_analyzer['name']}")
print(f"Parameters: {len(document_analyzer['parameters'])}")
```

## Error Handling

The API returns appropriate HTTP status codes:

- `200 OK` - Successful request
- `404 Not Found` - Tool not found (for specific tool requests)
- `500 Internal Server Error` - Server error

Example error response:
```json
{
  "detail": "Tool 'nonexistent_tool' not found"
}
```

## Use Cases

1. **Frontend Tool Discovery**: Frontend applications can dynamically discover available tools and present them to users.

2. **Dynamic UI Generation**: Create forms and interfaces based on tool parameters.

3. **API Documentation**: Generate interactive API documentation for available tools.

4. **Tool Validation**: Validate tool names and parameters before making function calls.

5. **Feature Detection**: Check which tool categories are enabled on the server.

6. **Development/Debugging**: Inspect available tools during development and testing.
