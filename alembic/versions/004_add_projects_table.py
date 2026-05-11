"""004_add_projects_table

Revision ID: 004_add_projects_table
Revises: 001_initial_schema
Create Date: 2026-05-09 18:00:00.000000

Add projects table with foreign key to users.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004_add_projects_table'
down_revision: Union[str, None] = '001_initial_schema'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create projects table."""
    
    op.create_table(
        'projects',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column(
            'status',
            sa.Enum('active', 'completed', 'archived', name='projectstatus'),
            nullable=False,
            server_default='active'
        ),
        sa.Column('start_date', sa.Date(), nullable=True),
        sa.Column('end_date', sa.Date(), nullable=True),
        sa.Column(
            'created_at',
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text('now()')
        ),
        sa.Column(
            'updated_at',
            sa.TIMESTAMP(timezone=True),
            nullable=False,
            server_default=sa.text('now()')
        ),
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['users.id'],
            name='fk_projects_created_by_users',
            ondelete='RESTRICT'  # Prevent deleting users who created projects
        ),
    )
    
    # Create indexes for common query patterns
    op.create_index(
        'ix_projects_created_by',
        'projects',
        ['created_by']
    )
    
    op.create_index(
        'ix_projects_status',
        'projects',
        ['status']
    )
    
    op.create_index(
        'ix_projects_created_at',
        'projects',
        ['created_at']
    )


def downgrade() -> None:
    """Drop projects table."""
    
    # Drop indexes first
    op.drop_index('ix_projects_created_at', table_name='projects')
    op.drop_index('ix_projects_status', table_name='projects')
    op.drop_index('ix_projects_created_by', table_name='projects')
    
    # Drop table
    op.drop_table('projects')
    
    # Drop enum type
    op.execute('DROP TYPE projectstatus')
