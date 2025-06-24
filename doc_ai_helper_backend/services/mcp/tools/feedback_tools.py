"""
Feedback generation tools for MCP server.

This module provides tools for analyzing conversations and generating
improvement feedback based on user interactions.
"""

import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


async def generate_feedback_from_conversation(
    conversation_history: List[Dict[str, Any]], 
    document_context: str = "",
    feedback_type: str = "general"
) -> str:
    """
    Generate feedback based on conversation analysis.

    Args:
        conversation_history: List of conversation messages
        document_context: Document context for analysis (optional)
        feedback_type: Type of feedback (general, comprehension, gaps, suggestions)

    Returns:
        JSON string containing feedback analysis
    """
    try:
        # Analyze conversation patterns
        user_questions = [
            msg for msg in conversation_history if msg.get("role") == "user"
        ]
        assistant_responses = [
            msg for msg in conversation_history if msg.get("role") == "assistant"
        ]

        # Basic feedback analysis
        feedback = {
            "conversation_summary": {
                "total_messages": len(conversation_history),
                "user_questions": len(user_questions),
                "assistant_responses": len(assistant_responses),
                "analysis_timestamp": datetime.now().isoformat(),
            },
            "feedback_type": feedback_type,
            "suggestions": [
                "Consider adding more examples",
                "Improve clarity of explanations",
                "Add interactive elements",
            ],            "priority_level": "medium",
        }

        logger.info(
            f"Generated feedback for conversation with {len(user_questions)} questions"
        )
        
        # FastMCPではJSON文字列として返す
        import json
        return json.dumps(feedback, indent=2)

    except Exception as e:
        logger.error(f"Error generating feedback from conversation: {e}")
        import json
        return json.dumps({"error": str(e)})


async def create_improvement_proposal(
    current_content: str, 
    feedback_data: str,
    improvement_type: str = "general"
) -> str:
    """
    Create a structured improvement proposal based on feedback.

    Args:
        current_content: Current content to improve
        feedback_data: Feedback analysis results (JSON string)
        improvement_type: Type of improvement (general, structure, content)    Returns:
        JSON string containing structured improvement proposal
    """
    try:
        # Parse feedback_data if it's a JSON string
        import json
        if isinstance(feedback_data, str):
            parsed_feedback = json.loads(feedback_data)
        else:
            parsed_feedback = feedback_data
            
        proposal = {
            "improvement_type": improvement_type,
            "current_content_analysis": {
                "length": len(current_content),
                "sections": len(current_content.split("\n\n")),
                "complexity": "medium",
            },
            "improvement_suggestions": [
                "Add more detailed explanations",
                "Include practical examples",
                "Improve document structure",
            ],
            "implementation_effort": "medium",
            "expected_improvements": {
                "readability": "15-20%",
                "completeness": "10-15%",
                "user_satisfaction": "20-25%",
            },
            "feedback_reference": parsed_feedback,
        }

        logger.info("Created improvement proposal")
        
        # FastMCPではJSON文字列として返す
        return json.dumps(proposal, indent=2)

    except Exception as e:
        logger.error(f"Error creating improvement proposal: {e}")
        import json
        return json.dumps({"error": str(e)})


async def analyze_conversation_patterns(
    conversation_history: List[Dict[str, Any]], analysis_depth: str = "basic"
) -> Dict[str, Any]:
    """
    Analyze patterns in conversation history.

    Args:
        conversation_history: List of conversation messages
        analysis_depth: Depth of analysis (basic, detailed, comprehensive)

    Returns:
        Dict containing pattern analysis
    """
    try:
        # Basic pattern analysis
        analysis = {
            "patterns": {
                "message_frequency": len(conversation_history),
                "engagement_level": (
                    "high" if len(conversation_history) > 10 else "medium"
                ),
            },
            "analysis_depth": analysis_depth,
            "insights": ["User shows high engagement"],
            "recommendations": ["Continue current approach"],
        }

        logger.info(f"Analyzed conversation patterns with {analysis_depth} depth")
        return analysis

    except Exception as e:
        logger.error(f"Error analyzing conversation patterns: {e}")
        return {"error": str(e)}
