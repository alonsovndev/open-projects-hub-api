"""add ai credits and user api keys

Revision ID: b4f16d2a7c90
Revises: c3b7e1a95d02
Create Date: 2026-09-20 15:04:11.902155

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "b4f16d2a7c90"
down_revision: str | None = "c3b7e1a95d02"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing accounts are granted the same 5 free credits as new ones, via the server
    # default. F-010 ties the grant to account creation, and every account that predates
    # this migration has simply never had the chance to be granted them.
    op.add_column(
        "users",
        sa.Column("ai_credits_remaining", sa.Integer(), server_default="5", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("ai_credits_granted", sa.Integer(), server_default="5", nullable=False),
    )

    bind = op.get_bind()
    # The enum must exist before CREATE TABLE references it by name with create_type=False.
    postgresql.ENUM("gemini", "openai", "deepseek", name="aiprovider").create(bind, checkfirst=True)

    op.create_table(
        "user_api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "provider",
            postgresql.ENUM("gemini", "openai", "deepseek", name="aiprovider", create_type=False),
            nullable=False,
        ),
        # Ciphertext and nonce only. There is deliberately no plaintext column: NFR-010-01
        # requires the key to be unreadable at rest, and NFR-010-02 requires that no read
        # path can return it.
        sa.Column("encrypted_key", sa.LargeBinary(), nullable=False),
        sa.Column("encryption_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("key_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("masked_key", sa.String(length=64), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        # One key per provider per user (FR-010-04). This constraint is what makes a
        # rotation an overwrite rather than an extra row holding the superseded secret.
        sa.UniqueConstraint("user_id", "provider", name="uq_user_api_keys_user_provider"),
    )
    op.create_index(op.f("ix_user_api_keys_user_id"), "user_api_keys", ["user_id"])
    op.create_index(op.f("ix_user_api_keys_created_at"), "user_api_keys", ["created_at"])
    op.create_index(op.f("ix_user_api_keys_updated_at"), "user_api_keys", ["updated_at"])

    op.create_table(
        "api_key_validation_attempts",
        # Keyed by user: the 5-per-hour budget in NFR-010-03 is per account, and there is
        # exactly one open window per account at a time.
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index(op.f("ix_api_key_validation_attempts_created_at"), "api_key_validation_attempts", ["created_at"])
    op.create_index(op.f("ix_api_key_validation_attempts_updated_at"), "api_key_validation_attempts", ["updated_at"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_table("api_key_validation_attempts")
    op.drop_table("user_api_keys")
    postgresql.ENUM(name="aiprovider").drop(op.get_bind(), checkfirst=True)
    op.drop_column("users", "ai_credits_granted")
    op.drop_column("users", "ai_credits_remaining")
