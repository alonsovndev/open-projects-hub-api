"""005_add_stories_table

Revision ID: 005_add_stories_table
Revises: 004_add_projects_table
Create Date: 2026-05-09 17:50:00.000000

Add stories table with foreign keys to projects and users.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '005_add_stories_table'
down_revision: Union[str, None] = '004_add_projects_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create stories table."""
    
    op.create_table(
        'stories',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, nullable=False),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column(
            'status',
            sa.Enum('todo', 'in_progress', 'done', name='storystatus'),
            nullable=False,
            server_default='todo'
        ),
        sa.Column(
            'priority',
            sa.Enum('low', 'medium', 'high', name='storypriority'),
            nullable=False,
            server_default='medium'
        ),
        sa.Column('points', sa.Integer(), nullable=True),
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
        # Foreign key to projects (cascade delete stories when project is deleted)
        sa.ForeignKeyConstraint(
            ['project_id'],
            ['projects.id'],
            name='fk_stories_project_id_projects',
            ondelete='CASCADE'
        ),
        # Foreign key to users (created_by)
        sa.ForeignKeyConstraint(
            ['created_by'],
            ['users.id'],
            name='fk_stories_created_by_users',
            ondelete='RESTRICT'
        ),
        # Foreign key to users (assigned_to)
        sa.ForeignKeyConstraint(
            ['assigned_to'],
            ['users.id'],
            name='fk_stories_assigned_to_users',
            ondelete='SET NULL'  # Keep story but unassign when user is deleted
        ),
    )
    
    # Create indexes for common query patterns
    op.create_index(
        'ix_stories_project_id',
        'stories',
        ['project_id']
    )
    
    op.create_index(
        'ix_stories_created_by',
        'stories',
        ['created_by']
    )
    
    op.create_index(
        'ix_stories_assigned_to',
        'stories',
        ['assigned_to']
    )
    
    op.create_index(
        'ix_stories_status',
        'stories',
        ['status']
    )
    
    op.create_index(
        'ix_stories_priority',
        'stories',
        ['priority']
    )
    
    op.create_index(
        'ix_stories_created_at',
        'stories',
        ['created_at']
    )


def downgrade() -> None:
    """Drop stories table."""
    
    # Drop indexes first
    op.drop_index('ix_stories_created_at', table_name='stories')
    op.drop_index('ix_stories_priority', table_name='stories')
    op.drop_index('ix_stories_status', table_name='stories')
    op.drop_index('ix_stories_assigned_to', table_name='stories')
    op.drop_index('ix_stories_created_by', table_name='stories')
    op.drop_index('ix_stories_project_id', table_name='stories')
    
    # Drop table
    op.drop_table('stories')
    
    # Drop enum types
    op.execute('DROP TYPE storypriority')
    op.execute('DROP TYPE storystatus')