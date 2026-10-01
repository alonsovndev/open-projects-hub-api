import uuid

from sqlalchemy import Column, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import ENUM as pg_enum, UUID  # noqa: N811
from sqlalchemy.orm import relationship

# Imported for relationship foreign_keys resolution
from src.app.features.projects.infrastructure.models.project_model import ProjectModel  # noqa: F401
from src.app.features.stories.infrastructure.models.story_model import StoryModel  # noqa: F401
from src.app.features.workspaces.infrastructure.models.workspace_model import WorkspaceModel  # noqa: F401
from src.app.shared.persistence import Base


class UserModel(Base):
    """
    SQLAlchemy model for the 'users' table.
    """

    __tablename__ = "users"

    # 1. Primary key
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)

    # 2. Data columns
    email = Column(String(255), unique=True, nullable=False, index=True)
    display_name = Column(String(255), nullable=False)
    password_hash = Column(String(255), nullable=False)
    role = Column(
        pg_enum("admin", "member", "viewer", name="userrole", create_type=False), nullable=False, default="viewer"
    )
    # Bumped on forced logout (e.g. after a password reset) to invalidate every
    # refresh token issued before that point, without needing a token ledger.
    token_version = Column(Integer, nullable=False, server_default="0", default=0)
    # Free platform refinements (F-010). `granted` is retained alongside `remaining` so the
    # UI can render "3 of 5" without hardcoding the grant size, and so a future change to
    # the grant does not retroactively rewrite what existing accounts were given.
    ai_credits_remaining = Column(Integer, nullable=False, server_default="5", default=5)
    ai_credits_granted = Column(Integer, nullable=False, server_default="5", default=5)
    # NULL until a self-registered account confirms its email (F-008); accounts
    # created by an admin or the seed script are verified on creation.
    email_verified_at = Column(DateTime(timezone=True), nullable=True)
    # Set when an Admin removes the account. Rows are kept because projects and stories
    # reference their creator; a deactivated account can no longer sign in or be listed.
    deactivated_at = Column(DateTime(timezone=True), nullable=True)
    workspace_id = Column(
        UUID(as_uuid=True), ForeignKey("workspaces.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    # Relationships
    created_projects = relationship("ProjectModel", foreign_keys="ProjectModel.created_by", backref="creator")
    created_stories = relationship("StoryModel", foreign_keys="StoryModel.created_by", backref="story_creator")
    assigned_stories = relationship("StoryModel", foreign_keys="StoryModel.assigned_to", backref="assignee")

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )
