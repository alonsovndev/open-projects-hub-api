"""create_clients_table

Revision ID: d6c19e951f4a
Revises: 006_extend_projects_table
Create Date: 2026-05-19 11:14:18.522054

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd6c19e951f4a'
down_revision: Union[str, None] = '006_extend_projects_table'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create clients table and add foreign key to projects."""
    
    # Create clients table
    op.create_table(
        'clients',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('name', sa.String(length=200), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=True),
        sa.Column('phone', sa.String(length=50), nullable=True),
        sa.Column('company', sa.String(length=200), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )
    
    # Create indexes for better query performance
    op.create_index('ix_clients_name', 'clients', ['name'])
    op.create_index('ix_clients_email', 'clients', ['email'])
    op.create_index('ix_clients_company', 'clients', ['company'])
    
    # Create a default client for existing projects
    op.execute("""
        INSERT INTO clients (id, name, email, company, notes)
        VALUES (
            'a0000000-0000-0000-0000-000000000001'::uuid,
            'Default Client',
            'default@example.com',
            'N/A',
            'Auto-generated default client for existing projects'
        )
    """)
    
    # Add client_id column to projects table
    op.add_column('projects', sa.Column('client_id', sa.UUID(), nullable=True))
    
    # Set all existing projects to use the default client
    op.execute("""
        UPDATE projects 
        SET client_id = 'a0000000-0000-0000-0000-000000000001'::uuid
        WHERE client_id IS NULL
    """)
    
    # Now make client_id NOT NULL and add foreign key
    op.alter_column('projects', 'client_id', nullable=False)
    op.create_foreign_key(
        'fk_projects_client_id',
        'projects',
        'clients',
        ['client_id'],
        ['id'],
        ondelete='RESTRICT'  # Prevent deletion of clients that have projects
    )
    
    # Create index on foreign key for better join performance
    op.create_index('ix_projects_client_id', 'projects', ['client_id'])


def downgrade() -> None:
    """Remove client relationship and drop clients table."""
    
    # Drop foreign key and index from projects
    op.drop_index('ix_projects_client_id', 'projects')
    op.drop_constraint('fk_projects_client_id', 'projects', type_='foreignkey')
    op.drop_column('projects', 'client_id')
    
    # Drop clients table indexes
    op.drop_index('ix_clients_company', 'clients')
    op.drop_index('ix_clients_email', 'clients')
    op.drop_index('ix_clients_name', 'clients')
    
    # Drop clients table
    op.drop_table('clients')
