from datetime import datetime

from src.app.shared.domain.value_objects.entity_id import EntityId


class BaseEntity:
    def __init__(self, id: EntityId = None, created_at: datetime | None = None, updated_at: datetime | None = None):
        self.id: EntityId = id or EntityId.generate()

        self.created_at: datetime = created_at or datetime.now()
        self.updated_at: datetime = updated_at or datetime.now()

    def mark_as_updated(self) -> None:
        self.updated_at = datetime.now()
