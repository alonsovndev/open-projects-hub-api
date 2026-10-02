import sqlalchemy.exc
from sqlalchemy import delete, exists, select, update
from sqlalchemy.ext.asyncio import AsyncSession

# Cross-feature write, see ADR-001: a pending member may already have stories assigned.
from src.app.features.stories.infrastructure.models.story_model import StoryModel
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.infrastructure.mappers.user_mapper import UserMapper
from src.app.features.user.infrastructure.models.user_model import UserModel
from src.app.features.workspaces.domain.entities.workspace_entity import WorkspaceEntity
from src.app.features.workspaces.domain.repositories.workspace_repository import WorkspaceRepository
from src.app.features.workspaces.infrastructure.models.workspace_model import WorkspaceModel
from src.app.shared.domain.value_objects.entity_id import EntityId


# The unique index behind users.email; any other integrity error is a real bug, not a duplicate.
USERS_EMAIL_UNIQUE_INDEX = "ix_users_email"


class WorkspaceRepositoryImpl(WorkspaceRepository):
    def __init__(self, db_session: AsyncSession):
        self.db_session = db_session

    async def create_with_admin(
        self, workspace: WorkspaceEntity, admin: UserEntity, replacing: UserEntity | None = None
    ) -> UserEntity | None:
        admin_model = UserMapper.to_model(admin)
        try:
            if replacing is not None:
                await self._discard_pending_account(replacing)
            self.db_session.add(WorkspaceModel(id=workspace.id.value, name=workspace.name))
            # The FK needs the workspace row in place before the user row is inserted.
            await self.db_session.flush()
            self.db_session.add(admin_model)
            await self.db_session.commit()
        except sqlalchemy.exc.IntegrityError as error:
            await self.db_session.rollback()
            if USERS_EMAIL_UNIQUE_INDEX in str(error.orig):
                return None
            raise
        except Exception:
            await self.db_session.rollback()
            raise
        await self.db_session.refresh(admin_model)
        return UserMapper.to_entity(admin_model)

    async def _discard_pending_account(self, pending: UserEntity) -> None:
        # An Admin can assign stories to someone they added before that person verifies;
        # those assignments must not keep the address hostage (the FK does not cascade).
        await self.db_session.execute(
            update(StoryModel).where(StoryModel.assigned_to == pending.id.value).values(assigned_to=None)
        )
        # Guarded on email_verified_at so an account verified in the meantime is never removed.
        await self.db_session.execute(
            delete(UserModel).where(UserModel.id == pending.id.value, UserModel.email_verified_at.is_(None))
        )
        if pending.is_admin() and pending.workspace_id is not None:
            # A pending Admin never signed in, so its workspace holds no data; drop it unless
            # someone else has joined it.
            await self.db_session.execute(
                delete(WorkspaceModel).where(
                    WorkspaceModel.id == pending.workspace_id.value,
                    ~exists(select(UserModel.id).where(UserModel.workspace_id == pending.workspace_id.value)),
                )
            )
        await self.db_session.flush()

    async def find_by_id(self, workspace_id: EntityId) -> WorkspaceEntity | None:
        model = await self.db_session.get(WorkspaceModel, workspace_id.value)
        if model is None:
            return None
        return self._to_entity(model)

    async def reserve_ai_credits(self, workspace_id: EntityId, amount: int, ceiling: int) -> int:
        # Row lock makes read-and-bump atomic across concurrent verifications. No commit here:
        # the caller's next commit persists the reservation together with the user's grant, and
        # a failure before it releases both, so credits are never counted without being given.
        granted_total = await self.db_session.scalar(
            select(WorkspaceModel.ai_credits_granted_total)
            .where(WorkspaceModel.id == workspace_id.value)
            .with_for_update()
        )
        if granted_total is None:
            raise ValueError(f"Workspace not found: {workspace_id.value}")
        reserved = max(0, min(amount, ceiling - granted_total))
        await self.db_session.execute(
            update(WorkspaceModel)
            .where(WorkspaceModel.id == workspace_id.value)
            .values(ai_credits_granted_total=granted_total + reserved)
        )
        return reserved

    async def update(self, workspace: WorkspaceEntity) -> WorkspaceEntity:
        model = await self.db_session.get(WorkspaceModel, workspace.id.value)
        if model is None:
            raise ValueError(f"Workspace not found: {workspace.id.value}")
        model.name = workspace.name
        model.updated_at = workspace.updated_at
        try:
            await self.db_session.commit()
        except Exception:
            await self.db_session.rollback()
            raise
        await self.db_session.refresh(model)
        return self._to_entity(model)

    @staticmethod
    def _to_entity(model: WorkspaceModel) -> WorkspaceEntity:
        return WorkspaceEntity(
            id=EntityId.from_string(str(model.id)),
            name=model.name,
            created_at=model.created_at,
            updated_at=model.updated_at,
        )
