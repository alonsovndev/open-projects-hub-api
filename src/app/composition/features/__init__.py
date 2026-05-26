"""
Feature-specific dependency composition.

Exports use case factories from all feature modules for centralized access.

Usage:
    from src.app.composition.features import (
        get_create_project_use_case,
        get_login_use_case,
    )

Organization:
    Each feature module (auth.py, projects.py, etc.) contains:
    - Feature-specific repository factories (not shared)
    - All use case factories for that feature
    - Explicit dependencies on infrastructure and shared repositories
"""

# This file will be populated in Phase 4 with exports from:
# - auth.py
# - clients.py
# - dashboard.py
# - projects.py
# - refinement.py
# - stories.py
# - users.py
