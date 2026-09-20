"""Pytest configuration and shared fixtures."""

import sys
from pathlib import Path

import pytest


# Add src to path for imports
src_path = Path(__file__).parent.parent / "src"
if str(src_path) not in sys.path:
    sys.path.insert(0, str(src_path))

# Import all ORM models once, up front, so SQLAlchemy's mapper registry is fully
# populated before any test configures a mapper. Without this, string-based
# relationship() references (e.g. ProjectModel -> "StoryDraftModel") only resolve
# if the referenced model module happened to be imported by an earlier test —
# making failures depend on test collection order. Mirrors the same "DO NOT
# REMOVE" import list in alembic/env.py, which exists for the same reason.
from src.app.features.auth.infrastructure.models.account_lockout_model import AccountLockoutModel  # noqa: F401,E402
from src.app.features.auth.infrastructure.models.password_reset_code_model import (  # noqa: F401,E402
    PasswordResetCodeModel,
)
from src.app.features.auth.infrastructure.models.revoked_refresh_token_model import (  # noqa: F401,E402
    RevokedRefreshTokenModel,
)
from src.app.features.clients.infrastructure.models.client_model import ClientModel  # noqa: F401,E402
from src.app.features.projects.infrastructure.models.project_model import ProjectModel  # noqa: F401,E402
from src.app.features.refinement.infrastructure.models.story_draft_model import StoryDraftModel  # noqa: F401,E402
from src.app.features.stories.infrastructure.models.story_model import StoryModel  # noqa: F401,E402
from src.app.features.user.infrastructure.models.user_model import UserModel  # noqa: F401,E402


def pytest_configure(config):
    """Configure pytest markers."""
    config.addinivalue_line("markers", "unit: Unit tests")
    config.addinivalue_line("markers", "integration: Integration tests")
    config.addinivalue_line("markers", "e2e: End-to-end tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "auth: Authentication related tests")


@pytest.fixture(scope="session")
def project_root():
    """Get project root directory."""
    return Path(__file__).parent.parent
