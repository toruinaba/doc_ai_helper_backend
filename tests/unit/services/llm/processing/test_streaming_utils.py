"""
Tests for streaming utilities.
"""

import asyncio
import pytest
from unittest.mock import AsyncMock

from doc_ai_helper_backend.services.llm.processing.streaming_utils import StreamingUtils


class TestStreamingUtils:
    """Test streaming utilities functionality."""

    @pytest.fixture
    def streaming_utils(self):
        """Create StreamingUtils instance for testing."""
        return StreamingUtils()

    @pytest.mark.asyncio
    async def test_chunk_content_basic(self, streaming_utils):
        """Test basic content chunking."""
        content = "This is a test content for chunking"
        chunks = []

        async for chunk in streaming_utils.chunk_content(content, chunk_size=5):
            chunks.append(chunk)

        assert len(chunks) > 1
        assert "".join(chunks) == content

    @pytest.mark.asyncio
    async def test_chunk_content_with_delay(self, streaming_utils):
        """Test content chunking with total delay."""
        content = "Test content"
        chunks = []

        start_time = asyncio.get_event_loop().time()
        async for chunk in streaming_utils.chunk_content(
            content, chunk_size=5, total_delay=0.1
        ):
            chunks.append(chunk)
        end_time = asyncio.get_event_loop().time()

        assert len(chunks) > 1
        assert "".join(chunks) == content
        # Should take at least the specified delay
        assert end_time - start_time >= 0.05  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_chunk_content_empty(self, streaming_utils):
        """Test chunking empty content."""
        content = ""
        chunks = []

        async for chunk in streaming_utils.chunk_content(content):
            chunks.append(chunk)

        assert chunks == []

    @pytest.mark.asyncio
    async def test_buffer_stream(self, streaming_utils):
        """Test stream buffering."""

        async def test_stream():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"

        buffered_chunks = []
        async for chunk in streaming_utils.buffer_stream(test_stream(), buffer_size=10):
            buffered_chunks.append(chunk)

        assert len(buffered_chunks) > 0

    @pytest.mark.asyncio
    async def test_buffer_stream_with_newline_flush(self, streaming_utils):
        """Test stream buffering with newline flush."""

        async def test_stream():
            yield "line1\n"
            yield "line2"
            yield "\nline3"

        buffered_chunks = []
        async for chunk in streaming_utils.buffer_stream(
            test_stream(), buffer_size=20, flush_on_newline=True
        ):
            buffered_chunks.append(chunk)

        assert len(buffered_chunks) >= 2

    @pytest.mark.asyncio
    async def test_aggregate_stream(self, streaming_utils):
        """Test stream aggregation."""

        async def test_stream():
            yield "Hello"
            yield " "
            yield "World"

        result = await streaming_utils.aggregate_stream(test_stream())
        assert result == "Hello World"

    @pytest.mark.asyncio
    async def test_aggregate_stream_max_length_exceeded(self, streaming_utils):
        """Test stream aggregation with max length exceeded."""

        async def test_stream():
            yield "A" * 100
            yield "B" * 100

        with pytest.raises(ValueError, match="Content length exceeded maximum"):
            await streaming_utils.aggregate_stream(test_stream(), max_content_length=50)

    @pytest.mark.asyncio
    async def test_throttle_stream_no_throttling(self, streaming_utils):
        """Test stream throttling with no throttling."""

        async def test_stream():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"

        chunks = []
        async for chunk in streaming_utils.throttle_stream(
            test_stream(), max_chunks_per_second=0
        ):
            chunks.append(chunk)

        assert chunks == ["chunk1", "chunk2", "chunk3"]

    @pytest.mark.asyncio
    async def test_throttle_stream_with_throttling(self, streaming_utils):
        """Test stream throttling with throttling enabled."""

        async def test_stream():
            yield "chunk1"
            yield "chunk2"

        chunks = []
        start_time = asyncio.get_event_loop().time()
        async for chunk in streaming_utils.throttle_stream(
            test_stream(), max_chunks_per_second=10  # 10 chunks per second
        ):
            chunks.append(chunk)
        end_time = asyncio.get_event_loop().time()

        assert chunks == ["chunk1", "chunk2"]
        # Should take at least 0.1 seconds between chunks
        assert end_time - start_time >= 0.05  # Allow some tolerance

    @pytest.mark.asyncio
    async def test_filter_stream_no_filter(self, streaming_utils):
        """Test stream filtering with no filter."""

        async def test_stream():
            yield "chunk1"
            yield "chunk2"
            yield "chunk3"

        chunks = []
        async for chunk in streaming_utils.filter_stream(test_stream()):
            chunks.append(chunk)

        assert chunks == ["chunk1", "chunk2", "chunk3"]

    @pytest.mark.asyncio
    async def test_filter_stream_with_filter(self, streaming_utils):
        """Test stream filtering with filter function."""

        async def test_stream():
            yield "keep"
            yield "skip"
            yield "keep"

        def filter_func(chunk):
            return chunk == "keep"

        chunks = []
        async for chunk in streaming_utils.filter_stream(
            test_stream(), filter_func=filter_func
        ):
            chunks.append(chunk)

        assert chunks == ["keep", "keep"]

    @pytest.mark.asyncio
    async def test_transform_stream(self, streaming_utils):
        """Test stream transformation."""

        async def test_stream():
            yield "hello"
            yield "world"

        def transform_func(chunk):
            return chunk.upper()

        chunks = []
        async for chunk in streaming_utils.transform_stream(
            test_stream(), transform_func=transform_func
        ):
            chunks.append(chunk)

        assert chunks == ["HELLO", "WORLD"]

    @pytest.mark.asyncio
    async def test_transform_stream_no_transform(self, streaming_utils):
        """Test stream transformation with no transform function."""

        async def test_stream():
            yield "hello"
            yield "world"

        chunks = []
        async for chunk in streaming_utils.transform_stream(test_stream()):
            chunks.append(chunk)

        assert chunks == ["hello", "world"]

    @pytest.mark.asyncio
    async def test_join_streams(self, streaming_utils):
        """Test joining multiple streams."""

        async def stream1():
            yield "A1"
            yield "A2"

        async def stream2():
            yield "B1"
            yield "B2"

        chunks = []
        async for chunk in streaming_utils.join_streams(stream1(), stream2()):
            chunks.append(chunk)

        assert len(chunks) == 4
        assert chunks == ["A1", "A2", "B1", "B2"]

    @pytest.mark.asyncio
    async def test_join_streams_empty(self, streaming_utils):
        """Test joining no streams."""
        chunks = []
        async for chunk in streaming_utils.join_streams():
            chunks.append(chunk)

        assert chunks == []

    @pytest.mark.asyncio
    async def test_create_mock_stream(self, streaming_utils):
        """Test creating mock stream."""
        test_content = "Hello World Test"

        chunks = []
        async for chunk in streaming_utils.create_mock_stream(
            test_content, chunk_size=5, delay=0.01
        ):
            chunks.append(chunk)

        assert "".join(chunks) == test_content
        assert len(chunks) > 1
