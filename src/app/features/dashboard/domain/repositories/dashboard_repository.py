"""Dashboard repository interface."""

from abc import ABC, abstractmethod
from uuid import UUID


class DashboardRepository(ABC):
    """Abstract repository interface for dashboard queries."""

    @abstractmethod
    async def get_aggregated_stats(self, *, workspace_id: UUID, user_id: UUID | None = None) -> dict:
        """
        Get all dashboard count statistics in a single query.

        Args:
            workspace_id: Only projects and stories of this workspace are counted
            user_id: Optional user ID for user-specific stats

        Returns:
            Dictionary with aggregated statistics:
            - total_projects, active_projects, total_stories,
              assigned_stories, completed_stories
        """
