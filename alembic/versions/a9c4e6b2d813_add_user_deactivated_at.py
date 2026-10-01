"""add users.deactivated_at

Admins remove teammates by deactivating them: projects and stories keep referencing the
creator, so the row stays and only loses the ability to sign in.

Revision ID: a9c4e6b2d813
Revises: f1b8d3a6c924
Create Date: 2026-10-01 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "a9c4e6b2d813"
down_revision: str | None = "f1b8d3a6c924"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column("users", sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True))


def downgrade() -> None:
    op.drop_column("users", "deactivated_at")
