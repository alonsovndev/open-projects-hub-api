"""drop story_drafts

Refined stories are no longer persisted before approval; they are saved to ``stories``
only when the Admin approves them. Unapproved drafts are discarded with the table.

Revision ID: f1b8d3a6c924
Revises: e7a3c9d1b254
Create Date: 2026-09-30 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "f1b8d3a6c924"
down_revision: str | None = "e7a3c9d1b254"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Drop the story_drafts table and its enum."""
    op.drop_index(op.f("ix_story_drafts_updated_at"), table_name="story_drafts")
    op.drop_index("ix_story_drafts_status", table_name="story_drafts")
    op.drop_index("ix_story_drafts_project_id_created_at", table_name="story_drafts")
    op.drop_index("ix_story_drafts_created_by_status", table_name="story_drafts")
    op.drop_index(op.f("ix_story_drafts_created_at"), table_name="story_drafts")
    op.drop_table("story_drafts")
    postgresql.ENUM(name="draftstatus").drop(op.get_bind(), checkfirst=True)


def downgrade() -> None:
    """Recreate an empty story_drafts table; dropped drafts are not restored."""
    op.create_table(
        "story_drafts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=500), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", sa.ARRAY(sa.Text()), nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("status", sa.Enum("draft", "applied", name="draftstatus"), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_story_drafts_created_at"), "story_drafts", ["created_at"], unique=False)
    op.create_index("ix_story_drafts_created_by_status", "story_drafts", ["created_by", "status"], unique=False)
    op.create_index("ix_story_drafts_project_id_created_at", "story_drafts", ["project_id", "created_at"], unique=False)
    op.create_index("ix_story_drafts_status", "story_drafts", ["status"], unique=False)
    op.create_index(op.f("ix_story_drafts_updated_at"), "story_drafts", ["updated_at"], unique=False)
