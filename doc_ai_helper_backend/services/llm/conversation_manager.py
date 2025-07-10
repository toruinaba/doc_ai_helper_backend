"""
Conversation manager for document integration via conversation history.

This module manages document content integration into LLM conversations
through conversation history injection, avoiding complex session management.
"""

import logging
from typing import Dict, List, Optional, Any

from doc_ai_helper_backend.models.repository_context import RepositoryContext
from doc_ai_helper_backend.models.document import DocumentMetadata
from doc_ai_helper_backend.models.llm import MessageItem
from doc_ai_helper_backend.services.git.factory import GitServiceFactory
from doc_ai_helper_backend.core.exceptions import GitServiceException

logger = logging.getLogger(__name__)


class ConversationManager:
    """Document integration management via conversation history."""
    
    MAX_DOCUMENT_LENGTH = 8000  # Token limit consideration
    
    def __init__(self, git_service_factory: GitServiceFactory):
        """
        Initialize ConversationManager.
        
        Args:
            git_service_factory: Factory for creating Git service instances
        """
        self.git_service_factory = git_service_factory
    
    async def create_document_aware_conversation(
        self,
        repository_context: RepositoryContext,
        initial_prompt: str,
        document_metadata: Optional[DocumentMetadata] = None
    ) -> List[MessageItem]:
        """
        Generate conversation history including document content.
        
        Args:
            repository_context: Repository context containing service, owner, repo, etc.
            initial_prompt: User's initial question/prompt
            document_metadata: Optional document metadata
        
        Returns:
            Conversation history in the following format:
            1. SYSTEM: Context information (repository, file info)
            2. ASSISTANT: Document content presentation
            3. USER: User's question
        
        Raises:
            GitServiceException: If document fetch fails
        """
        try:
            # Generate system prompt with repository context
            system_message = self._create_system_message(repository_context, document_metadata)
            
            # Fetch document content
            document_content = await self._fetch_document_content(repository_context)
            
            # Create assistant message with document content
            assistant_message = self._create_document_message(
                repository_context, document_content, document_metadata
            )
            
            # Create user message
            user_message = MessageItem(
                role="user",
                content=initial_prompt
            )
            
            logger.info(
                f"Created document-aware conversation for {repository_context.owner}/{repository_context.repo}:{repository_context.current_path}"
            )
            
            return [system_message, assistant_message, user_message]
            
        except Exception as e:
            logger.error(f"Failed to create document-aware conversation: {e}")
            # Return fallback conversation
            return self._create_fallback_conversation(repository_context, initial_prompt, str(e))
    
    def is_initial_request(
        self, 
        conversation_history: Optional[List[MessageItem]],
        repository_context: Optional[RepositoryContext]
    ) -> bool:
        """
        Determine if this is an initial request that needs document integration.
        
        Args:
            conversation_history: Existing conversation history
            repository_context: Repository context
        
        Returns:
            bool: True if this is an initial request requiring document integration
        """
        # If no repository context, not a document-related request
        if not repository_context:
            return False
        
        # If no conversation history, this is initial request
        if not conversation_history:
            return True
        
        # If conversation history exists but is empty, this is initial request
        if len(conversation_history) == 0:
            return True
        
        # If conversation history has content, check if it already contains document content
        # Look for assistant message that contains document content indicator
        for message in conversation_history:
            if (message.role == "assistant" and 
                message.content and 
                "Document content:" in message.content):
                return False
        
        return True
    
    async def _fetch_document_content(self, repository_context: RepositoryContext) -> str:
        """
        Fetch document content using GitService.
        
        Args:
            repository_context: Repository context
        
        Returns:
            str: Document content (truncated if necessary)
        
        Raises:
            GitServiceException: If document fetch fails
        """
        try:
            # Create Git service using factory
            git_service = self.git_service_factory.create(
                repository_context.service,
                access_token=getattr(repository_context, 'access_token', None)
            )
            
            # Get document from repository
            document_response = await git_service.get_document(
                owner=repository_context.owner,
                repo=repository_context.repo,
                path=repository_context.current_path,
                ref=repository_context.ref or "main"
            )
            
            content = document_response.content.content
            
            # Truncate if content is too long
            if len(content) > self.MAX_DOCUMENT_LENGTH:
                truncated_content = content[:self.MAX_DOCUMENT_LENGTH]
                truncated_content += f"\n\n[Content truncated - showing first {self.MAX_DOCUMENT_LENGTH} characters]"
                logger.warning(
                    f"Document content truncated from {len(content)} to {self.MAX_DOCUMENT_LENGTH} characters"
                )
                return truncated_content
            
            return content
            
        except Exception as e:
            logger.error(f"Failed to fetch document content: {e}")
            raise GitServiceException(f"Document fetch failed: {str(e)}")
    
    def _create_system_message(
        self, 
        repository_context: RepositoryContext, 
        document_metadata: Optional[DocumentMetadata]
    ) -> MessageItem:
        """
        Create system message with repository and document context.
        
        Args:
            repository_context: Repository context
            document_metadata: Optional document metadata
        
        Returns:
            MessageItem: System message
        """
        system_content = f"""You are a document assistant for the repository {repository_context.owner}/{repository_context.repo}.

Current document: {repository_context.current_path}
Branch/Reference: {repository_context.ref or 'main'}
Git Service: {repository_context.service}"""

        if document_metadata:
            # Handle different DocumentMetadata types
            if hasattr(document_metadata, 'content_type'):
                # DocumentMetadata from document.py
                system_content += f"""
Content Type: {document_metadata.content_type}
Last Modified: {document_metadata.last_modified}
Size: {document_metadata.size} bytes"""
                
                if document_metadata.extra and "frontmatter" in document_metadata.extra:
                    system_content += f"\nDocument Frontmatter: {document_metadata.extra['frontmatter']}"
            else:
                # DocumentMetadata from repository_context.py
                system_content += f"""
Document Type: {document_metadata.type}
Last Modified: {document_metadata.last_modified or 'Unknown'}"""
                if hasattr(document_metadata, 'file_size') and document_metadata.file_size:
                    system_content += f"\nSize: {document_metadata.file_size} bytes"
                if document_metadata.title:
                    system_content += f"\nTitle: {document_metadata.title}"

        system_content += """

The document content has been loaded and is available in the conversation history. You can reference this content to answer questions, provide summaries, create issues, or perform other document-related tasks."""

        return MessageItem(
            role="system",
            content=system_content
        )
    
    def _create_document_message(
        self, 
        repository_context: RepositoryContext, 
        document_content: str,
        document_metadata: Optional[DocumentMetadata]
    ) -> MessageItem:
        """
        Create assistant message presenting document content.
        
        Args:
            repository_context: Repository context
            document_content: Raw document content
            document_metadata: Optional document metadata
        
        Returns:
            MessageItem: Assistant message with document content
        """
        message_content = f"""Document content from {repository_context.current_path}:

```
{document_content}
```

This document is ready for analysis, summarization, or any other operations you'd like to perform."""

        return MessageItem(
            role="assistant", 
            content=message_content
        )
    
    def _create_fallback_conversation(
        self, 
        repository_context: RepositoryContext, 
        initial_prompt: str, 
        error_message: str
    ) -> List[MessageItem]:
        """
        Create fallback conversation for error cases.
        
        Args:
            repository_context: Repository context
            initial_prompt: User's initial prompt
            error_message: Error message from document fetch
        
        Returns:
            List[MessageItem]: Fallback conversation history
        """
        system_message = MessageItem(
            role="system",
            content=f"""Document assistant for {repository_context.owner}/{repository_context.repo}.

⚠️ Unable to load document content from {repository_context.current_path}:
{error_message}

I can still help with general questions about the repository or document, but I won't have access to the specific document content."""
        )
        
        user_message = MessageItem(
            role="user",
            content=initial_prompt
        )
        
        logger.info(f"Created fallback conversation due to error: {error_message}")
        
        return [system_message, user_message]