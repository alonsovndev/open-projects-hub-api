from datetime import UTC, datetime

from src.app.shared.domain.value_objects.entity_id import EntityId


class BaseEntity:
    def __init__(
        self, id: EntityId | None = None, created_at: datetime | None = None, updated_at: datetime | None = None
    ):
        self.id: EntityId = id if id is not None else EntityId.generate()

        self.created_at: datetime = created_at if created_at is not None else datetime.now(tz=UTC)
        self.updated_at: datetime = updated_at if updated_at is not None else datetime.now(tz=UTC)

    def mark_as_updated(self) -> None:
        self.updated_at = datetime.now(tz=UTC)
