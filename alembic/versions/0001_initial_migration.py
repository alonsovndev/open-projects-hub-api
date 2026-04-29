"""Initial migration with users table including role

Revision ID: 0001_initial
Revises:
Create Date: 2026-04-29

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '0001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create enum type for user roles
    userrole_enum = postgresql.ENUM('ADMIN', 'USER', name='userrole')
    userrole_enum.create(op.get_bind())

    # Create users table
    op.create_table(
        'users',
        sa.Column(
            'id',
            postgresql.UUID(as_uuid=True),
            nullable=False,
            server_default=sa.text('gen_random_uuid()'),
        ),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('first_name', sa.String(length=50), nullable=False),
        sa.Column('last_name', sa.String(length=50), nullable=False),
        sa.Column('country_code', sa.String(length=10), nullable=True),
        sa.Column('password_hash', sa.String(length=255), nullable=False),
        sa.Column(
            'role',
            userrole_enum,
            nullable=False,
            server_default='USER',
        ),
        sa.Column(
            'created_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('NOW()'),
        ),
        sa.Column(
            'updated_at',
            sa.DateTime(),
            nullable=False,
            server_default=sa.text('NOW()'),
        ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email'),
    )

    op.create_index('idx_users_email', 'users', ['email'])


def downgrade() -> None:
    op.drop_index('idx_users_email', table_name='users')
    op.drop_table('users')

    userrole_enum = postgresql.ENUM('ADMIN', 'USER', name='userrole')
    userrole_enum.drop(op.get_bind())
