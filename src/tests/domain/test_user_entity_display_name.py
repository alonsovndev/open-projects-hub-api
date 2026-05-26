"""
Tests for UserEntity with displayName field.

Following API spec requirements:
- User should have displayName field (not computed from first_name/last_name)
- Role should be 'admin' or 'viewer' (not ADMIN/USER)
"""

from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


class TestUserEntityDisplayName:
    """Test UserEntity with displayName field."""

    def test_user_entity_has_display_name_field(self):
        """Test that UserEntity accepts display_name in constructor."""
        entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="John Doe",
            password_hash="hashed_password",
            role=UserRole.VIEWER,
        )

        assert entity.display_name == "John Doe"

    def test_user_entity_display_name_is_stored(self):
        """Test that display_name is stored, not computed."""
        entity = UserEntity(
            id=EntityId.generate(),
            email=Email("user@example.com"),
            display_name="Jane Smith",
            password_hash="hashed",
            role=UserRole.ADMIN,
        )

        # Should return stored value
        assert entity.display_name == "Jane Smith"

    def test_user_role_viewer_exists(self):
        """Test that UserRole.VIEWER enum exists."""
        assert hasattr(UserRole, "VIEWER")
        assert UserRole.VIEWER.value == "viewer"

    def test_user_role_admin_value(self):
        """Test that UserRole.ADMIN has correct value."""
        assert UserRole.ADMIN.value == "admin"

    def test_user_is_admin_with_admin_role(self):
        """Test is_admin() returns True for admin role."""
        entity = UserEntity(
            id=EntityId.generate(),
            email=Email("admin@example.com"),
            display_name="Admin User",
            password_hash="hashed",
            role=UserRole.ADMIN,
        )

        assert entity.is_admin() is True

    def test_user_is_admin_with_viewer_role(self):
        """Test is_admin() returns False for viewer role."""
        entity = UserEntity(
            id=EntityId.generate(),
            email=Email("viewer@example.com"),
            display_name="Viewer User",
            password_hash="hashed",
            role=UserRole.VIEWER,
        )

        assert entity.is_admin() is False
