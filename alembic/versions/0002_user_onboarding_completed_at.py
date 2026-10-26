"""user onboarding completed at

Revision ID: 0002_user_onboarding
Revises: 0001_initial
Create Date: 2026-10-26

F-005: NULL means the first-use welcome has not been dismissed yet.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


revision: str = "0002_user_onboarding"
down_revision: str | None = "0001_initial"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("onboarding_completed_at", sa.DateTime(timezone=True), nullable=True))
    # Accounts that already exist were never shown onboarding; do not surprise them with it now.
    op.execute("UPDATE users SET onboarding_completed_at = now()")


def downgrade() -> None:
    op.drop_column("users", "onboarding_completed_at")
