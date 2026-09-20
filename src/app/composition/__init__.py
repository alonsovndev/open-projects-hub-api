"""
Composition Root - Central Dependency Injection

This module is the single source of truth for all application dependencies.
All dependency wiring (repository creation, use case initialization) happens here.

Usage in routes:
    from src.app.composition import get_create_project_use_case, get_list_projects_use_case

    @router.post("")
    async def create_project(
        use_case: CreateProjectUseCase = Depends(get_create_project_use_case),
    ):
        return await use_case.execute(...)

Architecture:
    composition/
      infrastructure.py     → DB session, external services (Level 1)
      repositories.py       → Shared repository factories (Level 2)
      features/*.py         → Feature use case factories (Level 3)
      __init__.py (this)    → Public API (Level 4)

Testing:
    Override dependencies in tests via FastAPI dependency_overrides:

    app.dependency_overrides[get_project_repository] = lambda: MockProjectRepo()

Design Pattern:
    Follows the Composition Root pattern from enterprise DI frameworks
    (ASP.NET Core, Spring Boot). All object graph construction is centralized,
    while business logic remains decoupled from infrastructure concerns.
"""

# ============================================================================
# Infrastructure (Level 1) - DB session, external services
# ============================================================================
# ============================================================================
# Feature: Auth
# ============================================================================
from src.app.composition.features.auth import (
    get_confirm_password_reset_use_case,
    get_login_use_case,
    get_logout_use_case,
    get_refresh_token_use_case,
    get_register_use_case,
    get_request_password_reset_use_case,
    get_resend_reset_code_use_case,
    get_revoke_all_user_tokens_use_case,
)

# ============================================================================
# Feature: Clients
# ============================================================================
from src.app.composition.features.clients import (
    get_create_client_use_case,
    get_delete_client_use_case,
    get_get_client_by_id_use_case,
    get_get_clients_use_case,
    get_update_client_use_case,
)

# ============================================================================
# Feature: Dashboard
# ============================================================================
from src.app.composition.features.dashboard import get_dashboard_stats_use_case

# ============================================================================
# Feature: Projects
# ============================================================================
from src.app.composition.features.projects import (
    get_archive_project_use_case,
    get_create_project_use_case,
    get_delete_project_use_case,
    get_list_projects_use_case,
    get_project_by_id_use_case,
    get_project_repository,
    get_reactivate_project_use_case,
    get_update_project_use_case,
)

# ============================================================================
# Feature: Refinement
# ============================================================================
from src.app.composition.features.refinement import (
    get_approve_draft_use_case,
    get_approve_drafts_bulk_use_case,
    get_delete_draft_use_case,
    get_draft_repository,
    get_generate_stories_use_case,
    get_list_drafts_use_case,
    get_update_draft_use_case,
)

# ============================================================================
# Feature: Stories
# ============================================================================
from src.app.composition.features.stories import (
    get_assign_story_use_case,
    get_create_story_use_case,
    get_delete_story_use_case,
    get_get_stories_by_project_use_case,
    get_get_story_by_id_use_case,
    get_list_stories_use_case,
    get_update_story_use_case,
)

# ============================================================================
# Feature: Users
# ============================================================================
from src.app.composition.features.users import (
    get_change_password_use_case,
    get_create_user_use_case,
    get_get_user_by_id_use_case,
    get_get_user_profile_use_case,
    get_update_user_profile_use_case,
)
from src.app.composition.infrastructure import get_ai_service, get_database_session, get_email_sender

# ============================================================================
# Repositories - Shared (Level 2)
# ============================================================================
from src.app.composition.repositories import (
    build_story_repository,
    get_client_repository,
    get_story_repository,
    get_user_repository,
)


# ============================================================================
# Public API Exports
# ============================================================================
__all__ = [  # noqa: RUF022 - grouped by category for readability
    # Infrastructure
    "get_ai_service",
    "get_database_session",
    "get_email_sender",
    # Repositories (shared)
    "build_story_repository",
    "get_client_repository",
    "get_story_repository",
    "get_user_repository",
    # Auth
    "get_confirm_password_reset_use_case",
    "get_login_use_case",
    "get_logout_use_case",
    "get_refresh_token_use_case",
    "get_register_use_case",
    "get_request_password_reset_use_case",
    "get_resend_reset_code_use_case",
    "get_revoke_all_user_tokens_use_case",
    # Clients
    "get_create_client_use_case",
    "get_delete_client_use_case",
    "get_get_client_by_id_use_case",
    "get_get_clients_use_case",
    "get_update_client_use_case",
    # Dashboard
    "get_dashboard_stats_use_case",
    # Projects
    "get_archive_project_use_case",
    "get_create_project_use_case",
    "get_delete_project_use_case",
    "get_list_projects_use_case",
    "get_project_by_id_use_case",
    "get_project_repository",
    "get_reactivate_project_use_case",
    "get_update_project_use_case",
    # Refinement
    "get_approve_draft_use_case",
    "get_approve_drafts_bulk_use_case",
    "get_delete_draft_use_case",
    "get_draft_repository",
    "get_generate_stories_use_case",
    "get_list_drafts_use_case",
    "get_update_draft_use_case",
    # Stories
    "get_assign_story_use_case",
    "get_create_story_use_case",
    "get_delete_story_use_case",
    "get_get_stories_by_project_use_case",
    "get_get_story_by_id_use_case",
    "get_list_stories_use_case",
    "get_update_story_use_case",
    # Users
    "get_change_password_use_case",
    "get_create_user_use_case",
    "get_get_user_by_id_use_case",
    "get_get_user_profile_use_case",
    "get_update_user_profile_use_case",
]
