"""
LLM models.

This module contains Pydantic models for LLM services.
"""

from pydantic import BaseModel, Field
from typing import Dict, Any, List, Optional


class LLMQueryRequest(BaseModel):
    """
    Request model for LLM query.
    """

    prompt: str = Field(..., description="The prompt to send to the LLM")
    context_documents: Optional[List[str]] = Field(
        default=None, description="List of document paths to include in context"
    )
    provider: str = Field(
        default="openai", description="LLM provider to use (e.g., openai, anthropic)"
    )
    model: Optional[str] = Field(
        default=None,
        description="Specific model to use (if None, default for provider is used)",
    )
    options: Dict[str, Any] = Field(
        default_factory=dict, description="Additional options for the LLM provider"
    )
    disable_cache: bool = Field(
        default=False,
        description="If True, bypass cache and always make a fresh API call",
    )


class LLMUsage(BaseModel):
    """
    Usage information for LLM requests.
    """

    prompt_tokens: int = Field(default=0, description="Number of tokens in the prompt")
    completion_tokens: int = Field(
        default=0, description="Number of tokens in the completion"
    )
    total_tokens: int = Field(default=0, description="Total number of tokens used")


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


class LLMStreamResponse(BaseModel):
    """
    Response model for streaming LLM query.
    """

    model: str = Field(..., description="The model used for generation")
    provider: str = Field(..., description="The provider of the LLM")
    chunks: List[str] = Field(
        default_factory=list, description="Chunks of response received so far"
    )
    done: bool = Field(default=False, description="Whether the stream is complete")
    error: Optional[str] = Field(
        default=None, description="Error message if something went wrong"
    )
