"""
Test for MCP feedback tools functionality.

This module contains unit tests for the feedback tools used in MCP server.
"""

import pytest
import json
from unittest.mock import AsyncMock, patch
from datetime import datetime

from doc_ai_helper_backend.services.mcp.tools.feedback_tools import (
    generate_feedback_from_conversation,
    create_improvement_proposal,
    analyze_conversation_patterns,
)


class TestFeedbackTools:
    """Test the MCP feedback tools functionality."""

    @pytest.mark.asyncio
    async def test_generate_feedback_from_conversation_basic(self):
        """Test basic feedback generation from conversation."""
        conversation_history = [
            {"role": "user", "content": "What is machine learning?"},
            {"role": "assistant", "content": "Machine learning is a subset of AI..."},
            {"role": "user", "content": "Can you give me an example?"},
            {"role": "assistant", "content": "Sure, here's an example..."},
        ]

        result = await generate_feedback_from_conversation(conversation_history)

        # Should return JSON string
        assert isinstance(result, str)

        # Parse and validate JSON structure
        feedback_data = json.loads(result)
        assert "conversation_summary" in feedback_data
        assert "feedback_type" in feedback_data
        assert "suggestions" in feedback_data
        assert "priority_level" in feedback_data

        # Validate conversation summary
        summary = feedback_data["conversation_summary"]
        assert summary["total_messages"] == 4
        assert summary["user_questions"] == 2
        assert summary["assistant_responses"] == 2
        assert "analysis_timestamp" in summary

    @pytest.mark.asyncio
    async def test_generate_feedback_from_conversation_with_context(self):
        """Test feedback generation with document context."""
        conversation_history = [
            {"role": "user", "content": "Explain this document."},
            {"role": "assistant", "content": "This document discusses..."},
        ]
        document_context = "This is a technical document about AI."
        feedback_type = "comprehension"

        result = await generate_feedback_from_conversation(
            conversation_history, document_context, feedback_type
        )

        feedback_data = json.loads(result)
        assert feedback_data["feedback_type"] == "comprehension"
        assert "conversation_summary" in feedback_data

    @pytest.mark.asyncio
    async def test_generate_feedback_from_conversation_empty_history(self):
        """Test feedback generation with empty conversation history."""
        conversation_history = []

        result = await generate_feedback_from_conversation(conversation_history)

        feedback_data = json.loads(result)
        summary = feedback_data["conversation_summary"]
        assert summary["total_messages"] == 0
        assert summary["user_questions"] == 0
        assert summary["assistant_responses"] == 0

    @pytest.mark.asyncio
    async def test_generate_feedback_from_conversation_error_handling(self):
        """Test feedback generation error handling."""
        # Invalid conversation history format
        invalid_history = "not_a_list"

        result = await generate_feedback_from_conversation(invalid_history)

        feedback_data = json.loads(result)
        assert "error" in feedback_data

    @pytest.mark.asyncio
    async def test_create_improvement_proposal_basic(self):
        """Test basic improvement proposal creation."""
        current_content = """
        # Basic Document
        
        This is a simple document with basic content.
        It needs improvement in structure and detail.
        """

        feedback_data = json.dumps(
            {
                "suggestions": ["Add more examples", "Improve structure"],
                "priority_level": "high",
            }
        )

        result = await create_improvement_proposal(current_content, feedback_data)

        # Should return JSON string
        assert isinstance(result, str)

        # Parse and validate JSON structure
        proposal = json.loads(result)
        assert "improvement_type" in proposal
        assert "current_content_analysis" in proposal
        assert "improvement_suggestions" in proposal
        assert "implementation_effort" in proposal
        assert "expected_improvements" in proposal
        assert "feedback_reference" in proposal

    @pytest.mark.asyncio
    async def test_create_improvement_proposal_with_types(self):
        """Test improvement proposal with different improvement types."""
        current_content = "Short content"
        feedback_data = '{"suggestions": ["test"]}'

        for improvement_type in ["general", "structure", "content"]:
            result = await create_improvement_proposal(
                current_content, feedback_data, improvement_type
            )

            proposal = json.loads(result)
            assert proposal["improvement_type"] == improvement_type

    @pytest.mark.asyncio
    async def test_create_improvement_proposal_with_dict_feedback(self):
        """Test improvement proposal with feedback as dict."""
        current_content = "Test content"
        feedback_data = {"suggestions": ["improve"], "level": "medium"}

        result = await create_improvement_proposal(current_content, feedback_data)

        proposal = json.loads(result)
        assert "feedback_reference" in proposal
        assert proposal["feedback_reference"]["suggestions"] == ["improve"]

    @pytest.mark.asyncio
    async def test_create_improvement_proposal_error_handling(self):
        """Test improvement proposal error handling."""
        current_content = "Test content"
        invalid_feedback = "invalid_json{"

        result = await create_improvement_proposal(current_content, invalid_feedback)

        proposal = json.loads(result)
        assert "error" in proposal

    @pytest.mark.asyncio
    async def test_analyze_conversation_patterns_basic(self):
        """Test basic conversation pattern analysis."""
        conversation_history = [
            {"role": "user", "content": "Question 1"},
            {"role": "assistant", "content": "Answer 1"},
            {"role": "user", "content": "Question 2"},
            {"role": "assistant", "content": "Answer 2"},
        ]

        result = await analyze_conversation_patterns(conversation_history)

        assert isinstance(result, dict)
        assert "patterns" in result
        assert "analysis_depth" in result
        assert "insights" in result
        assert "recommendations" in result

        patterns = result["patterns"]
        assert patterns["message_frequency"] == 4
        assert patterns["engagement_level"] in ["high", "medium", "low"]

    @pytest.mark.asyncio
    async def test_analyze_conversation_patterns_depth_levels(self):
        """Test conversation pattern analysis with different depth levels."""
        conversation_history = [
            {"role": "user", "content": "Test question"},
            {"role": "assistant", "content": "Test answer"},
        ]

        for depth in ["basic", "detailed", "comprehensive"]:
            result = await analyze_conversation_patterns(conversation_history, depth)

            assert result["analysis_depth"] == depth
            assert "patterns" in result

    @pytest.mark.asyncio
    async def test_analyze_conversation_patterns_engagement_levels(self):
        """Test conversation pattern analysis engagement level calculation."""
        # Test high engagement (>10 messages)
        long_conversation = [
            {"role": "user", "content": f"Message {i}"} for i in range(12)
        ]

        result = await analyze_conversation_patterns(long_conversation)
        assert result["patterns"]["engagement_level"] == "high"

        # Test medium engagement (<=10 messages)
        short_conversation = [
            {"role": "user", "content": "Message 1"},
            {"role": "assistant", "content": "Answer 1"},
        ]

        result = await analyze_conversation_patterns(short_conversation)
        assert result["patterns"]["engagement_level"] == "medium"

    @pytest.mark.asyncio
    async def test_analyze_conversation_patterns_empty_history(self):
        """Test conversation pattern analysis with empty history."""
        conversation_history = []

        result = await analyze_conversation_patterns(conversation_history)

        assert result["patterns"]["message_frequency"] == 0
        assert result["patterns"]["engagement_level"] == "medium"

    @pytest.mark.asyncio
    async def test_analyze_conversation_patterns_error_handling(self):
        """Test conversation pattern analysis error handling."""
        # Test with None as conversation history to force an error
        with patch(
            "doc_ai_helper_backend.services.mcp.tools.feedback_tools.len",
            side_effect=TypeError("test error"),
        ):
            result = await analyze_conversation_patterns([])
            assert "error" in result
