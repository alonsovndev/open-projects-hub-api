"""Client API routes."""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status

from src.app.composition import (
    get_create_client_use_case,
    get_delete_client_use_case,
    get_get_client_by_id_use_case,
    get_get_clients_use_case,
    get_update_client_use_case,
)
from src.app.features.auth.presentation.auth_dependencies import get_current_user, require_admin
from src.app.features.clients.application.dtos.client_dto import (
    ClientResponse,
    CreateClientRequest,
    PaginatedClientsResponse,
    UpdateClientRequest,
)
from src.app.features.clients.application.use_cases.create_client import CreateClientUseCase
from src.app.features.clients.application.use_cases.delete_client import DeleteClientUseCase
from src.app.features.clients.application.use_cases.get_client_by_id import GetClientByIdUseCase
from src.app.features.clients.application.use_cases.get_clients import GetClientsUseCase
from src.app.features.clients.application.use_cases.update_client import UpdateClientUseCase
from src.app.shared.presentation.base_handler import BaseRouteHandler


router = APIRouter()
handler = BaseRouteHandler()


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    request: CreateClientRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: CreateClientUseCase = Depends(get_create_client_use_case),
) -> ClientResponse:
    """Create a new client. Admin only."""
    return await handler.execute_with_payload_extraction(  # type: ignore[no-any-return]
        execute_fn=lambda user_id: use_case.execute(request=request, created_by=user_id),
        current_user=current_user,
    )


@router.get(
    "",
    response_model=PaginatedClientsResponse,
)
async def get_clients(
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: GetClientsUseCase = Depends(get_get_clients_use_case),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> PaginatedClientsResponse:
    """Get all clients with pagination. Authenticated users only."""
    try:
        user_id = str(current_user["sub"])
        return await use_case.execute(user_id=user_id, offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve clients: {e!s}",
        ) from e


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
)
async def get_client_by_id(
    client_id: UUID,
    current_user: dict[str, Any] = Depends(get_current_user),
    use_case: GetClientByIdUseCase = Depends(get_get_client_by_id_use_case),
) -> ClientResponse:
    """Get a client by ID. Authenticated users only."""
    try:
        user_id = str(current_user["sub"])
        return await use_case.execute(client_id=client_id, user_id=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client: {e!s}",
        ) from e


@router.put(
    "/{client_id}",
    response_model=ClientResponse,
)
async def update_client(
    client_id: UUID,
    request: UpdateClientRequest,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: UpdateClientUseCase = Depends(get_update_client_use_case),
) -> ClientResponse:
    """Update a client. Admin only."""
    return await handler.execute_with_payload_extraction(  # type: ignore[no-any-return]
        execute_fn=lambda user_id: use_case.execute(client_id=client_id, request=request, created_by=user_id),
        current_user=current_user,
    )


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_client(
    client_id: UUID,
    current_user: dict[str, Any] = Depends(require_admin),
    use_case: DeleteClientUseCase = Depends(get_delete_client_use_case),
):
    """Delete a client. Admin only. Cannot delete if client has projects."""
    user_id = current_user.get("sub")
    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    try:
        await use_case.execute(client_id=client_id, created_by=user_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        # Database will raise error if client has projects (RESTRICT constraint)
        if "violates foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete client with associated projects",
            ) from e
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client: {e!s}",
        ) from e
