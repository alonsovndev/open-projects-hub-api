"""add project phase column

Revision ID: 172de3a42b18
Revises: 370af72fb83e
Create Date: 2026-09-18 19:14:05.597421

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = '172de3a42b18'
down_revision: Union[str, None] = '370af72fb83e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    bind = op.get_bind()
    # Enum type must exist before it can be used in ADD COLUMN (unlike CREATE TABLE,
    # which creates the type implicitly).
    postgresql.ENUM('discovery', 'planning', name='projectphase').create(bind, checkfirst=True)
    op.add_column(
        'projects',
        sa.Column(
            'phase',
            sa.Enum('discovery', 'planning', name='projectphase'),
            server_default='discovery',
            nullable=False,
        ),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column('projects', 'phase')
    postgresql.ENUM(name='projectphase').drop(op.get_bind(), checkfirst=True)
