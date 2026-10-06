"""remove the viewer user role

Clients no longer have accounts: stakeholders review a project through its access code. Only
freelancers (admins and members) log in.

Existing viewer accounts become deactivated members rather than being deleted, so they stop
working immediately and no data is lost. Their sessions are invalidated by bumping
`token_version`. An Admin who reactivates one (PATCH /v1/users/{id}/status) gives that person
full member rights, so deleting them from the Team page is the way to remove them for good.

Revision ID: d9f2b5e8c063
Revises: c8e1a4d7b952
Create Date: 2026-10-02 15:30:00.000000

"""

from collections.abc import Sequence

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "d9f2b5e8c063"
down_revision: str | None = "c8e1a4d7b952"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.execute(
        """
        UPDATE users
        SET role = 'member',
            deactivated_at = COALESCE(deactivated_at, now()),
            token_version = token_version + 1
        WHERE role = 'viewer'
        """
    )
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'member')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::text::userrole")
    op.execute("DROP TYPE userrole_old")


def downgrade() -> None:
    """Restores the enum value only; deactivated former viewers stay members and deactivated."""
    op.execute("ALTER TYPE userrole RENAME TO userrole_old")
    op.execute("CREATE TYPE userrole AS ENUM ('admin', 'member', 'viewer')")
    op.execute("ALTER TABLE users ALTER COLUMN role TYPE userrole USING role::text::userrole")
    op.execute("DROP TYPE userrole_old")
