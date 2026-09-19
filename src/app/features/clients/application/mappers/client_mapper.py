"""
Shared mapper for ClientEntity to ClientResponse.

Centralizes DTO mapping logic to reduce duplication across use cases.
"""

from src.app.features.clients.application.dtos.client_dto import ClientResponse
from src.app.features.clients.domain.entities.client_entity import ClientEntity


def to_client_response(entity: ClientEntity) -> ClientResponse:
    """
    Convert ClientEntity to ClientResponse DTO.

    Args:
        entity: ClientEntity domain object

    Returns:
        ClientResponse DTO with serialized entity data
    """
    return ClientResponse(
        id=str(entity.id.value),
        name=entity.name,
        email=entity.email.value if entity.email else None,
        phone=entity.phone.value if entity.phone else None,
        company=entity.company,
        address=entity.address,
        notes=entity.notes,
        created_at=entity.created_at.isoformat(),
        updated_at=entity.updated_at.isoformat(),
    )
