"""add projects.access_code

The key a client stakeholder types into the Client Review page. `projects.code` cannot play
that role: it is chosen by the freelancer, only unique within a workspace, and guessable.

Revision ID: c8e1a4d7b952
Revises: b7d2e5f8a361
Create Date: 2026-10-02 15:00:00.000000

"""

import secrets
from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c8e1a4d7b952"
down_revision: str | None = "b7d2e5f8a361"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None

# Must match src/app/features/projects/domain/value_objects/access_code.py; copied rather than
# imported so this migration keeps working if the application code changes later.
_ALPHABET = "ABCDEFGHJKLMNPQRSTUVWXYZ23456789"
_CODE_LENGTH = 8


def _generate_access_code() -> str:
    return "PRJ-" + "".join(secrets.choice(_ALPHABET) for _ in range(_CODE_LENGTH))


def upgrade() -> None:
    op.add_column("projects", sa.Column("access_code", sa.String(length=20), nullable=True))

    bind = op.get_bind()
    project_ids = bind.execute(sa.text("SELECT id FROM projects")).scalars().all()
    for project_id in project_ids:
        bind.execute(
            sa.text("UPDATE projects SET access_code = :access_code WHERE id = :id"),
            {"access_code": _generate_access_code(), "id": project_id},
        )

    op.alter_column("projects", "access_code", nullable=False)
    op.create_unique_constraint("uq_projects_access_code", "projects", ["access_code"])


def downgrade() -> None:
    op.drop_constraint("uq_projects_access_code", "projects", type_="unique")
    op.drop_column("projects", "access_code")
