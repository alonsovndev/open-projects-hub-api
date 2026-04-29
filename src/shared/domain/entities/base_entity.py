from datetime import datetime
from typing import Optional

from src.shared.domain.value_objects.entity_id import EntityId
from src.shared.utils.date_util import get_current_datetime


class BaseEntity:

    def __init__(self,
                 id: EntityId = None,
                 created_at: Optional[datetime] = None,
                 updated_at: Optional[datetime] = None
                 ):
        self.id: EntityId = id or EntityId.generate()

        self.created_at: datetime = created_at or get_current_datetime()
        self.updated_at: datetime = updated_at or get_current_datetime()

    def mark_as_updated(self) -> None:
        self.updated_at = get_current_datetime()
