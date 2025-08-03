"""
Document service for processing and retrieving documents.
"""

import logging
import os
from typing import Dict, List, Optional
from urllib.parse import urljoin

from doc_ai_helper_backend.core.exceptions import (
    DocumentParsingException,
    GitServiceException,
    GitHubRepositoryNotFoundError,
    NotFoundException,
)
from doc_ai_helper_backend.models.document import (
    DocumentResponse,
    DocumentType,
    RepositoryStructureResponse,
)
from doc_ai_helper_backend.models.link_info import LinkInfo
from doc_ai_helper_backend.services.document.processors.factory import (
    DocumentProcessorFactory,
)
from doc_ai_helper_backend.services.git.factory import GitServiceFactory

# Logger
logger = logging.getLogger("doc_ai_helper")


class DocumentService:
    """Service for processing and retrieving documents."""

    def __init__(self, cache_service=None):
        """Initialize document service.

        Args:
            cache_service: Cache service for caching documents and repository structures
        """
        self.cache_service = cache_service

    async def get_document(
        self,
        service: str,
        owner: str,
        repo: str,
        path: str,
        ref: str = "main",
        use_cache: bool = True,
        transform_links: bool = True,
        base_url: Optional[str] = None,
        root_path: Optional[str] = None,
    ) -> DocumentResponse:
        """Get document from a Git repository.

        Args:
            service: Git service type (github, gitlab, etc.)
            owner: Repository owner
            repo: Repository name
            path: Document path
            ref: Branch or tag name. Default is "main"
            use_cache: Whether to use cache. Default is True
            transform_links: Whether to transform image and static resource links to CDN URLs. Default is True
            base_url: Base URL for link transformation. If None, will be constructed from request parameters
            root_path: Root directory path for link resolution. If specified, relative links are resolved from this directory

        Returns:
            DocumentResponse: Document data

        Raises:
            NotFoundException: If document is not found
            GitServiceException: If there is an error with the Git service
            DocumentParsingException: If there is an error parsing the document
        """
        logger.info(f"Getting document from {service}/{owner}/{repo}/{path} at {ref}")

        # Check cache if enabled
        if use_cache and self.cache_service:
            cache_key = f"document:{service}:{owner}:{repo}:{path}:{ref}"
            cached_doc = await self.cache_service.get(cache_key)
            if cached_doc:
                logger.info(f"Document found in cache: {cache_key}")
                return cached_doc

        try:
            # Get Git service
            git_service = GitServiceFactory.create(service)

            # Get document from Git service
            document = await git_service.get_document(owner, repo, path, ref)

            # Determine document type
            file_extension = os.path.splitext(path)[1].lower()
            if file_extension in [".md", ".markdown"]:
                document_type = DocumentType.MARKDOWN
            elif file_extension in [".html", ".htm"]:
                document_type = DocumentType.HTML
            else:
                document_type = DocumentType.OTHER

            # Process document with appropriate processor
            try:
                # Get document processor
                processor = DocumentProcessorFactory.create(document_type)

                # Extract raw content from document
                raw_content = document.content.content

                # Process content
                processed_content = processor.process_content(raw_content, path)
                document.content = processed_content

                # Extract metadata
                processed_metadata = processor.extract_metadata(raw_content, path)
                if processed_metadata:
                    document.metadata.extra = processed_metadata

                # Extract links
                links = processor.extract_links(raw_content, path)

                # Transform links if requested
                if transform_links:
                    # Always construct base URL from request parameters (ignore provided base_url)
                    # Note: ref is handled as query parameter, not in the path
                    base_url = (
                        f"/api/v1/documents/contents/{service}/{owner}/{repo}"
                    )

                    transformed_content = processor.transform_links(
                        raw_content, path, base_url, service, owner, repo, ref, root_path
                    )
                    # Store transformed content
                    document.transformed_content = transformed_content

                # Add links to document
                document.links = links

            except Exception as e:
                logger.error(f"Error processing document: {str(e)}")
                # Fallback to original document if processing fails
                pass

            # Cache document if cache is enabled
            if use_cache and self.cache_service:
                cache_key = f"document:{service}:{owner}:{repo}:{path}:{ref}"
                await self.cache_service.set(cache_key, document)

            return document

        except GitHubRepositoryNotFoundError as e:
            logger.warning(f"Repository not found: {service}/{owner}/{repo}")
            raise
        except NotFoundException as e:
            logger.warning(f"Document not found: {service}/{owner}/{repo}/{path}")
            raise
        except GitServiceException as e:
            logger.error(f"Git service error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting document: {str(e)}")
            raise DocumentParsingException(f"Error processing document: {str(e)}")

    async def get_repository_structure(
        self,
        service: str,
        owner: str,
        repo: str,
        ref: str = "main",
        path: str = "",
        use_cache: bool = True,
    ) -> RepositoryStructureResponse:
        """Get repository structure.

        Args:
            service: Git service type (github, gitlab, etc.)
            owner: Repository owner
            repo: Repository name
            ref: Branch or tag name. Default is "main"
            path: Path prefix to filter by. Default is ""
            use_cache: Whether to use cache. Default is True

        Returns:
            RepositoryStructureResponse: Repository structure data

        Raises:
            NotFoundException: If repository is not found
            GitServiceException: If there is an error with the Git service
        """
        logger.info(
            f"Getting structure of {service}/{owner}/{repo} at {ref}, path: {path}"
        )

        # Check cache if enabled
        if use_cache and self.cache_service:
            cache_key = f"structure:{service}:{owner}:{repo}:{ref}:{path}"
            cached_structure = await self.cache_service.get(cache_key)
            if cached_structure:
                logger.info(f"Repository structure found in cache: {cache_key}")
                return cached_structure

        try:
            # Get Git service
            git_service = GitServiceFactory.create(service)

            # Get repository structure from Git service
            structure = await git_service.get_repository_structure(
                owner, repo, ref, path
            )

            # Cache repository structure if cache is enabled
            if use_cache and self.cache_service:
                cache_key = f"structure:{service}:{owner}:{repo}:{ref}:{path}"
                await self.cache_service.set(cache_key, structure)

            return structure

        except GitHubRepositoryNotFoundError as e:
            logger.warning(f"Repository not found: {service}/{owner}/{repo}")
            raise
        except NotFoundException as e:
            logger.warning(f"Repository not found: {service}/{owner}/{repo}")
            raise
        except GitServiceException as e:
            logger.error(f"Git service error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error getting repository structure: {str(e)}")
            raise GitServiceException(
                f"Error processing repository structure: {str(e)}"
            )

    async def search_repository(
        self, service: str, owner: str, repo: str, query: str, limit: int = 10
    ) -> Dict:
        """Search repository.

        Args:
            service: Git service type (github, gitlab, etc.)
            owner: Repository owner
            repo: Repository name
            query: Search query
            limit: Maximum number of results. Default is 10

        Returns:
            Dict: Search results

        Raises:
            NotFoundException: If repository is not found
            GitServiceException: If there is an error with the Git service
        """
        logger.info(f"Searching {service}/{owner}/{repo} for '{query}'")

        try:
            # Get Git service
            git_service = GitServiceFactory.create(service)

            # Check if repository exists
            if not await git_service.check_repository_exists(owner, repo):
                raise NotFoundException(f"Repository not found: {owner}/{repo}")

            # Search repository
            results = await git_service.search_repository(owner, repo, query, limit)

            return {
                "service": service,
                "owner": owner,
                "repo": repo,
                "query": query,
                "limit": limit,
                "results": results,
            }

        except NotFoundException as e:
            logger.warning(f"Repository not found: {service}/{owner}/{repo}")
            raise
        except GitServiceException as e:
            logger.error(f"Git service error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error searching repository: {str(e)}")
            raise GitServiceException(f"Error searching repository: {str(e)}")

    async def check_repository_exists(
        self, service: str, owner: str, repo: str
    ) -> bool:
        """Check if repository exists.

        Args:
            service: Git service type (github, gitlab, etc.)
            owner: Repository owner
            repo: Repository name

        Returns:
            bool: True if repository exists, False otherwise

        Raises:
            GitServiceException: If there is an error with the Git service
        """
        logger.info(f"Checking if repository exists: {service}/{owner}/{repo}")

        try:
            # Get Git service
            git_service = GitServiceFactory.create(service)

            # Check if repository exists
            return await git_service.check_repository_exists(owner, repo)

        except GitServiceException as e:
            logger.error(f"Git service error: {str(e)}")
            raise
        except Exception as e:
            logger.error(f"Error checking if repository exists: {str(e)}")
            raise GitServiceException(f"Error checking if repository exists: {str(e)}")
