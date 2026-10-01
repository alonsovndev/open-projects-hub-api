"""Workspace entity: the tenant boundary that owns clients and projects."""

from datetime import datetime

from src.app.shared.domain.entities.base_entity import BaseEntity
from src.app.shared.domain.value_objects.entity_id import EntityId


WORKSPACE_NAME_MAX_LENGTH = 100


class WorkspaceEntity(BaseEntity):
    def __init__(
        self,
        id: EntityId,
        name: str,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self._name = self._clean_name(name)
        super().__init__(id, created_at, updated_at)

    @property
    def name(self) -> str:
        return self._name

    def rename(self, name: str) -> None:
        self._name = self._clean_name(name)
        self.mark_as_updated()

    @staticmethod
    def _clean_name(name: str) -> str:
        cleaned_name = name.strip()
        if not cleaned_name or len(cleaned_name) > WORKSPACE_NAME_MAX_LENGTH:
            raise ValueError(f"Workspace name must be 1-{WORKSPACE_NAME_MAX_LENGTH} characters")
        return cleaned_name

    @classmethod
    def create(cls, name: str) -> "WorkspaceEntity":
        return cls(id=EntityId.generate(), name=name)

    @staticmethod
    def default_name_for(display_name: str) -> str:
        return f"{display_name}'s workspace"[:WORKSPACE_NAME_MAX_LENGTH]
