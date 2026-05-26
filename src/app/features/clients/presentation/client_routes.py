"""Client API routes."""

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


router = APIRouter()


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin)],
)
async def create_client(
    request: CreateClientRequest,
    use_case: CreateClientUseCase = Depends(get_create_client_use_case),
) -> ClientResponse:
    """Create a new client. Admin only."""
    try:
        return await use_case.execute(request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create client: {e!s}",
        )


@router.get(
    "",
    response_model=PaginatedClientsResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_clients(
    use_case: GetClientsUseCase = Depends(get_get_clients_use_case),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> PaginatedClientsResponse:
    """Get all clients with pagination. Authenticated users only."""
    try:
        return await use_case.execute(offset=offset, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve clients: {e!s}",
        )


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
    dependencies=[Depends(get_current_user)],
)
async def get_client_by_id(
    client_id: UUID,
    use_case: GetClientByIdUseCase = Depends(get_get_client_by_id_use_case),
) -> ClientResponse:
    """Get a client by ID. Authenticated users only."""
    try:
        return await use_case.execute(client_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve client: {e!s}",
        )


@router.put(
    "/{client_id}",
    response_model=ClientResponse,
    dependencies=[Depends(require_admin)],
)
async def update_client(
    client_id: UUID,
    request: UpdateClientRequest,
    use_case: UpdateClientUseCase = Depends(get_update_client_use_case),
) -> ClientResponse:
    """Update a client. Admin only."""
    try:
        return await use_case.execute(client_id, request)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to update client: {e!s}",
        )


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin)],
)
async def delete_client(
    client_id: UUID,
    use_case: DeleteClientUseCase = Depends(get_delete_client_use_case),
):
    """Delete a client. Admin only. Cannot delete if client has projects."""
    try:
        await use_case.execute(client_id)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except Exception as e:
        # Database will raise error if client has projects (RESTRICT constraint)
        if "violates foreign key constraint" in str(e).lower():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot delete client with associated projects",
            )
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to delete client: {e!s}",
        )
