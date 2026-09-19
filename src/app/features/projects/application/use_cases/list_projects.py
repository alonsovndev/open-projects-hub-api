"""List projects use case."""

from datetime import datetime

from src.app.features.projects.application.dtos.project_dto import ProjectResponse
from src.app.features.projects.application.mappers.project_mapper import to_project_response
from src.app.features.projects.domain.repositories.project_repository import ProjectRepository
from src.app.shared.application.dtos.pagination_dto import PaginatedResponse
from src.app.shared.logging import get_logger, set_user_id


class ListProjectsUseCase:
    """Use case for listing projects with pagination."""

    def __init__(self, project_repository: ProjectRepository):
        """
        Initialize use case.

        Args:
            project_repository: Project repository
        """
        self._repository = project_repository

    async def execute(
        self,
        user_id: str,
        limit: int = 20,
        offset: int = 0,
        status: str | None = None,
        client_id: str | None = None,
        created_from: datetime | None = None,
        created_to: datetime | None = None,
        updated_from: datetime | None = None,
        updated_to: datetime | None = None,
        search: str | None = None,
    ) -> PaginatedResponse[ProjectResponse]:
        """
        Execute list projects use case.

        Args:
            user_id: Current user ID
            limit: Maximum number of results (default 20)
            offset: Number of results to skip (default 0)
            status: Optional status filter (active, completed, archived)
            client_id: Optional client UUID filter
            created_from: Optional lower bound on created_at
            created_to: Optional upper bound on created_at
            updated_from: Optional lower bound on updated_at
            updated_to: Optional upper bound on updated_at
            search: Optional substring match on name or code (case-insensitive)

        Returns:
            PaginatedResponse containing pagination metadata and ProjectResponse items
        """
        log = get_logger(__name__)
        set_user_id(user_id)
        log.info(
            "Listing projects",
            extra={
                "event_type": "projects.list.started",
                "offset": offset,
                "limit": limit,
                "status": status,
                "client_id": client_id,
                "search": search,
            },
        )

        total = await self._repository.count(
            status=status,
            client_id=client_id,
            created_from=created_from,
            created_to=created_to,
            updated_from=updated_from,
            updated_to=updated_to,
            search=search,
        )
        entities_with_clients = await self._repository.find_all(
            limit=limit,
            offset=offset,
            status=status,
            client_id=client_id,
            created_from=created_from,
            created_to=created_to,
            updated_from=updated_from,
            updated_to=updated_to,
            search=search,
        )

        # Batch query optimization: fetch all story counts in one database roundtrip
        project_ids = [entity.id.value for entity, _ in entities_with_clients]
        story_counts = await self._repository.get_story_counts_batch(project_ids) if project_ids else {}

        items = []
        for entity, client_name in entities_with_clients:
            total_stories, completed_stories = story_counts.get(entity.id.value, (0, 0))
            items.append(to_project_response(entity, client_name, total_stories, completed_stories))

        page = (offset // limit) + 1 if limit > 0 else 1

        log.info(
            "Projects listed successfully",
            extra={"event_type": "projects.list.success", "total": total, "returned": len(items)},
        )
        return PaginatedResponse(
            total=total,
            page=page,
            per_page=limit,
            items=items,
        )
