"""
Parameter validator for LLM requests.

This module provides validation logic for LLM request parameters,
ensuring data integrity and providing meaningful error messages.
"""

import logging
from typing import Dict, Any, List, Optional

from pydantic import ValidationError
from doc_ai_helper_backend.models.llm import (
    LLMQueryRequest,
    CoreQueryRequest,
    ToolConfiguration,
    DocumentContext,
    ProcessingOptions,
)
from doc_ai_helper_backend.core.exceptions import LLMServiceException

logger = logging.getLogger(__name__)


class ParameterValidationError(LLMServiceException):
    """Exception raised when parameter validation fails."""
    
    def __init__(self, message: str, validation_errors: Optional[List[str]] = None):
        """
        Initialize validation error.
        
        Args:
            message: Main error message
            validation_errors: List of specific validation errors
        """
        super().__init__(message=message)
        self.validation_errors = validation_errors or []


class ParameterValidator:
    """
    Validator for LLM request parameters.
    
    This class provides comprehensive validation for all parameter groups
    in the structured LLM request format.
    """
    
    SUPPORTED_PROVIDERS = ["openai", "mock"]
    MAX_PROMPT_LENGTH = 100000  # Reasonable limit for prompt length
    MAX_CONVERSATION_HISTORY = 100  # Maximum number of conversation messages
    MAX_CONTEXT_DOCUMENTS = 10  # Maximum number of context documents
    
    def validate_request(self, request: LLMQueryRequest) -> None:
        """
        Validate the complete LLM request.
        
        Args:
            request: The request to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        validation_errors = []
        
        try:
            # Validate core query parameters
            self.validate_core_query(request.query)
        except ParameterValidationError as e:
            validation_errors.extend(e.validation_errors)
        
        try:
            # Validate tool configuration if present
            if request.tools:
                self.validate_tool_configuration(request.tools)
        except ParameterValidationError as e:
            validation_errors.extend(e.validation_errors)
        
        try:
            # Validate document context if present
            if request.document:
                self.validate_document_context(request.document)
        except ParameterValidationError as e:
            validation_errors.extend(e.validation_errors)
        
        try:
            # Validate processing options if present
            if request.processing:
                self.validate_processing_options(request.processing)
        except ParameterValidationError as e:
            validation_errors.extend(e.validation_errors)
        
        # Cross-parameter validation
        try:
            self.validate_parameter_combinations(request)
        except ParameterValidationError as e:
            validation_errors.extend(e.validation_errors)
        
        if validation_errors:
            raise ParameterValidationError(
                message="Request validation failed",
                validation_errors=validation_errors
            )
    
    def validate_core_query(self, query: CoreQueryRequest) -> None:
        """
        Validate core query parameters.
        
        Args:
            query: Core query parameters to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        errors = []
        
        # Validate prompt
        if not query.prompt or not query.prompt.strip():
            errors.append("Prompt cannot be empty or contain only whitespace")
        elif len(query.prompt) > self.MAX_PROMPT_LENGTH:
            errors.append(f"Prompt exceeds maximum length of {self.MAX_PROMPT_LENGTH} characters")
        
        # Validate provider
        if query.provider.lower() not in self.SUPPORTED_PROVIDERS:
            errors.append(
                f"Unsupported provider '{query.provider}'. "
                f"Supported providers: {', '.join(self.SUPPORTED_PROVIDERS)}"
            )
        
        # Validate conversation history
        if query.conversation_history:
            if len(query.conversation_history) > self.MAX_CONVERSATION_HISTORY:
                errors.append(
                    f"Conversation history exceeds maximum length of {self.MAX_CONVERSATION_HISTORY} messages"
                )
            
            # Validate message structure
            for i, message in enumerate(query.conversation_history):
                if not message.content or not message.content.strip():
                    errors.append(f"Message {i} in conversation history has empty content")
                if message.role not in ["user", "assistant", "system"]:
                    errors.append(f"Message {i} has invalid role '{message.role}'")
        
        if errors:
            raise ParameterValidationError(
                message="Core query validation failed",
                validation_errors=errors
            )
    
    def validate_tool_configuration(self, tools: ToolConfiguration) -> None:
        """
        Validate tool configuration parameters.
        
        Args:
            tools: Tool configuration to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        errors = []
        
        # Validate tool_choice
        if tools.tool_choice:
            valid_choices = ["auto", "none", "required"]
            if tools.tool_choice not in valid_choices and not isinstance(tools.tool_choice, str):
                errors.append(
                    f"Invalid tool_choice '{tools.tool_choice}'. "
                    f"Must be one of {valid_choices} or a function name"
                )
        
        # Validate enable_tools consistency
        if not tools.enable_tools and tools.tool_choice:
            errors.append("tool_choice specified but enable_tools is False")
        
        if errors:
            raise ParameterValidationError(
                message="Tool configuration validation failed",
                validation_errors=errors
            )
    
    def validate_document_context(self, document: DocumentContext) -> None:
        """
        Validate document context parameters.
        
        Args:
            document: Document context to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        errors = []
        
        # Validate context documents
        if document.context_documents:
            if len(document.context_documents) > self.MAX_CONTEXT_DOCUMENTS:
                errors.append(
                    f"Too many context documents. Maximum allowed: {self.MAX_CONTEXT_DOCUMENTS}"
                )
            
            # Validate document paths
            for i, doc_path in enumerate(document.context_documents):
                if not doc_path or not doc_path.strip():
                    errors.append(f"Context document {i} has empty path")
                elif not isinstance(doc_path, str):
                    errors.append(f"Context document {i} path must be a string")
        
        # Validate repository context consistency
        if document.auto_include_document and not document.repository_context:
            errors.append(
                "auto_include_document is True but repository_context is not provided"
            )
        
        if errors:
            raise ParameterValidationError(
                message="Document context validation failed",
                validation_errors=errors
            )
    
    def validate_processing_options(self, processing: ProcessingOptions) -> None:
        """
        Validate processing options parameters.
        
        Args:
            processing: Processing options to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        errors = []
        
        # Validate options dictionary
        if processing.options:
            # Check for reserved option keys that might conflict
            reserved_keys = ["prompt", "messages", "tools", "tool_choice"]
            conflicting_keys = set(processing.options.keys()) & set(reserved_keys)
            if conflicting_keys:
                errors.append(
                    f"Processing options contain reserved keys: {', '.join(conflicting_keys)}"
                )
            
            # Validate temperature if present
            if "temperature" in processing.options:
                temp = processing.options["temperature"]
                if not isinstance(temp, (int, float)) or temp < 0 or temp > 2:
                    errors.append("Temperature must be a number between 0 and 2")
            
            # Validate max_tokens if present
            if "max_tokens" in processing.options:
                max_tokens = processing.options["max_tokens"]
                if not isinstance(max_tokens, int) or max_tokens <= 0:
                    errors.append("max_tokens must be a positive integer")
        
        if errors:
            raise ParameterValidationError(
                message="Processing options validation failed",
                validation_errors=errors
            )
    
    def validate_parameter_combinations(self, request: LLMQueryRequest) -> None:
        """
        Validate cross-parameter combinations and dependencies.
        
        Args:
            request: Complete request to validate
            
        Raises:
            ParameterValidationError: If validation fails
        """
        errors = []
        
        # Validate tool-related combinations
        if request.tools and request.tools.enable_tools:
            # Check if provider supports tools
            if request.query.provider.lower() == "mock":
                # Mock provider might have limited tool support
                logger.warning("Using mock provider with tools - functionality may be limited")
        
        # Validate document-related combinations (more lenient)
        if request.document and request.document.auto_include_document:
            if not request.document.repository_context:
                # This is a warning, not an error for legacy compatibility
                logger.warning(
                    "auto_include_document is True but repository_context is not provided"
                )
        
        # Validate streaming compatibility
        if request.tools and request.tools.enable_tools and request.tools.complete_tool_flow:
            # This combination is supported but may have different behavior in streaming
            pass
        
        if errors:
            raise ParameterValidationError(
                message="Parameter combination validation failed",
                validation_errors=errors
            )
    
    def sanitize_processing_options(self, processing: ProcessingOptions) -> Dict[str, Any]:
        """
        Sanitize and prepare processing options for safe use.
        
        Args:
            processing: Processing options to sanitize
            
        Returns:
            Dict[str, Any]: Sanitized options
        """
        if not processing or not processing.options:
            return {}
        
        sanitized = {}
        
        # Copy known safe options
        safe_options = [
            "temperature", "max_tokens", "top_p", "frequency_penalty", 
            "presence_penalty", "stop", "logit_bias", "user"
        ]
        
        for key, value in processing.options.items():
            if key in safe_options:
                sanitized[key] = value
            else:
                # Log unknown options but don't include them
                logger.warning(f"Unknown processing option '{key}' ignored")
        
        return sanitized
    
    def validate_legacy_conversion(self, legacy_request: Dict[str, Any]) -> None:
        """
        Validate parameters when converting from legacy format.
        
        Args:
            legacy_request: Legacy request dictionary
            
        Raises:
            ParameterValidationError: If conversion would lose important data
        """
        errors = []
        
        # Check for deprecated parameters that should be migrated
        deprecated_params = [
            "document_content", 
            "include_document_in_system_prompt", 
            "system_prompt_template"
        ]
        
        present_deprecated = [
            param for param in deprecated_params 
            if param in legacy_request and legacy_request[param] is not None
        ]
        
        if present_deprecated:
            logger.warning(
                f"Legacy request contains deprecated parameters: {present_deprecated}. "
                "Consider migrating to the new document integration approach."
            )
        
        if errors:
            raise ParameterValidationError(
                message="Legacy conversion validation failed",
                validation_errors=errors
            )