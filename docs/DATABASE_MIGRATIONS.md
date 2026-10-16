# Database Migrations & Rollback Procedures

Practical runbook for working with Alembic migrations in this project. For the tooling
decision itself and the high-level backward-compatibility policy, see **ADR-017: Database
Migration Strategy** in the `open-projects-hub-docs` repository
(`docs/04-decisions/adr-017-database-migration-strategy.md`) — a separate repository, so not
linked directly here.

## Common Commands

```bash
# Apply all pending migrations
alembic upgrade head

# Check current revision
alembic current

# View migration history
alembic history

# Roll back one migration
alembic downgrade -1

# Roll back to a specific revision
alembic downgrade <revision>

# Roll back everything (empty schema)
alembic downgrade base

# Generate a new migration from model changes (review before committing — see below)
alembic revision --autogenerate -m "add_<thing>"
```

## Backward-Compatibility Checklist (per ADR-017)

Before merging a new migration:

- [ ] **Additive-first**: new columns/tables added before old ones are removed; a breaking
      change ships as two migrations (add-and-dual-write, then remove in a later release).
- [ ] **N-1 compatible**: the migration must not break the currently-deployed application
      version — required for zero-downtime rolling deploys (App Runner, per ADR-006).
- [ ] **Manually reviewed**: `alembic revision --autogenerate` output is a starting point,
      not a final migration — review the generated `upgrade()`/`downgrade()` before committing.
- [ ] **`downgrade()` is complete**: see the ENUM gotcha below — a downgrade that doesn't fully
      undo the upgrade will break the next `upgrade head` attempt.

Only one migration exists today (`0001_initial`, a squash of the pre-release history made
before the first deployment, so there is no deployed schema to break). This checklist is the
process to follow starting with the next schema change.

## ⚠️ PostgreSQL ENUM Types in `downgrade()`

**Gotcha found and fixed while verifying this runbook** (see `0001_initial`): a
`postgresql.ENUM` column type is a separate named object in PostgreSQL from the table that
uses it. `op.drop_table(...)` drops the table but **not** the enum type it referenced — the
type is left orphaned. The next `alembic upgrade head` then fails with
`DuplicateObjectError: type "..." already exists` when it tries to `CREATE TYPE` again.

**Rule**: any migration that creates a `postgresql.ENUM(...)` column must explicitly drop that
enum type in `downgrade()`, after the tables using it are dropped:

```python
def downgrade() -> None:
    bind = op.get_bind()
    op.drop_table("my_table")
    # ...
    postgresql.ENUM(name="my_enum_type").drop(bind, checkfirst=True)
```

## Verifying a Migration's Rollback (do this before merging)

Run the full cycle locally against `docker compose up postgres -d`:

```bash
alembic upgrade head        # apply
alembic downgrade -1        # roll back the new migration
alembic upgrade head        # re-apply — must succeed cleanly
```

If the re-apply fails, the `downgrade()` didn't fully undo the `upgrade()` (most commonly:
an orphaned ENUM type, per above, or a leftover index/constraint). This exact cycle was run
against `0001_initial` and confirmed idempotent after the ENUM fix.

## Seed Data

```bash
make seed-admin          # creates the first admin user — required first
make seed-sample-data    # idempotent: 3 clients, 6 projects, ~20 stories with varied statuses
```

`seed-sample-data` is safe to re-run — it matches clients by email and projects by code, and
only seeds a project's stories the first time that project is created.

## CI/CD Schema Validation

Not yet implemented — this repository has no GitHub Actions workflows yet. Automated
migration validation (running `alembic upgrade head` against a CI database before merge) is
in scope for **US-EP0-BE-003: CI/CD Pipeline Scaffolding and Testing Framework**, not
duplicated here.
