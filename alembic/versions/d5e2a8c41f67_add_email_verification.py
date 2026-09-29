"""add email verification

Revision ID: d5e2a8c41f67
Revises: b4f16d2a7c90
Create Date: 2026-09-28 10:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d5e2a8c41f67"
down_revision: str | None = "b4f16d2a7c90"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column("users", sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True))
    # Accounts that predate sign-up verification must keep signing in.
    op.execute("UPDATE users SET email_verified_at = created_at")

    op.create_table(
        "email_verification_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verification_codes_user_id"), "email_verification_codes", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_email_verification_codes_created_at"), "email_verification_codes", ["created_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_email_verification_codes_created_at"), table_name="email_verification_codes")
    op.drop_index(op.f("ix_email_verification_codes_user_id"), table_name="email_verification_codes")
    op.drop_table("email_verification_codes")

    op.drop_column("users", "email_verified_at")
