"""
Story authorization service.

Contains business logic for story ownership and permission checks.
"""

from src.app.composition.repositories import build_story_repository
from src.app.features.user.domain.value_objects.user_role import UserRole
from src.app.shared.domain.value_objects.entity_id import EntityId


class StoryAuthorizationService:
    """Service to handle story-level authorization checks."""

    @staticmethod
    async def is_story_owner_or_admin(
        session,
        story_id: str,
        user_id: str,
        user_role: str,
    ) -> tuple[bool, str | None]:
        """
        Check if user is story owner or has admin role.

        Args:
            session: Database session
            story_id: Story UUID as string
            user_id: User UUID as string
            user_role: User role from JWT token

        Returns:
            Tuple of (is_authorized, error_detail)
            - (True, None) if authorized
            - (False, error_message) if not authorized

        Raises:
            ValueError: If story_id format is invalid
        """
        # Admin bypass - admins can access any story
        if user_role == UserRole.ADMIN.value:
            return True, None

        # Parse story ID
        story_entity_id = EntityId.from_string(story_id)

        # Get story from repository
        story_repo = build_story_repository(session)
        story = await story_repo.find_by_id(story_entity_id.value)

        if not story:
            return False, "Story not found"

        # Check ownership
        if story.created_by.value != user_id:
            return False, "Not authorized to modify this story. Only the creator or an admin can modify stories."

        return True, None
