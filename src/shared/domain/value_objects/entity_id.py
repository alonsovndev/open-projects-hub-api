from uuid import UUID, uuid4
from dataclasses import dataclass


@dataclass(frozen=True)
class EntityId:
    value: UUID

    def __post_init__(self):
        if not isinstance(self.value, UUID):
            raise ValueError("EntityId must be a valid UUID")

    @classmethod
    def generate(cls) -> "EntityId":
        return cls(uuid4())

    @classmethod
    def from_string(cls, entity_id: str) -> "EntityId":
        try:
            return cls(UUID(entity_id))
        except ValueError:
            raise ValueError(f"Invalid UUID format: {entity_id}")

    def __str__(self) -> str:
        return str(self.value)
