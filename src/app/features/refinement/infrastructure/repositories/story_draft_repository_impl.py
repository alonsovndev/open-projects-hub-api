"""Story draft repository implementation using SQLAlchemy."""

import time
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import OperationalError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.infrastructure.mappers.story_draft_mapper import StoryDraftMapper
from src.app.features.refinement.infrastructure.models.story_draft_model import StoryDraftModel
from src.app.shared.logging import TechnicalLogger, get_logger


class StoryDraftRepositoryImpl(StoryDraftRepository):
    """SQLAlchemy implementation of StoryDraftRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session
        self._log = TechnicalLogger(get_logger(__name__), component="database")

    async def find_by_id(self, draft_id: UUID) -> StoryDraftEntity | None:
        """Find story draft by ID."""
        try:
            stmt = select(StoryDraftModel).where(StoryDraftModel.id == draft_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return StoryDraftMapper.to_entity(model)
            return None

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="find_by_id", table="story_drafts")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error fetching draft {draft_id}", error=e, operation="find_by_id", table="story_drafts"
            )
            raise

    async def find_by_project(
        self,
        project_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[StoryDraftEntity]:
        """Find story drafts for a project."""
        try:
            stmt = (
                select(StoryDraftModel)
                .where(StoryDraftModel.project_id == project_id)
                .order_by(StoryDraftModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [StoryDraftMapper.to_entity(m) for m in models]

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="find_by_project", table="story_drafts")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error fetching drafts for project {project_id}",
                error=e,
                operation="find_by_project",
                table="story_drafts",
            )
            raise

    async def find_active_by_user(
        self,
        user_id: UUID,
        limit: int = 20,
        offset: int = 0,
    ) -> list[StoryDraftEntity]:
        """Find active (non-applied) drafts by user."""
        try:
            stmt = (
                select(StoryDraftModel)
                .where(
                    StoryDraftModel.created_by == user_id,
                    StoryDraftModel.status != "applied",
                )
                .order_by(StoryDraftModel.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            result = await self._session.execute(stmt)
            models = result.scalars().all()

            return [StoryDraftMapper.to_entity(m) for m in models]

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="find_active_by_user", table="story_drafts")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error fetching drafts for user {user_id}",
                error=e,
                operation="find_active_by_user",
                table="story_drafts",
            )
            raise

    async def save(self, draft: StoryDraftEntity) -> StoryDraftEntity:
        """Save or update a story draft."""
        start = time.time()
        try:
            stmt = select(StoryDraftModel).where(StoryDraftModel.id == draft.id.value)
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            model = StoryDraftMapper.to_model(draft, existing)
            is_insert = not existing

            if not existing:
                self._session.add(model)

            await self._session.commit()
            await self._session.refresh(model)

            duration = (time.time() - start) * 1000
            self._log.operation(
                "db.insert" if is_insert else "db.update",
                success=True,
                duration_ms=duration,
                table="story_drafts",
                entity_id=str(draft.id.value),
            )
            return StoryDraftMapper.to_entity(model)

        except OperationalError as e:
            await self._session.rollback()
            self._log.connection_error("database", error=e, operation="save", table="story_drafts")
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log.error(f"Database error saving draft {draft.id}", error=e, operation="save", table="story_drafts")
            raise

    async def delete(self, draft_id: UUID) -> bool:
        """Delete a story draft."""
        start = time.time()
        try:
            stmt = select(StoryDraftModel).where(StoryDraftModel.id == draft_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            await self._session.delete(model)
            await self._session.commit()

            duration = (time.time() - start) * 1000
            self._log.operation(
                "db.delete", success=True, duration_ms=duration, table="story_drafts", entity_id=str(draft_id)
            )
            return True

        except OperationalError as e:
            await self._session.rollback()
            self._log.connection_error("database", error=e, operation="delete", table="story_drafts")
            raise
        except SQLAlchemyError as e:
            await self._session.rollback()
            self._log.error(
                f"Database error deleting draft {draft_id}", error=e, operation="delete", table="story_drafts"
            )
            raise

    async def count_by_project(self, project_id: UUID) -> int:
        """Count drafts for a project."""
        try:
            stmt = select(func.count()).select_from(StoryDraftModel).where(StoryDraftModel.project_id == project_id)
            result = await self._session.execute(stmt)
            return result.scalar() or 0

        except OperationalError as e:
            self._log.connection_error("database", error=e, operation="count_by_project", table="story_drafts")
            raise
        except SQLAlchemyError as e:
            self._log.error(
                f"Database error counting drafts for project {project_id}",
                error=e,
                operation="count_by_project",
                table="story_drafts",
            )
            raise
