"""create story_drafts table

Revision ID: 87801e07c55c
Revises: d6c19e951f4a
Create Date: 2026-05-19
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '87801e07c55c'
down_revision: Union[str, None] = 'd6c19e951f4a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create story_drafts table for AI refinement feature."""
    op.create_table(
        'story_drafts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('title', sa.String(500), nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('acceptance_criteria', postgresql.ARRAY(sa.Text), nullable=False, server_default='{}'),
        sa.Column('project_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('projects.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id'), nullable=False),
        sa.Column('status', sa.String(20), nullable=False, server_default='draft'),
        sa.Column('refined_title', sa.String(500), nullable=True),
        sa.Column('refined_description', sa.Text, nullable=True),
        sa.Column('refined_criteria', postgresql.ARRAY(sa.Text), nullable=True),
        sa.Column('created_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, nullable=False, server_default=sa.func.now()),
    )
    
    # Create indexes
    op.create_index('ix_story_drafts_project_id_created_at', 'story_drafts', ['project_id', 'created_at'])
    op.create_index('ix_story_drafts_created_by_status', 'story_drafts', ['created_by', 'status'])
    op.create_index('ix_story_drafts_status', 'story_drafts', ['status'])


def downgrade() -> None:
    """Drop story_drafts table."""
    op.drop_index('ix_story_drafts_status', table_name='story_drafts')
    op.drop_index('ix_story_drafts_created_by_status', table_name='story_drafts')
    op.drop_index('ix_story_drafts_project_id_created_at', table_name='story_drafts')
    op.drop_table('story_drafts')
