"""
Backward compatibility layer for LLM service refactoring.

This module provides utilities to help existing code work with the new
structured request format while maintaining backward compatibility.
"""

import logging
from typing import Optional
from functools import wraps

from doc_ai_helper_backend.models.llm import LLMQueryRequest, LLMResponse
from doc_ai_helper_backend.services.llm.query_processor import QueryProcessor
from doc_ai_helper_backend.services.llm.parameter_validator import ParameterValidator
from doc_ai_helper_backend.services.llm.conversation_manager import ConversationManager

logger = logging.getLogger(__name__)


class CompatibilityProcessor:
    """
    Processor that bridges legacy and new request formats.
    
    This class allows existing endpoints to gradually migrate to the new
    infrastructure while maintaining backward compatibility.
    """
    
    def __init__(self, conversation_manager: ConversationManager):
        """
        Initialize compatibility processor.
        
        Args:
            conversation_manager: Conversation manager for document integration
        """
        self.query_processor = QueryProcessor(conversation_manager)
        self.validator = ParameterValidator()
    
    async def process_legacy_request(
        self, 
        legacy_request: LLMQueryRequest,
        use_new_infrastructure: bool = True
    ) -> LLMResponse:
        """
        Process legacy request using either new or old infrastructure.
        
        Args:
            legacy_request: Legacy format request
            use_new_infrastructure: Whether to use new processing infrastructure
            
        Returns:
            LLMResponse: Response from LLM
        """
        if use_new_infrastructure:
            logger.debug("Processing legacy request using new infrastructure")
            
            # Convert to new format
            v2_request = LLMQueryRequest.from_legacy_request(legacy_request)
            
            # Validate converted request
            self.validator.validate_request(v2_request)
            
            # Process using new infrastructure
            return await self.query_processor.execute_query(v2_request, streaming=False)
        else:
            logger.debug("Processing legacy request using original infrastructure")
            # This would call the original processing logic
            # For now, we'll use the new infrastructure anyway
            return await self.process_legacy_request(legacy_request, use_new_infrastructure=True)
    
    def should_use_new_infrastructure(self, request: LLMQueryRequest) -> bool:
        """
        Determine whether to use new infrastructure for a legacy request.
        
        This method can implement logic to gradually roll out the new infrastructure
        based on various criteria (feature flags, request characteristics, etc.).
        
        Args:
            request: Legacy request to evaluate
            
        Returns:
            bool: True if new infrastructure should be used
        """
        # For now, always use new infrastructure
        # In practice, this could be controlled by feature flags, A/B testing, etc.
        return True
    
    def get_migration_status(self, request: LLMQueryRequest) -> dict:
        """
        Get migration status information for a legacy request.
        
        Args:
            request: Legacy request to analyze
            
        Returns:
            dict: Migration status and recommendations
        """
        status = {
            "uses_legacy_format": True,
            "can_migrate_to_v2": True,
            "migration_warnings": [],
            "migration_recommendations": [],
        }
        
        # Check for deprecated parameters
        if hasattr(request, 'document_content') and request.document_content:
            status["migration_warnings"].append(
                "Uses deprecated 'document_content' parameter"
            )
            status["migration_recommendations"].append(
                "Migrate to conversation-based document integration"
            )
        
        if (hasattr(request, 'include_document_in_system_prompt') and 
            not request.include_document_in_system_prompt):
            status["migration_warnings"].append(
                "Uses deprecated 'include_document_in_system_prompt' parameter"
            )
        
        if (hasattr(request, 'system_prompt_template') and 
            request.system_prompt_template != "contextual_document_assistant_ja"):
            status["migration_warnings"].append(
                "Uses deprecated 'system_prompt_template' parameter"
            )
        
        # Analyze parameter complexity
        param_count = len([
            field for field, value in request.__dict__.items() 
            if value is not None and field != 'prompt'
        ])
        
        if param_count > 5:
            status["migration_recommendations"].append(
                f"Complex request with {param_count} parameters - would benefit from v2 structure"
            )
        
        return status


def enable_v2_infrastructure(func):
    """
    Decorator to enable v2 infrastructure for legacy endpoints.
    
    This decorator can be applied to existing endpoint functions to gradually
    migrate them to use the new infrastructure.
    """
    @wraps(func)
    async def wrapper(*args, **kwargs):
        # Extract request from arguments
        request = None
        for arg in args:
            if isinstance(arg, LLMQueryRequest):
                request = arg
                break
        
        if request is None:
            # No LLMQueryRequest found, proceed with original function
            return await func(*args, **kwargs)
        
        # Check if we should use new infrastructure
        # This could be controlled by feature flags, environment variables, etc.
        use_v2 = True  # For now, always use v2
        
        if use_v2:
            logger.info("Using v2 infrastructure for legacy endpoint")
            
            # Create compatibility processor
            conversation_manager = None
            for arg in args:
                if isinstance(arg, ConversationManager):
                    conversation_manager = arg
                    break
            
            if conversation_manager:
                processor = CompatibilityProcessor(conversation_manager)
                return await processor.process_legacy_request(request)
        
        # Fall back to original function
        return await func(*args, **kwargs)
    
    return wrapper


class MigrationHelper:
    """
    Helper class for migrating from legacy to v2 format.
    
    This class provides utilities to help developers understand the
    differences between legacy and v2 formats and migrate their code.
    """
    
    @staticmethod
    def convert_legacy_to_v2(legacy_request: LLMQueryRequest) -> LLMQueryRequest:
        """
        Convert legacy request to v2 format with detailed logging.
        
        Args:
            legacy_request: Legacy format request
            
        Returns:
            LLMQueryRequest: Converted request
        """
        logger.info("Converting legacy request to v2 format")
        
        v2_request = LLMQueryRequest.from_legacy_request(legacy_request)
        
        # Log the conversion details
        conversion_details = {
            "original_param_count": len([
                field for field, value in legacy_request.__dict__.items() 
                if value is not None
            ]),
            "converted_groups": []
        }
        
        if v2_request.tools:
            conversion_details["converted_groups"].append("tools")
        if v2_request.document:
            conversion_details["converted_groups"].append("document")
        if v2_request.processing:
            conversion_details["converted_groups"].append("processing")
        
        logger.debug(f"Conversion details: {conversion_details}")
        
        return v2_request
    
    @staticmethod
    def convert_v2_to_legacy(v2_request: LLMQueryRequest) -> LLMQueryRequest:
        """
        Convert v2 request to legacy format.
        
        Args:
            v2_request: v2 format request
            
        Returns:
            LLMQueryRequest: Converted legacy request
        """
        logger.info("Converting v2 request to legacy format")
        return v2_request.to_legacy_request()
    
    @staticmethod
    def analyze_migration_complexity(legacy_request: LLMQueryRequest) -> dict:
        """
        Analyze the complexity of migrating a legacy request.
        
        Args:
            legacy_request: Legacy request to analyze
            
        Returns:
            dict: Migration complexity analysis
        """
        analysis = {
            "complexity": "simple",
            "factors": [],
            "estimated_effort": "low",
            "benefits": []
        }
        
        # Count non-default parameters
        non_default_params = 0
        for field, value in legacy_request.__dict__.items():
            if value is not None and field != 'prompt':
                non_default_params += 1
        
        if non_default_params > 8:
            analysis["complexity"] = "high"
            analysis["estimated_effort"] = "high"
            analysis["factors"].append(f"High parameter count: {non_default_params}")
            analysis["benefits"].append("Significant improvement in maintainability")
        elif non_default_params > 4:
            analysis["complexity"] = "medium"
            analysis["estimated_effort"] = "medium"
            analysis["factors"].append(f"Medium parameter count: {non_default_params}")
            analysis["benefits"].append("Improved parameter organization")
        else:
            analysis["benefits"].append("Better validation and error handling")
        
        # Check for tools usage
        if legacy_request.enable_tools:
            analysis["factors"].append("Uses function calling/tools")
            analysis["benefits"].append("Cleaner tool configuration")
        
        # Check for document integration
        if (legacy_request.repository_context or 
            legacy_request.document_metadata or 
            legacy_request.context_documents):
            analysis["factors"].append("Uses document integration")
            analysis["benefits"].append("Improved document handling")
        
        return analysis


# Global compatibility processor instance for easy access
_compatibility_processor: Optional[CompatibilityProcessor] = None

def get_compatibility_processor(conversation_manager: ConversationManager) -> CompatibilityProcessor:
    """Get or create global compatibility processor instance."""
    global _compatibility_processor
    if _compatibility_processor is None:
        _compatibility_processor = CompatibilityProcessor(conversation_manager)
    return _compatibility_processor