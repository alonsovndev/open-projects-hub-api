"""add workspaces and member role

Revision ID: e7a3c9d1b254
Revises: d5e2a8c41f67
Create Date: 2026-09-28 18:00:00.000000

"""

import uuid
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "e7a3c9d1b254"
down_revision: str | None = "d5e2a8c41f67"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

TENANT_TABLES = ("users", "clients", "projects")


def upgrade() -> None:
    """Upgrade schema."""
    # A new enum value cannot be used in the transaction that adds it, so commit it on its own.
    with op.get_context().autocommit_block():
        op.execute("ALTER TYPE userrole ADD VALUE IF NOT EXISTS 'member'")

    op.create_table(
        "workspaces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    for table in TENANT_TABLES:
        op.add_column(table, sa.Column("workspace_id", sa.UUID(), nullable=True))

    # Until now the instance was a single shared workspace, so every existing row moves into
    # one workspace; visibility for current accounts stays exactly as it was.
    bind = op.get_bind()
    has_rows = bind.execute(sa.text("SELECT EXISTS (SELECT 1 FROM users) OR EXISTS (SELECT 1 FROM clients)")).scalar()
    if has_rows:
        owner_name = bind.execute(
            sa.text(
                "SELECT display_name FROM users ORDER BY (role = 'admin') DESC, created_at LIMIT 1"
            )
        ).scalar()
        workspace_name = f"{owner_name}'s workspace"[:100] if owner_name else "Default workspace"
        workspace_id = uuid.uuid4()
        bind.execute(
            sa.text("INSERT INTO workspaces (id, name) VALUES (:id, :name)"),
            {"id": workspace_id, "name": workspace_name},
        )
        for table in TENANT_TABLES:
            bind.execute(sa.text(f"UPDATE {table} SET workspace_id = :id"), {"id": workspace_id})  # noqa: S608

    for table in TENANT_TABLES:
        op.alter_column(table, "workspace_id", nullable=False)
        op.create_foreign_key(
            f"fk_{table}_workspace_id", table, "workspaces", ["workspace_id"], ["id"], ondelete="RESTRICT"
        )

    op.create_index("ix_users_workspace_id", "users", ["workspace_id"], unique=False)
    op.create_index("ix_clients_workspace_id_name", "clients", ["workspace_id", "name"], unique=False)
    op.create_index(
        "ix_projects_workspace_id_status_created_at",
        "projects",
        ["workspace_id", "status", "created_at"],
        unique=False,
    )
    op.drop_constraint("projects_code_key", "projects", type_="unique")
    op.create_unique_constraint("uq_projects_workspace_id_code", "projects", ["workspace_id", "code"])
    op.create_index(
        "uq_clients_workspace_id_email",
        "clients",
        ["workspace_id", "email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )


def downgrade() -> None:
    """Downgrade schema.

    Lossy: members become viewers, and restoring the global project-code constraint fails
    loudly if two workspaces have since reused a code.
    """
    op.drop_index("uq_clients_workspace_id_email", table_name="clients")
    op.drop_constraint("uq_projects_workspace_id_code", "projects", type_="unique")
    op.create_unique_constraint("projects_code_key", "projects", ["code"])
    op.drop_index("ix_projects_workspace_id_status_created_at", table_name="projects")
    op.drop_index("ix_clients_workspace_id_name", table_name="clients")
    op.drop_index("ix_users_workspace_id", table_name="users")

    for table in TENANT_TABLES:
        op.drop_constraint(f"fk_{table}_workspace_id", table, type_="foreignkey")
        op.drop_column(table, "workspace_id")
    op.drop_table("workspaces")

    op.execute("UPDATE users SET role = 'viewer' WHERE role = 'member'")
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'viewer')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::text::userrole")
    op.execute("DROP TYPE userrole_old")
