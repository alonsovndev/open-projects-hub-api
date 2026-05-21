"""Dependency injection for clients feature."""
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.app.features.clients.application.use_cases.create_client import CreateClientUseCase
from src.app.features.clients.application.use_cases.delete_client import DeleteClientUseCase
from src.app.features.clients.application.use_cases.get_client_by_id import GetClientByIdUseCase
from src.app.features.clients.application.use_cases.get_clients import GetClientsUseCase
from src.app.features.clients.application.use_cases.update_client import UpdateClientUseCase
from src.app.features.clients.domain.repositories.client_repository import ClientRepository
from src.app.features.clients.infrastructure.repositories.client_repository_impl import ClientRepositoryImpl
from src.app.shared.presentation.dependencies import get_database_session


# Repository factory
async def get_client_repository(
    session: AsyncSession = Depends(get_database_session),
) -> ClientRepository:
    """
    Get client repository instance.
    
    Args:
        session: Database session
        
    Returns:
        ClientRepository interface
    """
    return ClientRepositoryImpl(session)


# Use case factories
async def get_create_client_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> CreateClientUseCase:
    """
    Get CreateClientUseCase instance.
    
    Args:
        repository: Client repository
        
    Returns:
        CreateClientUseCase instance
    """
    return CreateClientUseCase(repository)


async def get_get_clients_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> GetClientsUseCase:
    """
    Get GetClientsUseCase instance.
    
    Args:
        repository: Client repository
        
    Returns:
        GetClientsUseCase instance
    """
    return GetClientsUseCase(repository)


async def get_get_client_by_id_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> GetClientByIdUseCase:
    """
    Get GetClientByIdUseCase instance.
    
    Args:
        repository: Client repository
        
    Returns:
        GetClientByIdUseCase instance
    """
    return GetClientByIdUseCase(repository)


async def get_update_client_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> UpdateClientUseCase:
    """
    Get UpdateClientUseCase instance.
    
    Args:
        repository: Client repository
        
    Returns:
        UpdateClientUseCase instance
    """
    return UpdateClientUseCase(repository)


async def get_delete_client_use_case(
    repository: ClientRepository = Depends(get_client_repository),
) -> DeleteClientUseCase:
    """
    Get DeleteClientUseCase instance.
    
    Args:
        repository: Client repository
        
    Returns:
        DeleteClientUseCase instance
    """
    return DeleteClientUseCase(repository)
