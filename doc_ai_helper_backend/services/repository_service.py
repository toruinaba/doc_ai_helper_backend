"""
Repository management service.

This module provides CRUD operations for repository management with
delegation pattern support for RepositoryContext creation.
"""

import logging
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import IntegrityError

from ..core.exceptions import RepositoryServiceException
from ..db.models import Repository as RepositoryModel
from ..models.repository import (
    GitServiceType,
    RepositoryCreate,
    RepositoryResponse,
    RepositoryUpdate,
)
from ..models.repository_context import RepositoryContext

logger = logging.getLogger(__name__)


class RepositoryService:
    """
    Repository management service with CRUD operations.
    
    Supports the delegation pattern where RepositoryResponse can
    create RepositoryContext instances for LLM integration.
    """

    def __init__(self, db: AsyncSession):
        """
        Initialize repository service.
        
        Args:
            db: Database session
        """
        self.db = db

    async def create_repository(self, repo_data: RepositoryCreate) -> RepositoryResponse:
        """
        Create a new repository.
        
        Args:
            repo_data: Repository creation data
            
        Returns:
            Created repository response
            
        Raises:
            RepositoryServiceException: If creation fails
        """
        try:
            # Convert Pydantic model to SQLAlchemy model
            db_repo = RepositoryModel(
                name=repo_data.name,
                owner=repo_data.owner,
                service_type=repo_data.service_type.value,
                url=str(repo_data.url),
                base_url=repo_data.base_url,
                default_branch=repo_data.default_branch,
                root_path=repo_data.root_path,
                description=repo_data.description,
                is_public=repo_data.is_public,
                access_token_encrypted=self._encrypt_token(repo_data.access_token) if repo_data.access_token else None,
                supported_branches_json=["main"],  # Default, will be updated later
                repo_metadata=repo_data.metadata or {},
            )

            self.db.add(db_repo)
            await self.db.commit()
            await self.db.refresh(db_repo)

            logger.info(
                f"Created repository: {repo_data.service_type.value}/{repo_data.owner}/{repo_data.name}"
            )

            return self._to_response(db_repo)

        except IntegrityError as e:
            await self.db.rollback()
            error_msg = f"Repository already exists: {repo_data.service_type.value}/{repo_data.owner}/{repo_data.name}"
            logger.error(f"{error_msg} - {str(e)}")
            raise RepositoryServiceException(error_msg) from e
        except Exception as e:
            await self.db.rollback()
            error_msg = f"Failed to create repository: {str(e)}"
            logger.error(error_msg)
            raise RepositoryServiceException(error_msg) from e

    async def get_repository(self, repository_id: int) -> Optional[RepositoryResponse]:
        """
        Get repository by ID.
        
        Args:
            repository_id: Repository ID
            
        Returns:
            Repository response or None if not found
        """
        try:
            result = await self.db.execute(
                select(RepositoryModel).where(RepositoryModel.id == repository_id)
            )
            db_repo = result.scalar_one_or_none()

            if not db_repo:
                logger.warning(f"Repository not found: ID {repository_id}")
                return None

            return self._to_response(db_repo)

        except Exception as e:
            error_msg = f"Failed to get repository {repository_id}: {str(e)}"
            logger.error(error_msg)
            raise RepositoryServiceException(error_msg) from e

    async def list_repositories(
        self, skip: int = 0, limit: int = 100
    ) -> List[RepositoryResponse]:
        """
        List repositories with pagination.
        
        Args:
            skip: Number of records to skip
            limit: Maximum number of records to return
            
        Returns:
            List of repository responses
        """
        try:
            result = await self.db.execute(
                select(RepositoryModel)
                .offset(skip)
                .limit(limit)
                .order_by(RepositoryModel.created_at.desc())
            )
            repositories = result.scalars().all()

            return [self._to_response(repo) for repo in repositories]

        except Exception as e:
            error_msg = f"Failed to list repositories: {str(e)}"
            logger.error(error_msg)
            raise RepositoryServiceException(error_msg) from e

    async def update_repository(
        self, repository_id: int, updates: RepositoryUpdate
    ) -> Optional[RepositoryResponse]:
        """
        Update repository.
        
        Args:
            repository_id: Repository ID
            updates: Update data
            
        Returns:
            Updated repository response or None if not found
        """
        try:
            result = await self.db.execute(
                select(RepositoryModel).where(RepositoryModel.id == repository_id)
            )
            db_repo = result.scalar_one_or_none()

            if not db_repo:
                logger.warning(f"Repository not found for update: ID {repository_id}")
                return None

            # Update fields that are provided
            update_data = updates.model_dump(exclude_unset=True)
            for field, value in update_data.items():
                if field == "service_type" and value:
                    setattr(db_repo, field, value.value)
                elif field == "url" and value:
                    setattr(db_repo, field, str(value))
                elif field == "access_token" and value:
                    setattr(db_repo, "access_token_encrypted", self._encrypt_token(value))
                elif field == "metadata" and value:
                    setattr(db_repo, "repo_metadata", value)
                elif field not in ["access_token", "metadata"]:
                    setattr(db_repo, field, value)

            await self.db.commit()
            await self.db.refresh(db_repo)

            logger.info(f"Updated repository: ID {repository_id}")
            return self._to_response(db_repo)

        except IntegrityError as e:
            await self.db.rollback()
            error_msg = f"Repository update failed due to constraint violation: {str(e)}"
            logger.error(error_msg)
            raise RepositoryServiceException(error_msg) from e
        except Exception as e:
            await self.db.rollback()
            error_msg = f"Failed to update repository {repository_id}: {str(e)}"
            logger.error(error_msg)
            raise RepositoryServiceException(error_msg) from e

    async def delete_repository(self, repository_id: int) -> bool:
        """
        Delete repository.
        
        Args:
            repository_id: Repository ID
            
        Returns:
            True if deleted, False if not found
        """
        try:
            result = await self.db.execute(
                select(RepositoryModel).where(RepositoryModel.id == repository_id)
            )
            db_repo = result.scalar_one_or_none()

            if not db_repo:
                logger.warning(f"Repository not found for deletion: ID {repository_id}")
                return False

            await self.db.delete(db_repo)
            await self.db.commit()

            logger.info(f"Deleted repository: ID {repository_id}")
            return True

        except Exception as e:
            await self.db.rollback()
            error_msg = f"Failed to delete repository {repository_id}: {str(e)}"
            logger.error(error_msg)
            raise RepositoryServiceException(error_msg) from e

    async def find_by_context(self, context: RepositoryContext) -> Optional[RepositoryResponse]:
        """
        Find repository by RepositoryContext.
        
        This enables integration with existing LLM workflows that use RepositoryContext.
        
        Args:
            context: Repository context from LLM queries
            
        Returns:
            Repository response or None if not found
        """
        try:
            result = await self.db.execute(
                select(RepositoryModel).where(
                    RepositoryModel.service_type == context.service.value,
                    RepositoryModel.owner == context.owner,
                    RepositoryModel.name == context.repo,
                )
            )
            db_repo = result.scalar_one_or_none()

            if not db_repo:
                logger.info(
                    f"Repository not found by context: {context.service.value}/{context.owner}/{context.repo}"
                )
                return None

            return self._to_response(db_repo)

        except Exception as e:
            error_msg = f"Failed to find repository by context: {str(e)}"
            logger.error(error_msg)
            raise RepositoryServiceException(error_msg) from e

    def _to_response(self, db_repo: RepositoryModel) -> RepositoryResponse:
        """
        Convert SQLAlchemy model to Pydantic response model.
        
        Args:
            db_repo: SQLAlchemy repository model
            
        Returns:
            Repository response model
        """
        return RepositoryResponse(
            id=db_repo.id,
            name=db_repo.name,
            owner=db_repo.owner,
            service_type=GitServiceType(db_repo.service_type),
            url=db_repo.url,
            base_url=db_repo.base_url,
            default_branch=db_repo.default_branch,
            root_path=db_repo.root_path,
            description=db_repo.description,
            is_public=db_repo.is_public,
            supported_branches=db_repo.supported_branches_json or ["main"],
            metadata=db_repo.repo_metadata or {},
            created_at=db_repo.created_at,
            updated_at=db_repo.updated_at,
        )

    def _encrypt_token(self, token: str) -> str:
        """
        Encrypt access token for storage.
        
        TODO: Implement proper encryption. For now, this is a placeholder.
        
        Args:
            token: Plain text token
            
        Returns:
            Encrypted token
        """
        # PLACEHOLDER: In production, use proper encryption
        # e.g., Fernet, AWS KMS, or other encryption service
        return f"encrypted_{token}"

    def _decrypt_token(self, encrypted_token: str) -> str:
        """
        Decrypt access token.
        
        TODO: Implement proper decryption. For now, this is a placeholder.
        
        Args:
            encrypted_token: Encrypted token
            
        Returns:
            Plain text token
        """
        # PLACEHOLDER: In production, use proper decryption
        if encrypted_token.startswith("encrypted_"):
            return encrypted_token[10:]  # Remove "encrypted_" prefix
        return encrypted_token