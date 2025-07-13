"""
LLM models.

This module contains Pydantic models for LLM services.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Dict, Any, List, Optional, Union, Literal, TYPE_CHECKING
from enum import Enum
from datetime import datetime

# Forward references for repository context models
if TYPE_CHECKING:
    from .repository_context import RepositoryContext, DocumentMetadata


class MessageRole(str, Enum):
    """
    Role in a conversation message.
    """

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class MessageItem(BaseModel):
    """
    A single message in a conversation.
    """

    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    timestamp: Optional[datetime] = Field(
        default_factory=datetime.now,
        description="Timestamp when the message was created",
    )


# Legacy monolithic LLMQueryRequest removed - now using structured LLMQueryRequest as the main interface


class LLMUsage(BaseModel):
    """
    Usage information for LLM requests.
    """

    prompt_tokens: int = Field(default=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(
        default=0, description="Number of tokens in the completion"
    )
    total_tokens: int = Field(default=0, description="Total number of tokens used")


# Function Calling関連のモデル


class FunctionParameter(BaseModel):
    """
    Function parameter definition for function calling.
    """

    type: str = Field(
        ..., description="Parameter type (string, number, boolean, object, array)"
    )
    description: Optional[str] = Field(
        default=None, description="Parameter description"
    )
    enum: Optional[List[str]] = Field(
        default=None, description="Allowed values for the parameter"
    )
    items: Optional[Dict[str, Any]] = Field(
        default=None, description="Item type for array parameters"
    )
    properties: Optional[Dict[str, "FunctionParameter"]] = Field(
        default=None, description="Properties for object parameters"
    )
    required: Optional[List[str]] = Field(
        default=None, description="Required properties for object parameters"
    )


class FunctionDefinition(BaseModel):
    """
    Function definition for function calling.
    """

    name: str = Field(..., description="Function name")
    description: Optional[str] = Field(default=None, description="Function description")
    parameters: Optional[Dict[str, Any]] = Field(
        default=None, description="Function parameters schema"
    )


class FunctionCall(BaseModel):
    """
    Function call details from LLM response.
    """

    name: str = Field(..., description="Function name to call")
    arguments: str = Field(..., description="Function arguments as JSON string")


class ToolCall(BaseModel):
    """
    Tool call details from LLM response.
    """

    id: str = Field(..., description="Tool call ID")
    type: Literal["function"] = Field(default="function", description="Tool call type")
    function: FunctionCall = Field(..., description="Function call details")


class ToolChoice(BaseModel):
    """
    Tool choice strategy for function calling.
    """

    type: Literal["auto", "none", "required", "function"] = Field(
        ..., description="Tool choice strategy"
    )
    function: Optional[Dict[str, str]] = Field(
        default=None, description="Function specification for 'function' type"
    )


class LLMResponse(BaseModel):
    """
    Response model for LLM query.
    """

    content: str = Field(..., description="The content returned by the LLM")
    model: str = Field(..., description="The model used for generation")
    provider: str = Field(..., description="The provider of the LLM")
    usage: LLMUsage = Field(
        default_factory=LLMUsage, description="Token usage information"
    )
    raw_response: Dict[str, Any] = Field(
        default_factory=dict, description="Raw response from the provider"
    )
    optimized_conversation_history: Optional[List[MessageItem]] = Field(
        default=None,
        description="Optimized conversation history that frontend should use for next request",
    )
    history_optimization_info: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Information about how the conversation history was optimized",
    )
    tool_calls: Optional[List[ToolCall]] = Field(
        default=None,
        description="Tool calls requested by the LLM (for function calling)",
    )
    tool_execution_results: Optional[List[Dict[str, Any]]] = Field(
        default=None,
        description="Results of executed tool calls",
    )
    original_tool_calls: Optional[List[ToolCall]] = Field(
        default=None,
        description="Original tool calls from the initial LLM response (for debugging)",
    )


class ProviderCapabilities(BaseModel):
    """
    Capabilities of an LLM provider.
    """

    available_models: List[str] = Field(..., description="List of available models")
    max_tokens: Dict[str, int] = Field(..., description="Maximum tokens per model")
    supports_streaming: bool = Field(
        default=False, description="Whether the provider supports streaming"
    )
    supports_function_calling: bool = Field(
        default=False, description="Whether the provider supports function calling"
    )
    supports_vision: bool = Field(
        default=False, description="Whether the provider supports vision/images"
    )


class TemplateVariable(BaseModel):
    """
    Variable definition for prompt templates.
    """

    name: str = Field(..., description="Variable name")
    description: str = Field(default="", description="Variable description")
    required: bool = Field(default=True, description="Whether the variable is required")
    default: Optional[Any] = Field(
        default=None, description="Default value for the variable"
    )


class PromptTemplate(BaseModel):
    """
    Prompt template definition.
    """

    id: str = Field(..., description="Template identifier")
    name: str = Field(..., description="Template name")
    description: str = Field(default="", description="Template description")
    template: str = Field(
        ..., description="Template string with {{variable}} placeholders"
    )
    variables: List[TemplateVariable] = Field(
        default_factory=list, description="Variables used in the template"
    )


class LLMStreamChunk(BaseModel):
    """
    Streaming chunk response from LLM.
    """

    text: str = Field(..., description="The chunk of text from the LLM")
    done: bool = Field(default=False, description="Whether this is the last chunk")
    error: Optional[str] = Field(
        default=None, description="Error message, if any occurred during streaming"
    )




class ToolParameter(BaseModel):
    """
    Parameter definition for an MCP tool.
    """

    name: str = Field(..., description="Parameter name")
    type: str = Field(..., description="Parameter type")
    description: Optional[str] = Field(None, description="Parameter description")
    required: bool = Field(False, description="Whether the parameter is required")
    default: Optional[Any] = Field(None, description="Default value if any")


class MCPToolInfo(BaseModel):
    """
    Information about an MCP tool.
    """

    name: str = Field(..., description="Tool name")
    description: Optional[str] = Field(None, description="Tool description")
    parameters: List[ToolParameter] = Field(
        default_factory=list, description="Tool parameters"
    )
    category: Optional[str] = Field(
        None, description="Tool category (document, feedback, analysis, etc.)"
    )
    enabled: bool = Field(True, description="Whether the tool is enabled")


class MCPToolsResponse(BaseModel):
    """
    Response model for MCP tools list.
    """

    tools: List[MCPToolInfo] = Field(..., description="List of available MCP tools")
    total_count: int = Field(..., description="Total number of available tools")
    categories: List[str] = Field(..., description="Available tool categories")
    server_info: Dict[str, Any] = Field(
        default_factory=dict, description="MCP server information"
    )


# === New Refactored Request Models ===

class CoreQueryRequest(BaseModel):
    """
    Essential query parameters for LLM requests.
    
    This model contains only the fundamental parameters needed for any LLM query.
    """
    
    prompt: str = Field(..., min_length=1, description="The prompt to send to the LLM")
    provider: str = Field(
        default="openai", description="LLM provider to use (e.g., openai, anthropic)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use (if None, default for provider is used)",
    )
    conversation_history: Optional[List[MessageItem]] = Field(
        default=None, description="Previous messages in the conversation for context"
    )

    @field_validator('prompt')
    @classmethod
    def validate_prompt(cls, v):
        """Validate prompt is not empty or whitespace only."""
        if not v or not v.strip():
            raise ValueError("Prompt cannot be empty or contain only whitespace")
        return v.strip()


class ToolConfiguration(BaseModel):
    """
    Configuration for tool/function calling capabilities.
    
    This model groups all parameters related to LLM tool execution and function calling.
    """
    
    enable_tools: bool = Field(
        default=False, description="Enable automatic function calling/tool execution"
    )
    tool_choice: Optional[str] = Field(
        default="auto",
        description="Tool selection strategy: auto, none, required, or specific function name",
    )
    complete_tool_flow: bool = Field(
        default=True,
        description="If True, use complete Function Calling flow (tool execution + LLM followup). If False, use legacy flow (direct tool results)",
    )


class DocumentContext(BaseModel):
    """
    Document integration context for repository-aware queries.
    
    This model groups all parameters related to document and repository context.
    """
    
    repository_context: Optional["RepositoryContext"] = Field(
        default=None, description="Repository context from current document view"
    )
    document_metadata: Optional["DocumentMetadata"] = Field(
        default=None, description="Metadata of currently displayed document"
    )
    auto_include_document: bool = Field(
        default=True,
        description="Whether to automatically fetch document content from repository_context and include in conversation history for initial requests"
    )
    context_documents: Optional[List[str]] = Field(
        default=None, description="List of document paths to include in context"
    )


class ProcessingOptions(BaseModel):
    """
    Processing and caching options for LLM requests.
    
    This model groups parameters that control how the request is processed and cached.
    """
    
    disable_cache: bool = Field(
        default=False,
        description="If True, bypass cache and always make a fresh API call",
    )
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Additional options for the LLM provider"
    )


class LLMQueryRequest(BaseModel):
    """
    LLM query request with structured, grouped parameters.
    
    This model provides a cleaner, more maintainable structure by grouping
    related parameters into focused sub-models for better organization
    and easier maintenance.
    """
    
    query: CoreQueryRequest = Field(..., description="Core query parameters")
    tools: Optional[ToolConfiguration] = Field(
        default=None, description="Tool/function calling configuration"
    )
    document: Optional[DocumentContext] = Field(
        default=None, description="Document integration context"
    )
    processing: Optional[ProcessingOptions] = Field(
        default=None, description="Processing and caching options"
    )



# Update forward references for repository context models
def update_forward_refs():
    """Update forward references after all models are imported."""
    try:
        from .repository_context import RepositoryContext, DocumentMetadata

        LLMQueryRequest.model_rebuild()
        DocumentContext.model_rebuild()
    except ImportError:
        # Repository context models not yet available
        pass


# Call update function to resolve forward references
update_forward_refs()
