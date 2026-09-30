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
from src.app.features.clients.domain.exceptions.client_exceptions import (
    ClientEmailExistsError,
    ClientHasActiveProjectsError,
    ClientNotFoundError,
)
from src.app.shared.application.request_context import RequestContext
from src.app.shared.presentation.auth_dependencies import require_editor


router = APIRouter()


@router.post(
    "",
    response_model=ClientResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_client(
    request: CreateClientRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: CreateClientUseCase = Depends(get_create_client_use_case),
) -> ClientResponse:
    """
    Create a new client.

    Requires ADMIN role. The created_by user is extracted from the JWT token.

    Args:
        request: CreateClientRequest with client details (name, email, phone, etc.)
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected CreateClientUseCase

    Returns:
        ClientResponse with created client data

    Raises:
        400: Validation failed (invalid name, email, phone, etc.)
        401/403: Unauthorized or forbidden
        500: Internal server error
    """

    try:
        return await use_case.execute(request=request, ctx=ctx)
    except ClientEmailExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.get(
    "",
    response_model=PaginatedClientsResponse,
)
async def get_clients(
    ctx: RequestContext = Depends(require_editor),
    use_case: GetClientsUseCase = Depends(get_get_clients_use_case),
    offset: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=100),
) -> PaginatedClientsResponse:
    """
    Get all clients with pagination.

    Admin only: a client Viewer must not be able to enumerate the other clients a
    freelancer works with.

    Args:
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected GetClientsUseCase
        offset: Number of results to skip (default 0)
        limit: Maximum number of results (1-100, default 100)

    Returns:
        PaginatedClientsResponse with client list and pagination metadata

    Raises:
        401: Unauthorized
        403: Forbidden (admin only)
        500: Internal server error
    """
    return await use_case.execute(ctx=ctx, offset=offset, limit=limit)


@router.get(
    "/{client_id}",
    response_model=ClientResponse,
)
async def get_client_by_id(
    client_id: UUID,
    ctx: RequestContext = Depends(require_editor),
    use_case: GetClientByIdUseCase = Depends(get_get_client_by_id_use_case),
) -> ClientResponse:
    """
    Get a client by ID.

    Admin only, for the same reason as the list endpoint.

    Args:
        client_id: Client UUID
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected GetClientByIdUseCase

    Returns:
        ClientResponse with client data

    Raises:
        400: Invalid UUID
        401: Unauthorized
        403: Forbidden (admin only)
        404: Client not found
        500: Internal server error
    """

    try:
        return await use_case.execute(client_id=client_id, ctx=ctx)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e


@router.patch(
    "/{client_id}",
    response_model=ClientResponse,
)
async def update_client(
    client_id: UUID,
    request: UpdateClientRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: UpdateClientUseCase = Depends(get_update_client_use_case),
) -> ClientResponse:
    """
    Update a client.

    Requires ADMIN role.

    Args:
        client_id: Client UUID
        request: UpdateClientRequest with fields to update
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected UpdateClientUseCase

    Returns:
        ClientResponse with updated client data

    Raises:
        400: Validation failed
        401/403: Unauthorized or forbidden
        404: Client not found
        500: Internal server error
    """

    try:
        return await use_case.execute(client_id=client_id, request=request, ctx=ctx)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ClientEmailExistsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e


@router.delete(
    "/{client_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_client(
    client_id: UUID,
    ctx: RequestContext = Depends(require_editor),
    use_case: DeleteClientUseCase = Depends(get_delete_client_use_case),
):
    """
    Delete a client.

    Requires ADMIN role. Cannot delete if the client still has active projects;
    archived projects are removed as part of the deletion.

    Args:
        client_id: Client UUID
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected DeleteClientUseCase

    Raises:
        401/403: Unauthorized or forbidden
        404: Client not found
        409: Client still has active projects
        500: Internal server error
    """

    try:
        await use_case.execute(client_id=client_id, ctx=ctx)
    except ClientNotFoundError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except ClientHasActiveProjectsError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e)) from e
