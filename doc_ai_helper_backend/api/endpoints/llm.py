"""
LLM API endpoints.

This module provides the API endpoints for LLM functionality.
"""

from typing import Dict, Any, List, Optional
import json
import logging
from fastapi import APIRouter, Depends, HTTPException, Query, Path
from sse_starlette.sse import EventSourceResponse
from pydantic import ValidationError

from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    LLMResponse,
    PromptTemplate,
    MCPToolsResponse,
    MCPToolInfo,
    ToolParameter,
    ProviderCapabilities,
)
from doc_ai_helper_backend.services.llm.base import LLMServiceBase
from doc_ai_helper_backend.services.llm.factory import LLMServiceFactory
from doc_ai_helper_backend.services.llm.orchestrator import LLMOrchestrator
from doc_ai_helper_backend.core.exceptions import (
    LLMServiceException,
    ServiceNotFoundError,
    TemplateNotFoundError,
    TemplateSyntaxError,
)
from doc_ai_helper_backend.api.dependencies import get_llm_service, get_llm_orchestrator, get_llm_orchestrator_with_document_service
# Legacy imports - functionality now integrated into orchestrator

logger = logging.getLogger(__name__)


router = APIRouter()


# === Helper Dependencies ===

def get_llm_orchestrator_dep(
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator_with_document_service)
) -> LLMOrchestrator:
    """Dependency to get LLMOrchestrator instance with DocumentService integration."""
    return orchestrator


# Parameter validation is now handled by the orchestrator


@router.post(
    "/query",
    response_model=LLMResponse,
    summary="Query LLM",
    description="Send a query to an LLM with optional document context",
)
async def query_llm(
    request: LLMQueryRequest,
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator_dep),
    # Parameter validation handled by orchestrator
):
    """
    Send a query to an LLM using the structured parameter format.

    Args:
        request: The structured LLM query request
        query_processor: Query processing service
        validator: Parameter validation service

    Returns:
        LLMResponse: The response from the LLM
    """
    try:
        # Log raw request for debugging
        logger.info("=== RAW REQUEST DEBUG ===")
        logger.info(f"Full request: {request.model_dump()}")
        logger.info("========================")
        
        # Log request details for debugging
        logger.info(f"LLM query request - provider: {request.query.provider}")
        if request.tools:
            logger.info(f"Tools configuration - enable_tools: {request.tools.enable_tools}, tool_choice: {request.tools.tool_choice}")
        else:
            logger.info("No tools configuration provided in request")
            
        if request.document:
            if request.document.repository_context:
                repo_ctx = request.document.repository_context
                logger.info(f"Repository context - service: {repo_ctx.service}, owner: {repo_ctx.owner}, repo: {repo_ctx.repo}")
            else:
                logger.info("Document context provided but no repository context")
        else:
            logger.info("No document context provided in request")
        
        # Validate request parameters
        # Request validation handled by orchestrator
        
        # Process query using new infrastructure
        response = await orchestrator.execute_query(request)
        return response

    except ValidationError as e:
        logger.warning(f"Request validation failed: {e}")
        raise HTTPException(
            status_code=422, 
            detail=e.errors()
        )
    except ServiceNotFoundError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except LLMServiceException as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        logger.error(f"Unexpected error in query_llm: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get(
    "/capabilities",
    response_model=ProviderCapabilities,
    summary="Get LLM capabilities",
    description="Get the capabilities of the configured LLM provider",
)
async def get_capabilities(
    llm_service: LLMServiceBase = Depends(get_llm_service),
):
    """
    Get the capabilities of an LLM provider.

    Args:
        llm_service: The LLM service to use (injected)

    Returns:
        ProviderCapabilities: The provider capabilities
    """
    try:
        capabilities = await llm_service.get_capabilities()
        return capabilities

    except Exception as e:
        raise LLMServiceException(
            message="Error getting LLM capabilities", detail=str(e)
        )


@router.get(
    "/providers",
    response_model=Dict[str, Any],
    summary="Get provider information",
    description="Get information about available LLM providers and their status",
)
async def get_provider_info():
    """
    Get information about available LLM providers.
    
    Returns detailed information about each provider including
    configuration status and capabilities.

    Returns:
        Dict[str, Any]: Provider information and status
    """
    try:
        available_providers = LLMServiceFactory.get_available_providers()
        all_providers = LLMServiceFactory.get_available_providers()  # すべてサポートされているとする
        
        provider_statuses = {}
        for provider in all_providers:
            provider_statuses[provider] = {
                "provider": provider,
                "supported": True,
                "configured": True,  # 簡素化のため、登録されていれば設定済みとする
                "available": True
            }
        
        return {
            "available_providers": available_providers,
            "all_supported_providers": all_providers,
            "provider_details": provider_statuses,
            "total_available": len(available_providers),
            "total_supported": len(all_providers),
        }

    except Exception as e:
        logger.error(f"Error getting provider information: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get provider information: {str(e)}")


@router.get(
    "/providers/{provider_name}/status",
    response_model=Dict[str, Any],
    summary="Get specific provider status",
    description="Get detailed status information for a specific provider",
)
async def get_provider_status(
    provider_name: str = Path(..., description="Name of the provider to check")
):
    """
    Get detailed status information for a specific provider.

    Args:
        provider_name: Name of the provider

    Returns:
        Dict[str, Any]: Detailed provider status
    """
    try:
        available_providers = LLMServiceFactory.get_available_providers()
        
        if provider_name in available_providers:
            return {
                "provider": provider_name,
                "supported": True,
                "configured": True,
                "available": True
            }
        else:
            return {
                "provider": provider_name,
                "supported": False,
                "configured": False,
                "available": False
            }

    except Exception as e:
        logger.error(f"Error getting provider status for '{provider_name}': {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to get provider status: {str(e)}"
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
    orchestrator: LLMOrchestrator = Depends(get_llm_orchestrator_dep),
    # Parameter validation handled by orchestrator
):
    """
    Stream a response from an LLM using the structured parameter format.

    Args:
        request: The structured LLM query request
        query_processor: Query processing service
        validator: Parameter validation service

    Returns:
        EventSourceResponse: Server-Sent Events response
    """
    async def event_generator():
        try:
            # Log request details for debugging
            logger.info(f"STREAM LLM query request - provider: {request.query.provider}")
            if request.tools:
                logger.info(f"STREAM Tools configuration - enable_tools: {request.tools.enable_tools}, tool_choice: {request.tools.tool_choice}")
            else:
                logger.info("STREAM No tools configuration provided in request")
                
            if request.document:
                if request.document.repository_context:
                    repo_ctx = request.document.repository_context
                    logger.info(f"STREAM Repository context - service: {repo_ctx.service}, owner: {repo_ctx.owner}, repo: {repo_ctx.repo}")
                else:
                    logger.info("STREAM Document context provided but no repository context")
            else:
                logger.info("STREAM No document context provided in request")
            
            # Validate request parameters
            # Request validation handled by orchestrator
            
            # Execute streaming query using new infrastructure
            async for chunk in orchestrator.execute_streaming_query(request):
                yield json.dumps(chunk)

        except ValidationError as e:
            logger.warning(f"Request validation failed: {e}")
            yield json.dumps({
                "error": "Validation error",
                "validation_errors": e.errors()
            })
        except ServiceNotFoundError as e:
            yield json.dumps({"error": f"Service not found: {str(e)}"})
        except LLMServiceException as e:
            yield json.dumps({"error": f"LLM service error: {str(e)}"})
        except Exception as e:
            logger.error(f"Unexpected error in stream_llm_response: {e}")
            yield json.dumps({"error": "Internal server error"})

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
