"""Story draft repository implementation using SQLAlchemy."""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.refinement.domain.entities.story_draft_entity import StoryDraftEntity
from src.app.features.refinement.domain.repositories.story_draft_repository import StoryDraftRepository
from src.app.features.refinement.infrastructure.mappers.story_draft_mapper import StoryDraftMapper
from src.app.features.refinement.infrastructure.models.story_draft_model import StoryDraftModel
from src.app.shared.logging import get_logger


log = get_logger(__name__)


class StoryDraftRepositoryImpl(StoryDraftRepository):
    """SQLAlchemy implementation of StoryDraftRepository."""

    def __init__(self, session: AsyncSession):
        """
        Initialize repository with database session.

        Args:
            session: SQLAlchemy async session
        """
        self._session = session

    async def find_by_id(self, draft_id: UUID) -> StoryDraftEntity | None:
        """Find story draft by ID."""
        try:
            stmt = select(StoryDraftModel).where(StoryDraftModel.id == draft_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if model:
                return StoryDraftMapper.to_entity(model)
            return None

        except SQLAlchemyError as e:
            log.error(f"Database error fetching draft {draft_id}: {e}", exc_info=True)
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

        except SQLAlchemyError as e:
            log.error(f"Database error fetching drafts for project {project_id}: {e}", exc_info=True)
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

        except SQLAlchemyError as e:
            log.error(f"Database error fetching drafts for user {user_id}: {e}", exc_info=True)
            raise

    async def save(self, draft: StoryDraftEntity) -> StoryDraftEntity:
        """Save or update a story draft."""
        try:
            stmt = select(StoryDraftModel).where(StoryDraftModel.id == draft.id.value)
            result = await self._session.execute(stmt)
            existing = result.scalar_one_or_none()

            model = StoryDraftMapper.to_model(draft, existing)

            if not existing:
                self._session.add(model)

            await self._session.commit()
            await self._session.refresh(model)

            return StoryDraftMapper.to_entity(model)

        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(f"Database error saving draft {draft.id}: {e}", exc_info=True)
            raise

    async def delete(self, draft_id: UUID) -> bool:
        """Delete a story draft."""
        try:
            stmt = select(StoryDraftModel).where(StoryDraftModel.id == draft_id)
            result = await self._session.execute(stmt)
            model = result.scalar_one_or_none()

            if not model:
                return False

            await self._session.delete(model)
            await self._session.commit()
            return True

        except SQLAlchemyError as e:
            await self._session.rollback()
            log.error(f"Database error deleting draft {draft_id}: {e}", exc_info=True)
            raise

    async def count_by_project(self, project_id: UUID) -> int:
        """Count drafts for a project."""
        try:
            stmt = select(func.count()).select_from(StoryDraftModel).where(StoryDraftModel.project_id == project_id)
            result = await self._session.execute(stmt)
            return result.scalar() or 0

        except SQLAlchemyError as e:
            log.error(f"Database error counting drafts for project {project_id}: {e}", exc_info=True)
            raise
