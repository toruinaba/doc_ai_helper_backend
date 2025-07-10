"""
Constants and response patterns for the Mock LLM service.

This module contains all predefined responses, keywords, and constants used
by the MockLLMService to simulate realistic LLM behavior.
"""

import time
from typing import Dict, List


# Predefined response patterns for different query types
RESPONSE_PATTERNS = {
    "hello": "Hello! I'm a mock LLM assistant. How can I help you today?",
    "help": "I'm a mock LLM service used for testing. You can ask me anything, but I'll respond with predefined answers.",
    "error": "I'm simulating an error response for testing purposes.",
    "time": f"The current mock time is {time.strftime('%Y-%m-%d %H:%M:%S')}",
    "version": "Mock LLM Service v1.0.0",
}

# Keywords that trigger error simulation
ERROR_KEYWORDS = ["simulate_error", "force_error", "test_error"]

# Keywords that suggest GitHub/Git operations
GITHUB_KEYWORDS = [
    "create issue",
    "create an issue",
    "report bug",
    "report issue",
    "create pr",
    "create pull request",
    "submit pr",
    "submit a pr",
    "make pr",
    "make a pr",
    "check permissions",
    "check repository",
    "check access",
    "post to github",
    "post this to github",
    "submit to github",
    "create in github",
    "create git issue",
    "create git pr",
    "git issue",
    "git pull request",
    "github issue",
    "github pr",
    "github pull request",
]

# Keywords that suggest utility operations
UTILITY_KEYWORDS = [
    "current time",
    "what time",
    "time is",
    "clock",
    "now",
    "count",
    "character",
    "length",
    "how many",
    "word count",
    "email",
    "validate",
    "valid",
    "check email",
    "random",
    "generate",
    "random data",
    "uuid",
    "calculate",
    "math",
    "compute",
    "add",
    "subtract",
    "multiply",
    "divide",
]

# Keywords that suggest analysis operations
ANALYSIS_KEYWORDS = [
    "analyze",
    "analysis",
    "examine",
    "review",
    "study",
    "evaluate",
    "assess",
    "text",
    "document",
    "content",
    "structure",
]

# Keywords that reference previous conversation elements
PREVIOUS_QUESTION_KEYWORDS = ["前の質問", "previous question"]

PREVIOUS_ANSWER_KEYWORDS = ["前の回答", "previous answer", "last response"]

# Keywords that indicate conversation continuation
CONVERSATION_CONTINUATION_KEYWORDS = ["continue our conversation"]

# Mock template names (fallback for missing templates)
MOCK_TEMPLATE_NAMES = ["mock_template", "simple_template", "test_template"]

# Default model configurations
DEFAULT_MODELS = {
    "mock-model": {"max_tokens": 4096, "description": "Standard mock model"},
    "mock-model-large": {"max_tokens": 8192, "description": "Large context mock model"},
    "mock-model-small": {"max_tokens": 2048, "description": "Small, fast mock model"},
}

# Default streaming chunk size for mock responses
DEFAULT_CHUNK_SIZE = 15

# Token estimation ratio (characters per token)
CHARACTERS_PER_TOKEN = 4
