"""006_extend_projects_table

Revision ID: 006_extend_projects_table
Revises: 005_add_stories_table
Create Date: 2026-05-19 10:00:00.000000

Add code and priority fields to projects table.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '006_extend_projects_table'
down_revision: Union[str, None] = '005_add_stories_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add code and priority fields to projects table."""
    
    # Create priority enum type
    op.execute("CREATE TYPE projectpriority AS ENUM ('low', 'medium', 'high')")
    
    # Add code column (temporarily nullable, we'll populate it then make it NOT NULL)
    op.add_column('projects', sa.Column('code', sa.String(50), nullable=True))
    
    # Add priority column with default
    op.add_column(
        'projects',
        sa.Column(
            'priority',
            sa.Enum('low', 'medium', 'high', name='projectpriority'),
            nullable=False,
            server_default='medium'
        )
    )
    
    # Generate codes for existing projects (PROJ-001, PROJ-002, etc.)
    # Using a CTE with row numbers, then update
    op.execute("""
        WITH numbered_projects AS (
            SELECT id, ROW_NUMBER() OVER (ORDER BY created_at) as row_num
            FROM projects
        )
        UPDATE projects 
        SET code = 'PROJ-' || LPAD(numbered_projects.row_num::TEXT, 3, '0')
        FROM numbered_projects
        WHERE projects.id = numbered_projects.id
    """)
    
    # Now make code NOT NULL and UNIQUE
    op.alter_column('projects', 'code', nullable=False)
    op.create_unique_constraint('uq_projects_code', 'projects', ['code'])
    
    # Create indexes for new fields
    op.create_index('ix_projects_priority', 'projects', ['priority'])
    op.create_index('ix_projects_code', 'projects', ['code'])


def downgrade() -> None:
    """Remove code and priority fields from projects table."""
    
    # Drop indexes
    op.drop_index('ix_projects_code', table_name='projects')
    op.drop_index('ix_projects_priority', table_name='projects')
    
    # Drop unique constraint
    op.drop_constraint('uq_projects_code', 'projects', type_='unique')
    
    # Drop columns
    op.drop_column('projects', 'priority')
    op.drop_column('projects', 'code')
    
    # Drop enum type
    op.execute('DROP TYPE projectpriority')
