"""initial schema

Revision ID: 0001_initial
Revises:
Create Date: 2026-10-08

Squashed baseline of the pre-release migration history.
"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql


revision: str = "0001_initial"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "account_lockouts",
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("failed_attempts", sa.Integer(), nullable=False),
        sa.Column("locked_until", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_attempt_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("email"),
    )
    op.create_table(
        "revoked_refresh_tokens",
        sa.Column("token_hash", sa.String(length=64), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.PrimaryKeyConstraint("token_hash"),
    )
    op.create_index(op.f("ix_revoked_refresh_tokens_expires_at"), "revoked_refresh_tokens", ["expires_at"], unique=False)
    op.create_table(
        "workspaces",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("ai_credits_granted_total", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_table(
        "clients",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("phone", sa.String(length=50), nullable=True),
        sa.Column("company", sa.String(length=200), nullable=True),
        sa.Column("address", sa.Text(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_clients_company"), "clients", ["company"], unique=False)
    op.create_index(op.f("ix_clients_created_at"), "clients", ["created_at"], unique=False)
    op.create_index(op.f("ix_clients_email"), "clients", ["email"], unique=False)
    op.create_index(op.f("ix_clients_name"), "clients", ["name"], unique=False)
    op.create_index(op.f("ix_clients_updated_at"), "clients", ["updated_at"], unique=False)
    op.create_index("ix_clients_workspace_id_name", "clients", ["workspace_id", "name"], unique=False)
    op.create_index(
        "uq_clients_workspace_id_email",
        "clients",
        ["workspace_id", "email"],
        unique=True,
        postgresql_where=sa.text("email IS NOT NULL"),
    )
    op.create_table(
        "users",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("display_name", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("role", postgresql.ENUM("admin", "member", name="userrole"), nullable=False),
        sa.Column("token_version", sa.Integer(), server_default="0", nullable=False),
        sa.Column("ai_credits_remaining", sa.Integer(), server_default="5", nullable=False),
        sa.Column("ai_credits_granted", sa.Integer(), server_default="5", nullable=False),
        sa.Column("email_verified_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("deactivated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_created_at"), "users", ["created_at"], unique=False)
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_updated_at"), "users", ["updated_at"], unique=False)
    op.create_index(op.f("ix_users_workspace_id"), "users", ["workspace_id"], unique=False)
    op.create_table(
        "api_key_validation_attempts",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("window_started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_api_key_validation_attempts_created_at"), "api_key_validation_attempts", ["created_at"], unique=False
    )
    op.create_index(
        op.f("ix_api_key_validation_attempts_updated_at"), "api_key_validation_attempts", ["updated_at"], unique=False
    )
    op.create_table(
        "email_verification_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_email_verification_codes_created_at"), "email_verification_codes", ["created_at"], unique=False
    )
    op.create_index(op.f("ix_email_verification_codes_user_id"), "email_verification_codes", ["user_id"], unique=False)
    op.create_table(
        "password_reset_codes",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("code_hash", sa.String(length=255), nullable=False),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("attempt_count", sa.Integer(), server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_password_reset_codes_created_at"), "password_reset_codes", ["created_at"], unique=False)
    op.create_index(op.f("ix_password_reset_codes_user_id"), "password_reset_codes", ["user_id"], unique=False)
    op.create_table(
        "projects",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("access_code", sa.String(length=20), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("workspace_id", sa.UUID(), nullable=False),
        sa.Column("client_id", sa.UUID(), nullable=False),
        sa.Column("status", sa.Enum("active", "completed", "archived", name="projectstatus"), nullable=False),
        sa.Column("priority", sa.Enum("low", "medium", "high", name="projectpriority"), nullable=False),
        sa.Column(
            "phase", sa.Enum("discovery", "planning", name="projectphase"), server_default="discovery", nullable=False
        ),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["client_id"], ["clients.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="RESTRICT"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("access_code", name="uq_projects_access_code"),
        sa.UniqueConstraint("workspace_id", "code", name="uq_projects_workspace_id_code"),
    )
    op.create_index("ix_projects_client_id", "projects", ["client_id"], unique=False)
    op.create_index("ix_projects_code", "projects", ["code"], unique=False)
    op.create_index(op.f("ix_projects_created_at"), "projects", ["created_at"], unique=False)
    op.create_index("ix_projects_created_by", "projects", ["created_by"], unique=False)
    op.create_index("ix_projects_priority", "projects", ["priority"], unique=False)
    op.create_index("ix_projects_status_created_at", "projects", ["status", "created_at"], unique=False)
    op.create_index(op.f("ix_projects_updated_at"), "projects", ["updated_at"], unique=False)
    op.create_index(
        "ix_projects_workspace_id_status_created_at", "projects", ["workspace_id", "status", "created_at"], unique=False
    )
    op.create_table(
        "user_api_keys",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("provider", postgresql.ENUM("gemini", "openai", "deepseek", name="aiprovider"), nullable=False),
        sa.Column("encrypted_key", sa.LargeBinary(), nullable=False),
        sa.Column("encryption_nonce", sa.LargeBinary(), nullable=False),
        sa.Column("key_version", sa.Integer(), server_default="1", nullable=False),
        sa.Column("masked_key", sa.String(length=64), nullable=False),
        sa.Column("last_validated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "provider", name="uq_user_api_keys_user_provider"),
    )
    op.create_index(op.f("ix_user_api_keys_created_at"), "user_api_keys", ["created_at"], unique=False)
    op.create_index(op.f("ix_user_api_keys_updated_at"), "user_api_keys", ["updated_at"], unique=False)
    op.create_index(op.f("ix_user_api_keys_user_id"), "user_api_keys", ["user_id"], unique=False)
    op.create_table(
        "stories",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("acceptance_criteria", sa.ARRAY(sa.Text()), server_default="{}", nullable=False),
        sa.Column("project_id", sa.UUID(), nullable=False),
        sa.Column("created_by", sa.UUID(), nullable=False),
        sa.Column("assigned_to", sa.UUID(), nullable=True),
        sa.Column("status", sa.Enum("todo", "in_progress", "blocked", "done", name="storystatus"), nullable=False),
        sa.Column("priority", sa.Enum("low", "medium", "high", name="storypriority"), nullable=False),
        sa.Column("points", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["assigned_to"], ["users.id"]),
        sa.ForeignKeyConstraint(["created_by"], ["users.id"]),
        sa.ForeignKeyConstraint(["project_id"], ["projects.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_stories_assigned_to_status", "stories", ["assigned_to", "status"], unique=False)
    op.create_index(op.f("ix_stories_created_at"), "stories", ["created_at"], unique=False)
    op.create_index("ix_stories_created_by", "stories", ["created_by"], unique=False)
    op.create_index("ix_stories_project_id_created_at", "stories", ["project_id", "created_at"], unique=False)
    op.create_index("ix_stories_status_priority", "stories", ["status", "priority"], unique=False)
    op.create_index(op.f("ix_stories_updated_at"), "stories", ["updated_at"], unique=False)


def downgrade() -> None:
    op.drop_table("stories")
    op.drop_table("user_api_keys")
    op.drop_table("projects")
    op.drop_table("password_reset_codes")
    op.drop_table("email_verification_codes")
    op.drop_table("api_key_validation_attempts")
    op.drop_table("users")
    op.drop_table("clients")
    op.drop_table("workspaces")
    op.drop_table("revoked_refresh_tokens")
    op.drop_table("account_lockouts")

    # op.drop_table does not remove Postgres enum types; leaving them breaks the next upgrade.
    op.execute("DROP TYPE IF EXISTS aiprovider")
    op.execute("DROP TYPE IF EXISTS projectphase")
    op.execute("DROP TYPE IF EXISTS projectpriority")
    op.execute("DROP TYPE IF EXISTS projectstatus")
    op.execute("DROP TYPE IF EXISTS storypriority")
    op.execute("DROP TYPE IF EXISTS storystatus")
    op.execute("DROP TYPE IF EXISTS userrole")
