"""add auth session tables

Revision ID: a1c2f9e7d4b8
Revises: 172de3a42b18
Create Date: 2026-09-18 21:00:00.000000

"""
from collections.abc import Sequence
from typing import Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a1c2f9e7d4b8"
down_revision: str | None = "172de3a42b18"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "users",
        sa.Column("token_version", sa.Integer(), nullable=False, server_default="0"),
    )

    op.create_table(
        "account_lockouts",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("email"),
    )

    op.create_table(
        "revoked_refresh_tokens",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(
        op.f("ix_revoked_refresh_tokens_expires_at"), "revoked_refresh_tokens", ["expires_at"], unique=False
    )

    op.create_table(
        "password_reset_codes",
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
        op.f("ix_password_reset_codes_user_id"), "password_reset_codes", ["user_id"], unique=False
    )
    op.create_index(
        op.f("ix_password_reset_codes_created_at"), "password_reset_codes", ["created_at"], unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f("ix_password_reset_codes_created_at"), table_name="password_reset_codes")
    op.drop_index(op.f("ix_password_reset_codes_user_id"), table_name="password_reset_codes")
    op.drop_table("password_reset_codes")

    op.drop_index(op.f("ix_revoked_refresh_tokens_expires_at"), table_name="revoked_refresh_tokens")
    op.drop_table("revoked_refresh_tokens")

    op.drop_table("account_lockouts")

    op.drop_column("users", "token_version")
