"""
Compatibility layer for existing MCPAdapter usage.

This module provides a compatibility layer to help migrate from the old MCPAdapter
to the new FastMCP-based implementation.
"""

import warnings
from typing import Dict, Any, List, Optional
import asyncio

from doc_ai_helper_backend.models.document import DocumentResponse
from doc_ai_helper_backend.services.mcp import get_mcp_server


class MCPAdapterCompat:
    """
    Compatibility layer for existing MCPAdapter usage.

    This class provides the same interface as the old MCPAdapter but uses
    the new FastMCP server implementation under the hood.
    """

    def __init__(self):
        """Initialize compatibility layer with deprecation warning."""
        warnings.warn(
            "MCPAdapterCompat is a temporary compatibility layer. "
            "Please migrate to using doc_ai_helper_backend.services.mcp directly.",
            DeprecationWarning,
            stacklevel=2,
        )
        self.mcp_server = get_mcp_server()

    def convert_document_to_context(self, document: DocumentResponse) -> Dict[str, Any]:
        """
        Convert a document to MCP context format using new implementation.

        Args:
            document: The document to convert

        Returns:
            Dict[str, Any]: The document in MCP context format
        """
        warnings.warn(
            "convert_document_to_context is deprecated. "
            "Use doc_ai_helper_backend.services.mcp.call_tool('extract_document_context', ...) instead.",
            DeprecationWarning,
            stacklevel=2,
        )

        # Convert DocumentResponse to parameters for new MCP tool
        try:
            # Run async function in sync context
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            result = loop.run_until_complete(
                self.mcp_server.call_tool(
                    "extract_document_context",
                    content=document.content.text,
                    title=document.metadata.title or document.name,
                    path=document.path,
                    repository=f"{document.owner}/{document.repository}",
                    metadata={
                        "service": document.service,
                        "ref": document.ref,
                        "frontmatter": getattr(document.metadata, "frontmatter", {}),
                        "links": (
                            [link.dict() for link in document.links]
                            if document.links
                            else []
                        ),
                    },
                )
            )

            loop.close()
            return result

        except Exception as e:
            # Fallback to basic conversion if new implementation fails
            return {
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
                "error": f"New implementation failed: {str(e)}",
            }

    def optimize_context(
        self,
        contexts: List[Dict[str, Any]],
        max_tokens: int,
        current_prompt_tokens: Optional[int] = None,
    ) -> List[Dict[str, Any]]:
        """
        Optimize a list of contexts to fit within token limit.

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

        # Simple fallback optimization
        if not contexts:
            return []

        # Estimate available tokens
        available_tokens = max_tokens
        if current_prompt_tokens:
            available_tokens -= current_prompt_tokens

        # Simple truncation if needed
        total_estimated_tokens = sum(
            len(str(ctx)) // 4  # Rough estimation: 4 characters ~= 1 token
            for ctx in contexts
        )

        if total_estimated_tokens <= available_tokens:
            return contexts

        # Proportional truncation
        token_per_ctx = available_tokens // len(contexts)
        optimized_contexts = []

        for ctx in contexts:
            optimized_ctx = ctx.copy()
            if "content" in ctx and isinstance(ctx["content"], str):
                content = ctx["content"]
                estimated_content_tokens = len(content) // 4

                if estimated_content_tokens > token_per_ctx:
                    ratio = token_per_ctx / estimated_content_tokens
                    char_limit = int(len(content) * ratio)
                    optimized_ctx["content"] = content[:char_limit] + "..."

            optimized_contexts.append(optimized_ctx)

        return optimized_contexts


# Create a global compatibility instance for easy migration
mcp_adapter_compat = MCPAdapterCompat()
