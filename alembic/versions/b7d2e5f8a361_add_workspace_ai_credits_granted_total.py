"""add workspaces.ai_credits_granted_total

Lifetime free credits handed out per workspace, so a workspace's total is capped even when
members are removed and re-added.

Revision ID: b7d2e5f8a361
Revises: a9c4e6b2d813
Create Date: 2026-10-02 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "b7d2e5f8a361"
down_revision: str | None = "a9c4e6b2d813"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "workspaces",
        sa.Column("ai_credits_granted_total", sa.Integer(), nullable=False, server_default="0"),
    )
    op.execute(
        """
        UPDATE workspaces
        SET ai_credits_granted_total = granted.total
        FROM (
            SELECT workspace_id, COALESCE(SUM(ai_credits_granted), 0) AS total
            FROM users
            GROUP BY workspace_id
        ) AS granted
        WHERE workspaces.id = granted.workspace_id
        """
    )


def downgrade() -> None:
    op.drop_column("workspaces", "ai_credits_granted_total")
