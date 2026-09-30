#!/usr/bin/env python3
"""
Database seed script to populate realistic sample clients, projects, and stories.

Connects using the same configuration the running application uses
(src/app/config/config_<APP_ENV>.yml + .env), so it always targets
whatever database the app itself is configured for.

Idempotent: safe to re-run. Clients are matched by email, projects by
code, and stories by project (a project's stories are only seeded once,
on the run that creates that project).

Prerequisite: an admin user must already exist (run `make seed-admin`
first) — sample projects/stories are attributed to it as creator.

Usage:
    python scripts/seed_sample_data.py

Environment variables:
    APP_ENV: Application environment (local, dev, container, prod, test) - default: dev
    ADMIN_EMAIL: Email of the existing admin user to attribute records to (default: admin@example.com)
"""

import asyncio
import os
import sys
from pathlib import Path

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.app.config.app_config import AppConfig
from src.app.features.clients.domain.entities.client_entity import ClientEntity
from src.app.features.clients.infrastructure.repositories.client_repository_impl import ClientRepositoryImpl
from src.app.features.projects.domain.entities.project_entity import ProjectEntity
from src.app.features.projects.domain.value_objects.project_priority import ProjectPriority
from src.app.features.projects.domain.value_objects.project_status import ProjectStatus
from src.app.features.projects.infrastructure.mappers.project_mapper import ProjectMapper
from src.app.features.projects.infrastructure.models.project_model import ProjectModel
from src.app.features.projects.infrastructure.repositories.project_repository_impl import ProjectRepositoryImpl
from src.app.features.stories.domain.entities.story_entity import StoryEntity
from src.app.features.stories.domain.value_objects.story_priority import StoryPriority
from src.app.features.stories.domain.value_objects.story_status import StoryStatus
from src.app.features.stories.infrastructure.repositories.story_repository_impl import StoryRepositoryImpl
from src.app.features.user.infrastructure.repositories.user_repository_impl import UserRepositoryImpl
from src.app.shared.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId
from src.app.shared.persistence.engine_factory import close_engine, get_engine


CLIENTS = [
    {
        "name": "Acme Robotics",
        "email": "contact@acmerobotics.example",
        "phone": "+1-415-555-0142",
        "company": "Acme Robotics Inc.",
        "address": "500 Industrial Way, San Jose, CA",
        "notes": "Manufacturing automation client, monthly check-ins.",
    },
    {
        "name": "Blue Harbor Logistics",
        "email": "ops@blueharborlogistics.example",
        "phone": "+1-206-555-0198",
        "company": "Blue Harbor Logistics LLC",
        "address": "88 Pier Ave, Seattle, WA",
        "notes": "Fleet tracking platform, prefers weekly status emails.",
    },
    {
        "name": "Nova Health Systems",
        "email": "projects@novahealth.example",
        "phone": "+1-312-555-0173",
        "company": "Nova Health Systems",
        "address": "200 Lakeside Blvd, Chicago, IL",
        "notes": "HIPAA-sensitive workflows; requires signed change requests.",
    },
]

# Two projects per client, varying status/priority to cover realistic MVP scenarios.
PROJECTS_BY_CLIENT_INDEX = {
    0: [
        {
            "code": "ACME-INV",
            "name": "Inventory Tracking Revamp",
            "description": "Replace spreadsheet-based inventory tracking with a real-time dashboard.",
            "priority": ProjectPriority.HIGH,
            "status": ProjectStatus.ACTIVE,
        },
        {
            "code": "ACME-ONB",
            "name": "Technician Onboarding Portal",
            "description": "Self-service onboarding flow for new field technicians.",
            "priority": ProjectPriority.LOW,
            "status": ProjectStatus.COMPLETED,
        },
    ],
    1: [
        {
            "code": "BHL-FLEET",
            "name": "Fleet Tracking Dashboard",
            "description": "Live GPS tracking and route optimization for the delivery fleet.",
            "priority": ProjectPriority.HIGH,
            "status": ProjectStatus.ACTIVE,
        },
        {
            "code": "BHL-BILL",
            "name": "Automated Billing Reconciliation",
            "description": "Reconcile carrier invoices against contracted rates automatically.",
            "priority": ProjectPriority.MEDIUM,
            "status": ProjectStatus.ARCHIVED,
        },
    ],
    2: [
        {
            "code": "NOVA-PATIENT",
            "name": "Patient Intake Digitization",
            "description": "Digitize paper intake forms with HIPAA-compliant storage.",
            "priority": ProjectPriority.HIGH,
            "status": ProjectStatus.ACTIVE,
        },
        {
            "code": "NOVA-REPORT",
            "name": "Compliance Reporting Suite",
            "description": "Automated monthly compliance reports for regulators.",
            "priority": ProjectPriority.MEDIUM,
            "status": ProjectStatus.ACTIVE,
        },
    ],
}

# Stories per project code — deliberately varied statuses/priorities/points/assignment.
STORIES_BY_PROJECT_CODE = {
    "ACME-INV": [
        {
            "title": "Design inventory data model",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.HIGH,
            "points": 5,
            "assign_to_admin": True,
        },
        {
            "title": "Build barcode scanning API",
            "status": StoryStatus.IN_PROGRESS,
            "priority": StoryPriority.HIGH,
            "points": 8,
            "assign_to_admin": True,
        },
        {
            "title": "Real-time stock level dashboard",
            "status": StoryStatus.TODO,
            "priority": StoryPriority.MEDIUM,
            "points": 5,
            "assign_to_admin": False,
        },
        {
            "title": "Low-stock email alerts",
            "status": StoryStatus.TODO,
            "priority": StoryPriority.LOW,
            "points": 2,
            "assign_to_admin": False,
        },
        {
            "title": "Migrate legacy spreadsheet data",
            "status": StoryStatus.BLOCKED,
            "priority": StoryPriority.MEDIUM,
            "points": 3,
            "assign_to_admin": False,
        },
    ],
    "ACME-ONB": [
        {
            "title": "Onboarding checklist UI",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.MEDIUM,
            "points": 3,
            "assign_to_admin": True,
        },
        {
            "title": "Document upload flow",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.LOW,
            "points": 2,
            "assign_to_admin": False,
        },
        {
            "title": "Manager approval workflow",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.MEDIUM,
            "points": 5,
            "assign_to_admin": True,
        },
    ],
    "BHL-FLEET": [
        {
            "title": "Integrate GPS telemetry feed",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.HIGH,
            "points": 8,
            "assign_to_admin": True,
        },
        {
            "title": "Route optimization engine",
            "status": StoryStatus.IN_PROGRESS,
            "priority": StoryPriority.HIGH,
            "points": 13,
            "assign_to_admin": True,
        },
        {
            "title": "Driver mobile app polish",
            "status": StoryStatus.TODO,
            "priority": StoryPriority.MEDIUM,
            "points": 5,
            "assign_to_admin": False,
        },
        {
            "title": "Live map performance tuning",
            "status": StoryStatus.BLOCKED,
            "priority": StoryPriority.HIGH,
            "points": 5,
            "assign_to_admin": False,
        },
    ],
    "BHL-BILL": [
        {
            "title": "Carrier invoice parser",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.MEDIUM,
            "points": 5,
            "assign_to_admin": True,
        },
        {
            "title": "Rate mismatch reconciliation report",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.MEDIUM,
            "points": 3,
            "assign_to_admin": True,
        },
    ],
    "NOVA-PATIENT": [
        {
            "title": "HIPAA-compliant form storage",
            "status": StoryStatus.DONE,
            "priority": StoryPriority.HIGH,
            "points": 8,
            "assign_to_admin": True,
        },
        {
            "title": "Digital signature capture",
            "status": StoryStatus.IN_PROGRESS,
            "priority": StoryPriority.HIGH,
            "points": 5,
            "assign_to_admin": True,
        },
        {
            "title": "Intake form validation rules",
            "status": StoryStatus.TODO,
            "priority": StoryPriority.MEDIUM,
            "points": 3,
            "assign_to_admin": False,
        },
        {
            "title": "Audit log for record access",
            "status": StoryStatus.TODO,
            "priority": StoryPriority.HIGH,
            "points": 5,
            "assign_to_admin": False,
        },
    ],
    "NOVA-REPORT": [
        {
            "title": "Monthly compliance report template",
            "status": StoryStatus.TODO,
            "priority": StoryPriority.MEDIUM,
            "points": 5,
            "assign_to_admin": False,
        },
        {
            "title": "Scheduled report generation job",
            "status": StoryStatus.BLOCKED,
            "priority": StoryPriority.MEDIUM,
            "points": 3,
            "assign_to_admin": False,
        },
    ],
}


async def _get_or_create_client(
    repository: ClientRepositoryImpl, data: dict, workspace_id: EntityId
) -> tuple[ClientEntity, bool]:
    """Return (client, created) — reuses an existing client of the workspace matched by email."""
    existing = await repository.find_by_email(data["email"], workspace_id=workspace_id.value)
    if existing:
        return existing, False

    entity = ClientEntity.create(**data, workspace_id=workspace_id)
    saved = await repository.save(entity)
    return saved, True


async def _get_or_create_project(
    session: AsyncSession,
    repository: ProjectRepositoryImpl,
    code: str,
    client_id: EntityId,
    created_by: EntityId,
    spec: dict,
    workspace_id: EntityId,
) -> tuple[ProjectEntity, bool]:
    """Return (project, created) — reuses an existing project of the workspace matched by code."""
    stmt = select(ProjectModel).where(ProjectModel.code == code, ProjectModel.workspace_id == workspace_id.value)
    result = await session.execute(stmt)
    existing_model = result.scalar_one_or_none()
    if existing_model:
        return ProjectMapper.to_entity(existing_model), False

    project = ProjectEntity.create(
        name=spec["name"],
        code=code,
        created_by=created_by,
        client_id=client_id,
        workspace_id=workspace_id,
        description=spec["description"],
        priority=spec["priority"],
    )
    if spec["status"] == ProjectStatus.COMPLETED:
        project.complete()
    elif spec["status"] == ProjectStatus.ARCHIVED:
        project.archive()

    saved = await repository.save(project)
    return saved, True


async def _seed_stories_for_project(
    story_repository: StoryRepositoryImpl, project: ProjectEntity, created_by, admin_id, stories_spec: list[dict]
) -> int:
    """Seed stories for a project, skipping if it already has any (idempotent)."""
    existing_count = await story_repository.count(workspace_id=project.workspace_id.value, project_id=project.id.value)
    if existing_count > 0:
        return 0

    created = 0
    for spec in stories_spec:
        story = StoryEntity.create(
            title=spec["title"],
            project_id=project.id,
            created_by=created_by,
            priority=spec["priority"],
            points=spec["points"],
            assigned_to=admin_id if spec["assign_to_admin"] else None,
        )
        if spec["status"] == StoryStatus.IN_PROGRESS:
            story.start()
        elif spec["status"] == StoryStatus.DONE:
            story.complete()
        elif spec["status"] == StoryStatus.BLOCKED:
            # No dedicated transition method for "blocked" — set directly via update_details.
            story.update_details(status=StoryStatus.BLOCKED)

        await story_repository.save(story)
        created += 1

    return created


async def seed_sample_data():
    """Seed realistic sample clients, projects, and stories."""

    admin_email = os.getenv("ADMIN_EMAIL", "admin@example.com").lower().strip()
    app_env = AppConfig.instance().env

    print("=" * 60)
    print("🌱 Sample Data Seed Script (clients, projects, stories)")
    print("=" * 60)
    print(f"App Environment: {app_env}")
    print("-" * 60)

    engine = get_engine()

    try:
        async with engine.get_session() as session:
            user_repository = UserRepositoryImpl(session)
            admin = await user_repository.find_by_email(Email(admin_email))
            if admin is None:
                print(f"❌ ERROR: No admin user found for {admin_email}")
                print("   Run `make seed-admin` first, then re-run this script.")
                sys.exit(1)

            client_repository = ClientRepositoryImpl(session)
            project_repository = ProjectRepositoryImpl(session)
            story_repository = StoryRepositoryImpl(session)

            clients_created = 0
            projects_created = 0
            stories_created = 0

            for client_index, client_data in enumerate(CLIENTS):
                client, created = await _get_or_create_client(client_repository, client_data, admin.workspace_id)
                clients_created += int(created)
                print(f"{'✅ Created' if created else '↪️  Existing'} client: {client.name}")

                for project_spec in PROJECTS_BY_CLIENT_INDEX[client_index]:
                    project, created = await _get_or_create_project(
                        session,
                        project_repository,
                        project_spec["code"],
                        client.id,
                        admin.id,
                        project_spec,
                        admin.workspace_id,
                    )
                    projects_created += int(created)
                    print(f"   {'✅ Created' if created else '↪️  Existing'} project: {project.code} — {project.name}")

                    stories_spec = STORIES_BY_PROJECT_CODE.get(project_spec["code"], [])
                    added = await _seed_stories_for_project(story_repository, project, admin.id, admin.id, stories_spec)
                    stories_created += added
                    if added:
                        print(f"      ✅ Seeded {added} stories")
                    else:
                        print("      ↪️  Stories already present, skipped")

            print("-" * 60)
            print("🎉 Seed complete")
            print(f"   Clients created:  {clients_created} (of {len(CLIENTS)} total)")
            print(f"   Projects created: {projects_created}")
            print(f"   Stories created:  {stories_created}")
            print("=" * 60)

    except Exception as e:
        print("❌ ERROR: Failed to seed sample data")
        print(f"   {type(e).__name__}: {e!s}")
        sys.exit(1)
    finally:
        await close_engine()


if __name__ == "__main__":
    asyncio.run(seed_sample_data())
