"""
LLM API endpoints.

This module provides the API endpoints for LLM functionality.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sse_starlette.sse import EventSourceResponse

from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    LLMResponse,
    PromptTemplate,
    LLMStreamChunk,
    MCPToolsResponse,
    MCPToolInfo,
    ToolParameter,
)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.core.exceptions import (
    LLMServiceException,
    TemplateNotFoundError,
    TemplateSyntaxError,
)
from doc_ai_helper_backend.api.dependencies import get_llm_service

logger = logging.getLogger(__name__)


router = APIRouter()


@router.post(
    "/query",
    response_model=LLMResponse,
    summary="Query LLM",
    description="Send a query to an LLM with optional document context",
)
async def query_llm(
    request: LLMQueryRequest,
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Send a query to an LLM.

    Args:
        request: The query request containing prompt and options
        llm_service: The LLM service to use (injected)

    Returns:
        LLMResponse: The response from the LLM
    """

    try:
        # Use the injected LLM service instead of creating a new one

        # Prepare options
        options = request.options or {}
        if request.model:
            options["model"] = request.model

        # Set cache control flag
        if request.disable_cache:
            options["disable_cache"] = True

        # Process context documents if provided
        if request.context_documents:
            options["context_documents"] = (
                request.context_documents
            )  # Check if tools/function calling is enabled
        if request.enable_tools:
            # Get available tools from the LLM service
            available_tools = await llm_service.get_available_functions()
            # Convert tool_choice string to ToolChoice object
            tool_choice = None
            if request.tool_choice:
                from doc_ai_helper_backend.models.llm import ToolChoice

                if request.tool_choice in ["auto", "none", "required"]:
                    tool_choice = ToolChoice(type=request.tool_choice)  # type: ignore
                else:
                    # Assume it's a specific function name
                    tool_choice = ToolChoice(
                        type="required", function=request.tool_choice
                    )

            # Send query with tools using the complete flow or legacy flow
            if request.complete_tool_flow:
                # Use new complete flow (default)
                response = await llm_service.query_with_tools_and_followup(
                    prompt=request.prompt,
                    tools=available_tools,
                    conversation_history=request.conversation_history,
                    tool_choice=tool_choice,
                    options=options,
                    repository_context=request.repository_context,
                    document_metadata=request.document_metadata,
                    document_content=request.document_content,
                    system_prompt_template=request.system_prompt_template
                    or "contextual_document_assistant_ja",
                    include_document_in_system_prompt=request.include_document_in_system_prompt,
                )
            else:
                # Use legacy flow for backward compatibility
                response = await llm_service.query_with_tools(
                    prompt=request.prompt,
                    tools=available_tools,
                    conversation_history=request.conversation_history,
                    tool_choice=tool_choice,
                    options=options,
                    repository_context=request.repository_context,
                    document_metadata=request.document_metadata,
                    document_content=request.document_content,
                    system_prompt_template=request.system_prompt_template
                    or "contextual_document_assistant_ja",
                    include_document_in_system_prompt=request.include_document_in_system_prompt,
                )
                # Execute function calls if present (legacy behavior)
                if response.tool_calls:
                    executed_results = []
                    for tool_call in response.tool_calls:
                        try:
                            result = await llm_service.execute_function_call(
                                tool_call.function,
                                {func.name: func for func in available_tools},
                            )
                            executed_results.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "result": result,
                                }
                            )
                        except Exception as e:
                            executed_results.append(
                                {
                                    "tool_call_id": tool_call.id,
                                    "function_name": tool_call.function.name,
                                    "error": str(e),
                                }
                            )

                    # Add execution results to response
                    response.tool_execution_results = executed_results
        else:
            # Send regular query to LLM with conversation history and repository context
            response = await llm_service.query(
                request.prompt,
                conversation_history=request.conversation_history,
                options=options,
                repository_context=request.repository_context,
                document_metadata=request.document_metadata,
                document_content=request.document_content,
                system_prompt_template=request.system_prompt_template
                or "contextual_document_assistant_ja",
                include_document_in_system_prompt=request.include_document_in_system_prompt,
            )

        return response

    except Exception as e:
        raise LLMServiceException(message="Error querying LLM", detail=str(e))


@router.get(
    "/capabilities",
    summary="Get LLM capabilities",
    description="Get the capabilities of the configured LLM provider",
)
async def get_capabilities(
    provider: Optional[str] = Query(
        None, description="LLM provider to check capabilities for"
    ),
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Get the capabilities of an LLM provider.

    Args:
        provider: The provider to check capabilities for (optional)
        llm_service: The LLM service to use (injected)

    Returns:
        dict: The provider capabilities
    """
    try:
        capabilities = await llm_service.get_capabilities()
        return capabilities

    except Exception as e:
        raise LLMServiceException(
            message="Error getting LLM capabilities", detail=str(e)
        )


@router.get(
    "/templates",
    response_model=List[str],
    summary="List available templates",
    description="Get a list of available prompt templates",
)
async def list_templates(
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Get a list of available prompt templates.

    Args:
        llm_service: The LLM service to use (injected)

    Returns:
        List[str]: List of template IDs
    """
    try:
        templates = await llm_service.get_available_templates()
        return templates

    except Exception as e:
        raise LLMServiceException(message="Error listing templates", detail=str(e))


@router.post(
    "/format-prompt",
    response_model=str,
    summary="Format prompt template",
    description="Format a prompt template with provided variables",
)
async def format_prompt(
    request: Dict[str, Any],
    template_id: str = Query(..., description="ID of the template to format"),
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Format a prompt template with variables.

    Args:
        request: The variables to substitute in the template
        template_id: The ID of the template to format
        llm_service: The LLM service to use (injected)

    Returns:
        str: The formatted prompt
    """
    try:
        formatted = await llm_service.format_prompt(template_id, request)
        return formatted

    except TemplateNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except TemplateSyntaxError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise LLMServiceException(message="Error formatting template", detail=str(e))


@router.post(
    "/stream",
    summary="Stream LLM response",
    description="Stream response from LLM in real-time using Server-Sent Events (SSE)",
)
async def stream_llm_response(
    request: LLMQueryRequest,
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Stream a response from an LLM with optional Function Calling support.

    Args:
        request: The query request containing prompt and options
        llm_service: The LLM service to use (injected)

    Returns:
        EventSourceResponse: Server-Sent Events response
    """
    # Check if streaming is supported
    capabilities = await llm_service.get_capabilities()
    if not capabilities.supports_streaming:
        raise HTTPException(
            status_code=400,
            detail="The selected LLM provider does not support streaming",
        )

    async def event_generator():
        try:
            # Prepare options
            options = request.options or {}
            if request.model:
                options["model"] = request.model

            # Set cache control flag
            if request.disable_cache:
                options["disable_cache"] = True

            # Process context documents if provided
            if request.context_documents:
                options["context_documents"] = request.context_documents

            # Check if tools/function calling is enabled
            if request.enable_tools:
                # Get available tools from the LLM service
                available_tools = await llm_service.get_available_functions()

                # Convert tool_choice string to ToolChoice object
                tool_choice = None
                if request.tool_choice:
                    from doc_ai_helper_backend.models.llm import ToolChoice

                    if request.tool_choice in ["auto", "none", "required"]:
                        tool_choice = ToolChoice(type=request.tool_choice)  # type: ignore
                    else:
                        # Assume it's a specific function name
                        tool_choice = ToolChoice(
                            type="required", function=request.tool_choice
                        )

                # For streaming with Function Calling, we need to handle it differently
                if request.complete_tool_flow:
                    # Use complete flow with streaming
                    yield json.dumps(
                        {
                            "status": "tools_processing",
                            "message": "Analyzing request and selecting tools...",
                        }
                    )

                    # Execute tools first, then stream the final response
                    response = await llm_service.query_with_tools_and_followup(
                        prompt=request.prompt,
                        tools=available_tools,
                        conversation_history=request.conversation_history,
                        tool_choice=tool_choice,
                        options=options,
                    )

                    # Stream the final response content
                    if hasattr(response, "content") and response.content:
                        # Send tool execution info
                        if (
                            hasattr(response, "tool_execution_results")
                            and response.tool_execution_results
                        ):
                            tool_info = {
                                "tools_executed": len(response.tool_execution_results),
                                "tool_names": [
                                    r.get("function_name", "unknown")
                                    for r in response.tool_execution_results
                                ],
                            }
                            yield json.dumps(
                                {"status": "tools_completed", "tool_info": tool_info}
                            )

                        # Stream the content word by word for a smooth experience
                        words = response.content.split()
                        for i, word in enumerate(words):
                            chunk = word + (" " if i < len(words) - 1 else "")
                            yield json.dumps({"text": chunk})
                            # Small delay for smooth streaming effect
                            import asyncio

                            await asyncio.sleep(0.02)

                else:
                    # Legacy flow - execute tools and return results
                    yield json.dumps(
                        {"status": "tools_processing", "message": "Executing tools..."}
                    )

                    response = await llm_service.query_with_tools(
                        prompt=request.prompt,
                        tools=available_tools,
                        conversation_history=request.conversation_history,
                        tool_choice=tool_choice,
                        options=options,
                    )

                    # Execute function calls if present
                    if response.tool_calls:
                        executed_results = []
                        for tool_call in response.tool_calls:
                            try:
                                result = await llm_service.execute_function_call(
                                    tool_call.function,
                                    {func.name: func for func in available_tools},
                                )
                                executed_results.append(
                                    {
                                        "tool_call_id": tool_call.id,
                                        "function_name": tool_call.function.name,
                                        "result": result,
                                    }
                                )
                                # Send progress update
                                yield json.dumps(
                                    {
                                        "status": "tool_executed",
                                        "tool_name": tool_call.function.name,
                                    }
                                )
                            except Exception as e:
                                executed_results.append(
                                    {
                                        "tool_call_id": tool_call.id,
                                        "function_name": tool_call.function.name,
                                        "error": str(e),
                                    }
                                )

                        # Send tool execution results
                        yield json.dumps({"tool_execution_results": executed_results})

                    # Send any content from the initial response
                    if hasattr(response, "content") and response.content:
                        yield json.dumps({"text": response.content})

            else:
                # Regular streaming without tools
                # stream_queryメソッドを呼び出してAsyncGeneratorを取得
                async for text_chunk in llm_service.stream_query(
                    request.prompt,
                    conversation_history=request.conversation_history,
                    options=options,
                    repository_context=request.repository_context,
                    document_metadata=request.document_metadata,
                    document_content=request.document_content,
                    system_prompt_template=request.system_prompt_template
                    or "contextual_document_assistant_ja",
                    include_document_in_system_prompt=request.include_document_in_system_prompt,
                ):
                    # Send each chunk as an SSE event
                    yield json.dumps({"text": text_chunk})

            # Signal completion
            yield json.dumps({"done": True})

        except Exception as e:
            # Send error as an event
            error_msg = str(e)
            yield json.dumps({"error": error_msg})

    # Return an SSE response
    return EventSourceResponse(event_generator())


@router.get(
    "/tools",
    response_model=MCPToolsResponse,
    summary="Get available MCP tools",
    description="Get a list of all available MCP tools with their descriptions and parameters",
)
async def get_mcp_tools():
    """
    Get information about all available MCP tools.

    Returns:
        MCPToolsResponse: Information about available tools
    """
    try:
        from doc_ai_helper_backend.services.mcp.server import (
            get_tools_info,
            get_server_info,
        )

        # Get detailed tool information
        tools_info = await get_tools_info()
        server_info = await get_server_info()

        # Convert to MCPToolInfo objects
        mcp_tools = []
        categories = set()

        for tool_info in tools_info:
            # Convert parameters
            parameters = [
                ToolParameter(
                    name=param["name"],
                    type=param["type"],
                    description=param.get("description", ""),
                    required=param.get("required", False),
                    default=param.get("default"),
                )
                for param in tool_info.get("parameters", [])
            ]

            # Create MCPToolInfo
            mcp_tool = MCPToolInfo(
                name=tool_info["name"],
                description=tool_info.get("description"),
                parameters=parameters,
                category=tool_info.get("category", "other"),
                enabled=tool_info.get("enabled", True),
            )

            mcp_tools.append(mcp_tool)
            categories.add(tool_info.get("category", "other"))

        return MCPToolsResponse(
            tools=mcp_tools,
            total_count=len(mcp_tools),
            categories=sorted(list(categories)),
            server_info=server_info,
        )

    except Exception as e:
        logger.error(f"Error getting MCP tools: {e}")
        raise HTTPException(
            status_code=500, detail=f"Failed to get MCP tools: {str(e)}"
        )


@router.get(
    "/tools/{tool_name}",
    response_model=MCPToolInfo,
    summary="Get specific MCP tool information",
    description="Get detailed information about a specific MCP tool",
)
async def get_mcp_tool(
    tool_name: str = Path(..., description="Name of the tool to get information about")
):
    """
    Get information about a specific MCP tool.

    Args:
        tool_name: Name of the tool

    Returns:
        MCPToolInfo: Information about the specified tool
    """
    try:
        from doc_ai_helper_backend.services.mcp.server import get_tools_info

        tools_info = await get_tools_info()

        # Find the specific tool
        tool_info = next(
            (tool for tool in tools_info if tool["name"] == tool_name), None
        )

        if not tool_info:
            raise HTTPException(status_code=404, detail=f"Tool '{tool_name}' not found")

        # Convert parameters
        parameters = [
            ToolParameter(
                name=param["name"],
                type=param["type"],
                description=param.get("description", ""),
                required=param.get("required", False),
                default=param.get("default"),
            )
            for param in tool_info.get("parameters", [])
        ]

        return MCPToolInfo(
            name=tool_info["name"],
            description=tool_info.get("description"),
            parameters=parameters,
            category=tool_info.get("category", "other"),
            enabled=tool_info.get("enabled", True),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting MCP tool '{tool_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get MCP tool: {str(e)}")
