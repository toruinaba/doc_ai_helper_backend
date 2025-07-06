"""LLMサービスの機能コンポーネント

このモジュールは、LLMサービスの各機能を独立したコンポーネントとして提供します。
Pure delegation patternを使用してmixin継承を排除し、明確な責任分離を実現します。
"""

"""LLMサービスの機能コンポーネント

このモジュールは、LLMサービスの各機能を独立したコンポーネントとして提供します。
Pure delegation patternを使用してmixin継承を排除し、明確な責任分離を実現します。
"""

# コンポーネントのインポート
from .cache import LLMCacheService
from .templates import PromptTemplateManager
from .messaging import MessageBuilder, SystemPromptBuilder, SystemPromptCache
from .functions import (
    FunctionService,
    FunctionRegistry,
    FunctionCallManager,
    validate_function_call_arguments,
    execute_function_safely,
)
from .response_builder import ResponseBuilder, LLMResponseBuilder
from .tokens import TokenCounter
from .streaming_utils import StreamingUtils
from .query_manager import QueryManager

# エクスポートリスト
__all__ = [
    "LLMCacheService",
    "PromptTemplateManager",
    "MessageBuilder",
    "SystemPromptBuilder",
    "SystemPromptCache",
    "FunctionService",
    "FunctionRegistry",
    "FunctionCallManager",
    "validate_function_call_arguments",
    "execute_function_safely",
    "ResponseBuilder",
    "LLMResponseBuilder",  # 後方互換性
    "TokenCounter",
    "StreamingUtils",
    "QueryManager",
]

# バージョン情報
__version__ = "1.0.0"
__author__ = "doc_ai_helper_backend team"
__description__ = "LLM service components with pure delegation pattern"
