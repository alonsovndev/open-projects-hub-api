from typing import Union

from pydantic import BaseModel
from uuid import uuid4

from src.app.features.user.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.user.domain.entities.user_entity import UserEntity
from src.app.features.user.domain.value_objects.email import Email
from src.app.shared.domain.value_objects.entity_id import EntityId

def map_entity_to_dto_user(user_entity:  Union[BaseModel, UserEntity]) -> UserResponse:
    """
    Convert a User Entity to a User DTO (Data Transfer Object).
    """

    return UserResponse(
        id=str(user_entity.id),
        email=str(user_entity.email),
        display_name=user_entity.display_name,
        role=str(user_entity.role.value),
    )

def map_create_request_to_entity(payload: UserCreateRequest, password_hash: str) -> UserEntity:
    return UserEntity(
        id=EntityId.from_string(str(uuid4())),
        email=Email(str(payload.email).lower().strip()),
        display_name=payload.display_name.strip(),
        password_hash=password_hash,
    )