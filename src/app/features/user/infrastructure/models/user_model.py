import uuid

from sqlalchemy import Column, DateTime, Integer, String, func
from sqlalchemy.dialects.postgresql import ENUM as pg_enum, UUID  # noqa: N811
from sqlalchemy.orm import relationship

# Imported for relationship foreign_keys resolution
from src.app.features.projects.infrastructure.models.project_model import ProjectModel  # noqa: F401
from src.app.features.refinement.infrastructure.models.story_draft_model import StoryDraftModel  # noqa: F401
from src.app.features.stories.infrastructure.models.story_model import StoryModel  # noqa: F401
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
    role = Column(pg_enum("admin", "viewer", name="userrole", create_type=False), nullable=False, default="viewer")
    # Bumped on forced logout (e.g. after a password reset) to invalidate every
    # refresh token issued before that point, without needing a token ledger.
    token_version = Column(Integer, nullable=False, server_default="0", default=0)

    # Relationships
    created_projects = relationship("ProjectModel", foreign_keys="ProjectModel.created_by", backref="creator")
    created_stories = relationship("StoryModel", foreign_keys="StoryModel.created_by", backref="story_creator")
    assigned_stories = relationship("StoryModel", foreign_keys="StoryModel.assigned_to", backref="assignee")
    story_drafts = relationship("StoryDraftModel", backref="draft_creator")

    # 3. Audit columns
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False, index=True)
    updated_at = Column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False, index=True
    )
