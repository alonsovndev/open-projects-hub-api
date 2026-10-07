"""Guard: every tenant repository method is confined to a workspace.

A repository method without a `workspace_id` parameter can read or change another
workspace's rows, and nothing else in the suite would notice. New methods therefore fail
here until they take `workspace_id` or are allowlisted with the reason they are safe.
"""

import inspect

import pytest

from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.dashboard.domain.repositories.dashboard_repository import DashboardRepository
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.features.stories.domain.repositories.story_repository import StoryRepository


TENANT_PORTS = [ClientRepository, ProjectRepository, StoryRepository, DashboardRepository]

# Methods that carry the workspace some other way. Each entry is a security decision.
UNSCOPED_BY_DESIGN = {
    # The entity carries its workspace_id; the implementation writes/filters with it.
    ("ClientRepository", "save"),
    ("ClientRepository", "update"),
    ("ProjectRepository", "save"),
    # Callers have already confirmed the project (create) or loaded the record through a
    # scoped read (update); documented on the port.
    ("StoryRepository", "save"),
    # The workspace is the argument itself.
    ("ProjectRepository", "count_active_by_workspace"),
    # The one deliberate cross-workspace read: a client stakeholder has no session, so the
    # unguessable, instance-wide-unique access code stands in for the workspace.
    ("ProjectRepository", "find_by_access_code"),
    # Scoped through BacklogQuery.workspace_id, which is a required field.
    ("StoryRepository", "find_backlog"),
    ("StoryRepository", "count_backlog"),
}


def port_methods():
    for port in TENANT_PORTS:
        for name, method in inspect.getmembers(port, predicate=inspect.isfunction):
            if getattr(method, "__isabstractmethod__", False):
                yield port.__name__, name, method


@pytest.mark.parametrize(("port", "name", "method"), list(port_methods()), ids=lambda value: str(value))
def test_tenant_repository_methods_take_a_workspace(port, name, method):
    if (port, name) in UNSCOPED_BY_DESIGN:
        return
    assert "workspace_id" in inspect.signature(method).parameters, (
        f"{port}.{name} has no workspace_id: it could reach another workspace's rows"
    )


def test_the_allowlist_names_only_existing_methods():
    existing = {(port, name) for port, name, _ in port_methods()}
    assert existing >= UNSCOPED_BY_DESIGN, sorted(UNSCOPED_BY_DESIGN - existing)
