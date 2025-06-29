"""
Model Context Protocol (MCP) adapter.

⚠️  DEPRECATED: This module is deprecated and will be removed in future versions.
Use the new FastMCP-based implementation in doc_ai_helper_backend.services.mcp instead.

This module provides utilities to convert documents to MCP format and
optimize context for LLM queries.
"""

from typing import Dict, Any, List, Optional
import json
import warnings

from doc_ai_helper_backend.models.document import DocumentResponse


class MCPAdapter:
    """
    Model Context Protocol (MCP) adapter.

    ⚠️  DEPRECATED: This class is deprecated. Use the new FastMCP server implementation instead.
    See doc_ai_helper_backend.services.mcp for the new implementation.

    This class provides methods to convert documents to MCP format and optimize
    context for LLM queries.
    """

    def __init__(self):
        """Initialize MCPAdapter with deprecation warning."""
        warnings.warn(
            "MCPAdapter is deprecated and will be removed in future versions. "
            "Use doc_ai_helper_backend.services.mcp instead.",
            DeprecationWarning,
            stacklevel=2,
        )

    @staticmethod
    def convert_document_to_context(document: DocumentResponse) -> Dict[str, Any]:
        """
        Convert a document to MCP context format.

        ⚠️  DEPRECATED: Use doc_ai_helper_backend.services.mcp.call_tool('extract_document_context', ...) instead.

        Args:
            document: The document to convert

        Returns:
            Dict[str, Any]: The document in MCP context format
        """
        warnings.warn(
            "convert_document_to_context is deprecated. "
            "Use the new MCP server tools instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        # Basic document context
        context = {
            "type": "document",
            "content": document.content.text,
            "metadata": {
                "title": document.metadata.title or document.name,
                "path": document.path,
                "repository": f"{document.owner}/{document.repository}",
                "service": document.service,
                "format": (
                    "markdown"
                    if document.type.value == "markdown"
                    else document.type.value
                ),
            },
        }

        # Add frontmatter if available
        if hasattr(document.metadata, "frontmatter") and document.metadata.frontmatter:
            context["metadata"]["frontmatter"] = document.metadata.frontmatter

        # Add links if available
        if document.links:
            context["links"] = [
                {
                    "text": link.text,
                    "url": link.url,
                    "is_external": link.is_external,
                    "is_image": link.is_image,
                }
                for link in document.links
            ]

        return context

    @staticmethod
    def optimize_context(
        contexts: List[Dict[str, Any]],
        max_tokens: int,
        current_prompt_tokens: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Optimize a list of contexts to fit within token limit.

        ⚠️  DEPRECATED: Use the new MCP server tools for context optimization instead.

        This method applies various strategies to reduce context size while
        preserving the most important information.

        Args:
            contexts: List of context items to optimize
            max_tokens: Maximum tokens allowed
            current_prompt_tokens: Current tokens used by prompt (if any)

        Returns:
            List[Dict[str, Any]]: Optimized context list
        """
        warnings.warn(
            "optimize_context is deprecated. "
            "Use the new MCP server tools for context optimization instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        if not contexts:
            return []

        # Estimate available tokens
        available_tokens = max_tokens
        if current_prompt_tokens:
            available_tokens -= current_prompt_tokens

        # If we have enough tokens, return the original contexts
        total_estimated_tokens = sum(
            len(json.dumps(ctx)) // 4  # Rough estimation: 4 characters ~= 1 token
            for ctx in contexts
        )
        if total_estimated_tokens <= available_tokens:
            return contexts

        # Otherwise, apply optimization strategies

        # Strategy 1: Truncate content of each document to fit proportionally
        token_per_ctx = available_tokens // len(contexts)
        optimized_contexts = []

        for ctx in contexts:
            optimized_ctx = ctx.copy()

            # Estimate context metadata tokens
            ctx_without_content = ctx.copy()
            if "content" in ctx_without_content:
                ctx_without_content["content"] = ""
            metadata_tokens = len(json.dumps(ctx_without_content)) // 4

            # Calculate available tokens for content
            content_tokens = token_per_ctx - metadata_tokens
            if content_tokens <= 0:
                content_tokens = 10  # Minimum content

            # Truncate content if needed
            if "content" in ctx and isinstance(ctx["content"], str):
                content = ctx["content"]
                estimated_content_tokens = len(content) // 4

                if estimated_content_tokens > content_tokens:
                    # Simple truncation - in a real implementation,
                    # more sophisticated truncation would be used
                    ratio = content_tokens / estimated_content_tokens
                    char_limit = int(len(content) * ratio)
                    optimized_ctx["content"] = content[:char_limit] + "..."

            optimized_contexts.append(optimized_ctx)

        return optimized_contexts
