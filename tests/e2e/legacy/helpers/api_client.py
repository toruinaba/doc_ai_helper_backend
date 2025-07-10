"""
Simplified backend API client for E2E tests.

This module provides a streamlined client for communicating with the backend API server
during end-to-end tests, focusing on core functionality needed for E2E scenarios.
"""

import asyncio
import json
from typing import Dict, Any, Optional, AsyncGenerator
import httpx
import logging

logger = logging.getLogger(__name__)


class BackendAPIClient:
    """
    Client for communicating with the Document AI Helper backend API.

    This client is designed for E2E tests where the backend server is running
    in a separate process.
    """

    def __init__(self, base_url: str = "http://localhost:8000", timeout: int = 30):
        """
        Initialize the API client.

        Args:
            base_url: Base URL of the backend API server
            timeout: Request timeout in seconds
        """
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout
        self._client = httpx.AsyncClient(timeout=timeout)

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self._client.aclose()

    @property
    def client(self) -> httpx.AsyncClient:
        """Get the underlying httpx AsyncClient for direct use."""
        return self._client

    async def health_check(self) -> bool:
        """
        Check if the backend API server is running and healthy.

        Returns:
            True if the server is healthy, False otherwise
        """
        try:
            response = await self._client.get(f"{self.base_url}/api/v1/health/")
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False

    async def get_document(
        self,
        service: str,
        owner: str,
        repo: str,
        path: str,
        ref: str = "main",
        transform_links: bool = True,
        base_url: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Get a document from a Git repository via the backend API.

        Args:
            service: Git service name (github, forgejo, mock)
            owner: Repository owner
            repo: Repository name
            path: Document path
            ref: Branch or tag name
            transform_links: Whether to transform relative links
            base_url: Base URL for link transformation

        Returns:
            Document response as dictionary

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = (
            f"{self.base_url}/api/v1/documents/contents/{service}/{owner}/{repo}/{path}"
        )
        params = {"ref": ref, "transform_links": transform_links}
        if base_url:
            params["base_url"] = base_url

        logger.info(f"Getting document: {url} with params: {params}")

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def query_llm(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        tools_enabled: bool = True,
        provider: str = "mock",
        model: Optional[str] = None,
        stream: bool = False,
        repository_context=None,
    ) -> Dict[str, Any]:
        """
        Send a query to the LLM via the backend API.

        Args:
            prompt: The prompt to send to the LLM
            context: Optional context information
            tools_enabled: Whether to enable MCP tools
            provider: LLM provider to use
            model: Specific model to use
            stream: Whether to use streaming response
            repository_context: Repository context for Git operations

        Returns:
            LLM response as dictionary

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.base_url}/api/v1/llm/query"
        payload = {
            "prompt": prompt,
            "provider": provider,
            "enable_tools": tools_enabled,
        }

        if context:
            payload["context"] = context
        if model:
            payload["model"] = model
        if stream:
            payload["stream"] = stream
        if repository_context:
            payload["repository_context"] = repository_context

        logger.info(f"Sending LLM query: {prompt[:100]}...")

        response = await self._client.post(url, json=payload)
        response.raise_for_status()
        return response.json()

    async def stream_llm_query(
        self,
        prompt: str,
        context: Optional[Dict[str, Any]] = None,
        tools_enabled: bool = True,
        provider: str = "mock",
        model: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Send a streaming query to the LLM via the backend API.

        Args:
            prompt: The prompt to send to the LLM
            context: Optional context information
            tools_enabled: Whether to enable MCP tools
            provider: LLM provider to use
            model: Specific model to use

        Yields:
            Chunks of the LLM response

        Raises:
            httpx.HTTPStatusError: If the request fails
        """
        url = f"{self.base_url}/api/v1/llm/stream"
        payload = {
            "prompt": prompt,
            "provider": provider,
            "enable_tools": tools_enabled,
        }

        if context:
            payload["context"] = context
        if model:
            payload["model"] = model

        logger.info(f"Starting streaming LLM query: {prompt[:100]}...")

        async with self._client.stream("POST", url, json=payload) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:]  # Remove 'data: ' prefix
                    if data.strip() == "[DONE]":
                        break
                    try:
                        chunk_data = json.loads(data)
                        if "text" in chunk_data:
                            yield chunk_data["text"]
                        elif "content" in chunk_data:
                            yield chunk_data["content"]
                    except json.JSONDecodeError:
                        continue

    async def get_repository_structure(
        self, service: str, owner: str, repo: str, ref: str = "main", path: str = ""
    ) -> Dict[str, Any]:
        """
        Get repository structure via the backend API.

        Args:
            service: Git service name
            owner: Repository owner
            repo: Repository name
            ref: Branch or tag name
            path: Path to get structure for

        Returns:
            Repository structure as dictionary
        """
        url = f"{self.base_url}/api/v1/documents/structure/{service}/{owner}/{repo}"
        params = {"ref": ref}
        if path:
            params["path"] = path

        response = await self._client.get(url, params=params)
        response.raise_for_status()
        return response.json()

    async def wait_for_server(self, max_attempts: int = 30, delay: float = 1.0) -> bool:
        """
        Wait for the backend server to become available.

        Args:
            max_attempts: Maximum number of health check attempts
            delay: Delay between attempts in seconds

        Returns:
            True if server becomes available, False if timeout
        """
        for attempt in range(max_attempts):
            if await self.health_check():
                logger.info(f"Backend server is available (attempt {attempt + 1})")
                return True

            logger.info(
                f"Waiting for backend server (attempt {attempt + 1}/{max_attempts})"
            )
            await asyncio.sleep(delay)

        logger.error("Backend server did not become available within timeout")
        return False
