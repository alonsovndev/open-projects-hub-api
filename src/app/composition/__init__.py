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
# Feature: AI Credits & API Keys
# ============================================================================
from src.app.composition.features.ai_config import (
    get_api_key_cipher,
    get_credit_balance_use_case,
    get_delete_api_key_use_case,
    get_key_validation_throttle,
    get_list_api_keys_use_case,
    get_refinement_provider_resolver,
    get_save_api_key_use_case,
    get_user_api_key_repository,
    get_validate_api_key_use_case,
)

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
    get_resend_verification_use_case,
    get_revoke_all_user_tokens_use_case,
    get_verify_email_use_case,
)

# ============================================================================
# Feature: Backlog
# ============================================================================
from src.app.composition.features.backlog import get_export_backlog_markdown_use_case, get_get_project_backlog_use_case

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
    get_approve_stories_bulk_use_case,
    get_approve_story_use_case,
    get_generate_stories_use_case,
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
    get_list_workspace_users_use_case,
    get_update_user_profile_use_case,
)

# ============================================================================
# Feature: Workspaces
# ============================================================================
from src.app.composition.features.workspaces import get_update_workspace_use_case
from src.app.composition.infrastructure import get_ai_service, get_database_session, get_email_sender

# ============================================================================
# Repositories - Shared (Level 2)
# ============================================================================
from src.app.composition.repositories import (
    build_story_repository,
    get_client_repository,
    get_story_repository,
    get_user_repository,
    get_workspace_repository,
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
    "get_workspace_repository",
    # Auth
    "get_confirm_password_reset_use_case",
    "get_login_use_case",
    "get_logout_use_case",
    "get_refresh_token_use_case",
    "get_register_use_case",
    "get_request_password_reset_use_case",
    "get_resend_reset_code_use_case",
    "get_resend_verification_use_case",
    "get_revoke_all_user_tokens_use_case",
    "get_verify_email_use_case",
    # AI Credits & API Keys
    "get_api_key_cipher",
    "get_credit_balance_use_case",
    "get_delete_api_key_use_case",
    "get_key_validation_throttle",
    "get_list_api_keys_use_case",
    "get_refinement_provider_resolver",
    "get_save_api_key_use_case",
    "get_user_api_key_repository",
    "get_validate_api_key_use_case",
    # Clients
    "get_create_client_use_case",
    "get_delete_client_use_case",
    "get_get_client_by_id_use_case",
    "get_get_clients_use_case",
    "get_update_client_use_case",
    # Backlog
    "get_export_backlog_markdown_use_case",
    "get_get_project_backlog_use_case",
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
    "get_approve_stories_bulk_use_case",
    "get_approve_story_use_case",
    "get_generate_stories_use_case",
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
    "get_list_workspace_users_use_case",
    "get_update_user_profile_use_case",
    # Workspaces
    "get_update_workspace_use_case",
]
