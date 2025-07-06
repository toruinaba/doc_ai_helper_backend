"""
Streaming utilities for LLM services.

This module provides utilities for handling streaming responses across
different LLM service implementations.
"""

import asyncio
import logging
from typing import AsyncGenerator, Union, List

logger = logging.getLogger(__name__)


class StreamingUtils:
    """
    Utility class for handling streaming operations in LLM services.

    This class provides common streaming functionality that can be reused
    across different LLM service implementations.
    """

    @staticmethod
    async def chunk_content(
        content: str,
        chunk_size: int = 15,
        delay_per_chunk: float = 0.1,
        total_delay: float = 0.0,
    ) -> AsyncGenerator[str, None]:
        """
        Split content into chunks and yield them with delays.

        This is useful for simulating streaming responses or controlling
        the rate of content delivery.

        Args:
            content: The content to chunk
            chunk_size: Size of each chunk in characters
            delay_per_chunk: Delay between chunks in seconds
            total_delay: Total delay to distribute across all chunks

        Yields:
            str: Content chunks
        """
        if not content:
            return

        # Calculate dynamic delay if total_delay is specified
        if total_delay > 0 and len(content) > 0:
            num_chunks = max(1, len(content) // chunk_size)
            delay_per_chunk = total_delay / num_chunks

        for i in range(0, len(content), chunk_size):
            chunk = content[i : i + chunk_size]

            if delay_per_chunk > 0:
                await asyncio.sleep(delay_per_chunk)

            yield chunk

        logger.debug(
            f"Completed chunking {len(content)} characters into {len(content) // chunk_size + 1} chunks"
        )

    @staticmethod
    async def buffer_stream(
        stream: AsyncGenerator[str, None],
        buffer_size: int = 100,
        flush_on_newline: bool = True,
    ) -> AsyncGenerator[str, None]:
        """
        Buffer a stream and yield when buffer is full or on newlines.

        This can improve streaming performance by reducing the number
        of small yields.

        Args:
            stream: The input stream to buffer
            buffer_size: Maximum buffer size before flushing
            flush_on_newline: Whether to flush buffer on newline characters

        Yields:
            str: Buffered content
        """
        buffer = ""

        async for chunk in stream:
            buffer += chunk

            # Check if we should flush the buffer
            should_flush = len(buffer) >= buffer_size or (
                flush_on_newline and "\n" in buffer
            )

            if should_flush:
                yield buffer
                buffer = ""

        # Yield any remaining content in buffer
        if buffer:
            yield buffer

        logger.debug("Completed stream buffering")

    @staticmethod
    async def merge_streams(
        *streams: AsyncGenerator[str, None],
        separator: str = "",
    ) -> AsyncGenerator[str, None]:
        """
        Merge multiple streams into a single stream.

        Args:
            *streams: Variable number of async generators to merge
            separator: Separator to insert between streams

        Yields:
            str: Merged content from all streams
        """
        for i, stream in enumerate(streams):
            if i > 0 and separator:
                yield separator

            async for chunk in stream:
                yield chunk

        logger.debug(f"Merged {len(streams)} streams")

    @staticmethod
    async def filter_stream(
        stream: AsyncGenerator[str, None],
        filter_func: callable,
    ) -> AsyncGenerator[str, None]:
        """
        Filter a stream based on a filter function.

        Args:
            stream: The input stream to filter
            filter_func: Function that takes a chunk and returns bool

        Yields:
            str: Filtered chunks
        """
        async for chunk in stream:
            if filter_func(chunk):
                yield chunk

        logger.debug("Completed stream filtering")

    @staticmethod
    async def transform_stream(
        stream: AsyncGenerator[str, None],
        transform_func: callable,
    ) -> AsyncGenerator[str, None]:
        """
        Transform each chunk in a stream using a transform function.

        Args:
            stream: The input stream to transform
            transform_func: Function that takes a chunk and returns transformed chunk

        Yields:
            str: Transformed chunks
        """
        async for chunk in stream:
            transformed_chunk = transform_func(chunk)
            if transformed_chunk:  # Only yield non-empty chunks
                yield transformed_chunk

        logger.debug("Completed stream transformation")

    @staticmethod
    async def collect_stream(
        stream: AsyncGenerator[str, None],
        max_length: int = 10000,
    ) -> str:
        """
        Collect all chunks from a stream into a single string.

        Args:
            stream: The stream to collect
            max_length: Maximum length to collect (prevents memory issues)

        Returns:
            str: Collected content from the entire stream
        """
        collected = ""

        async for chunk in stream:
            collected += chunk

            # Prevent memory issues with very long streams
            if len(collected) >= max_length:
                logger.warning(
                    f"Stream collection truncated at {max_length} characters"
                )
                break

        logger.debug(f"Collected {len(collected)} characters from stream")
        return collected

    @staticmethod
    async def rate_limit_stream(
        stream: AsyncGenerator[str, None],
        max_chunks_per_second: float = 10.0,
    ) -> AsyncGenerator[str, None]:
        """
        Rate limit a stream to control throughput.

        Args:
            stream: The input stream to rate limit
            max_chunks_per_second: Maximum chunks to yield per second

        Yields:
            str: Rate-limited chunks
        """
        if max_chunks_per_second <= 0:
            # No rate limiting
            async for chunk in stream:
                yield chunk
            return

        min_delay = 1.0 / max_chunks_per_second
        last_yield_time = 0.0

        async for chunk in stream:
            current_time = asyncio.get_event_loop().time()

            # Calculate required delay
            time_since_last = current_time - last_yield_time
            required_delay = min_delay - time_since_last

            if required_delay > 0:
                await asyncio.sleep(required_delay)

            yield chunk
            last_yield_time = asyncio.get_event_loop().time()

        logger.debug(f"Rate limited stream at {max_chunks_per_second} chunks/second")
