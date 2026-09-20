"""add story acceptance criteria column

Revision ID: c3b7e1a95d02
Revises: a1c2f9e7d4b8
Create Date: 2026-09-20 10:12:44.118207

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c3b7e1a95d02'
down_revision: Union[str, None] = 'a1c2f9e7d4b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    # Existing rows carry their criteria inside `description` as a flattened
    # "**Acceptance Criteria:**" block written by the refinement approval mapper. They are
    # left as-is: the text stays readable, and backfilling would mean parsing free text an
    # Admin may since have edited. New approvals populate this column directly.
    op.add_column(
        'stories',
        sa.Column(
            'acceptance_criteria',
            sa.ARRAY(sa.Text()),
            server_default='{}',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('stories', 'acceptance_criteria')
