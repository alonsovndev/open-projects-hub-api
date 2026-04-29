from typing import Union

from pydantic import BaseModel
from uuid import uuid4

from src.app.features.application.dtos.user_dto import UserCreateRequest, UserResponse
from src.app.features.domain.entities.user_entity import UserEntity
from src.app.features.domain.value_objects.email import Email
from src.shared.domain.value_objects.entity_id import EntityId

def map_entity_to_dto_user(user_entity:  Union[BaseModel, UserEntity]) -> UserResponse:
    """
    Convert a User Entity to a User DTO (Data Transfer Object).
    """

    full_name = f"{user_entity.first_name} {user_entity.last_name}"
    return UserResponse(
        id=str(user_entity.id),
        fullname=full_name,
        email=str(user_entity.email),

    )

def map_create_request_to_entity(payload: UserCreateRequest, password_hash: str) -> UserEntity:
    return UserEntity(
        id=EntityId.from_string(str(uuid4())),
        email=Email(str(payload.email).lower().strip()),
        first_name=payload.first_name.strip(),
        last_name=payload.last_name.strip(),
        password_hash=password_hash,
    )