"""001_initial_schema

Revision ID: 001_initial_schema
Revises: 
Create Date: 2026-05-09 16:30:00.000000

Initial database schema including:
- users table with displayName and role (admin/viewer)
- user_preferences table with theme and language
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '001_initial_schema'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create initial schema: users and user_preferences tables."""
    
    # ========================================
    # 1. CREATE ENUM TYPE FOR USER ROLES
    # ========================================
    user_role_enum = postgresql.ENUM('admin', 'viewer', name='userrole', create_type=False)
    user_role_enum.create(op.get_bind(), checkfirst=True)
    
    # ========================================
    # 2. CREATE USERS TABLE
    # ========================================
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('display_name', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column('role', user_role_enum, nullable=False, server_default='viewer'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email')
    )
    
    # Create indexes on users table
    op.create_index('ix_users_email', 'users', ['email'], unique=True)
    op.create_index('ix_users_created_at', 'users', ['created_at'])
    op.create_index('ix_users_updated_at', 'users', ['updated_at'])
    
    # ========================================
    # 2. CREATE USER_PREFERENCES TABLE
    # ========================================
    op.create_table(
        'user_preferences',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('theme', sa.String(length=10), nullable=False, server_default='auto'),
        sa.Column('language', sa.String(length=10), nullable=False, server_default='en'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', name='uq_user_preferences_user_id')
    )
    
    # Create index on user_preferences table
    op.create_index('ix_user_preferences_user_id', 'user_preferences', ['user_id'], unique=True)


def downgrade() -> None:
    """Drop all tables in reverse order."""
    
    # Drop user_preferences table first (has FK to users)
    op.drop_index('ix_user_preferences_user_id', table_name='user_preferences')
    op.drop_table('user_preferences')
    
    # Drop users table
    op.drop_index('ix_users_updated_at', table_name='users')
    op.drop_index('ix_users_created_at', table_name='users')
    op.drop_index('ix_users_email', table_name='users')
    op.drop_table('users')
    
    # Drop enum type
    user_role_enum = postgresql.ENUM('admin', 'viewer', name='userrole')
    user_role_enum.drop(op.get_bind(), checkfirst=True)
