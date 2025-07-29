"""
Conversation History Optimization

会話履歴の最適化とトークン管理機能を提供します。
"""

import logging
from typing import Dict, Any, Optional, List

from doc_ai_helper_backend.models.llm import MessageItem, MessageRole

logger = logging.getLogger(__name__)


def estimate_message_tokens(message: MessageItem, encoding_name: str = "cl100k_base") -> int:
    """Estimate token count for a single message"""
    try:
        import tiktoken
        encoding = tiktoken.get_encoding(encoding_name)
        return len(encoding.encode(f"{message.role.value}: {message.content}"))
    except ImportError:
        # Fallback if tiktoken is not available
        return len(message.content) // 4  # Rough approximation: 4 chars ≈ 1 token


def optimize_conversation_history(
    history: List[MessageItem],
    max_tokens: int = 4000,
    preserve_recent: int = 2,
    encoding_name: str = "cl100k_base",
) -> tuple[List[MessageItem], Dict[str, Any]]:
    """
    Optimize conversation history to fit within token limits.
    
    When conversation history exceeds the specified token count,
    removes the oldest messages first while always preserving
    the specified number of most recent messages.
    """
    if not history:
        return [], {"was_optimized": False, "reason": "Empty history"}

    # Estimate total tokens
    total_tokens = sum(estimate_message_tokens(msg, encoding_name) for msg in history)
    
    if total_tokens <= max_tokens:
        return history, {
            "was_optimized": False,
            "reason": "History within token limit",
            "original_messages": len(history),
            "final_messages": len(history),
            "original_tokens": total_tokens,
            "final_tokens": total_tokens,
            "removed_messages": 0,
        }

    # Need to optimize - preserve recent messages and fit as many older ones as possible
    if len(history) <= preserve_recent:
        # Can't remove any messages due to preserve_recent constraint
        recent_tokens = sum(estimate_message_tokens(msg, encoding_name) for msg in history[-preserve_recent:])
        return history, {
            "was_optimized": False,
            "reason": f"Cannot optimize: only {len(history)} messages, preserve_recent={preserve_recent}",
            "original_messages": len(history),
            "final_messages": len(history),
            "original_tokens": total_tokens,
            "final_tokens": recent_tokens,
            "removed_messages": 0,
        }

    # Keep recent messages
    recent_messages = history[-preserve_recent:]
    recent_tokens = sum(estimate_message_tokens(msg, encoding_name) for msg in recent_messages)
    
    if recent_tokens > max_tokens:
        # Even recent messages exceed limit - return them anyway as they're required
        return recent_messages, {
            "was_optimized": True,
            "reason": f"Recent {preserve_recent} messages exceed token limit",
            "original_messages": len(history),
            "final_messages": len(recent_messages),
            "original_tokens": total_tokens,
            "final_tokens": recent_tokens,
            "removed_messages": len(history) - len(recent_messages),
        }
    
    # Add older messages until we approach the limit
    available_tokens = max_tokens - recent_tokens
    older_messages = history[:-preserve_recent]
    
    # Try to include as many older messages as possible (starting from most recent older messages)
    included_older = []
    current_tokens = 0
    
    for msg in reversed(older_messages):
        msg_tokens = estimate_message_tokens(msg, encoding_name)
        if current_tokens + msg_tokens <= available_tokens:
            included_older.insert(0, msg)  # Insert at beginning to maintain order
            current_tokens += msg_tokens
        else:
            break
    
    final_history = included_older + recent_messages
    final_tokens = current_tokens + recent_tokens
    
    return final_history, {
        "was_optimized": True,
        "reason": "Removed oldest messages to fit token limit",
        "original_messages": len(history),
        "final_messages": len(final_history),
        "original_tokens": total_tokens,
        "final_tokens": final_tokens,
        "removed_messages": len(history) - len(final_history),
    }


def build_conversation_messages(
    prompt: str,
    conversation_history: Optional[List[MessageItem]] = None,
    system_prompt: Optional[str] = None,
) -> List[MessageItem]:
    """
    Build conversation messages for LLM API call.
    
    Args:
        prompt: User's current prompt
        conversation_history: Previous conversation messages
        system_prompt: System prompt to include
        
    Returns:
        List of messages formatted for LLM API
    """
    messages = []
    
    # Add system prompt if provided
    if system_prompt:
        messages.append(MessageItem(role=MessageRole.SYSTEM, content=system_prompt))
    
    # Add conversation history if provided
    if conversation_history:
        messages.extend(conversation_history)
    
    # Add current user prompt
    messages.append(MessageItem(role=MessageRole.USER, content=prompt))
    
    return messages