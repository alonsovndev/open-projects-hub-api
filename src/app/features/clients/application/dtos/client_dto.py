"""Client Data Transfer Objects."""
from typing import Optional, List
from pydantic import BaseModel, Field, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.clients.domain.validators.client_validators import ClientValidators


class CreateClientRequest(BaseModel):
    """Request DTO for creating a client."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: str) -> str:
        """Validate client name using domain validators."""
        ClientValidators.validate_name(v)
        return v
    
    @field_validator("company")
    @classmethod
    def validate_company(cls, v: Optional[str]) -> Optional[str]:
        """Validate company name using domain validators."""
        if v:
            ClientValidators.validate_company(v)
        return v


class UpdateClientRequest(BaseModel):
    """Request DTO for updating a client."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    name: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    
    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        """Validate client name using domain validators."""
        if v is not None:
            ClientValidators.validate_name(v)
        return v
    
    @field_validator("company")
    @classmethod
    def validate_company(cls, v: Optional[str]) -> Optional[str]:
        """Validate company name using domain validators."""
        if v is not None:
            ClientValidators.validate_company(v)
        return v


class ClientResponse(BaseModel):
    """Response DTO for client data."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )
    
    id: str
    name: str
    email: Optional[str] = None
    phone: Optional[str] = None
    company: Optional[str] = None
    address: Optional[str] = None
    notes: Optional[str] = None
    created_at: str
    updated_at: str


class PaginatedClientsResponse(BaseModel):
    """Response DTO for paginated clients list."""
    
    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )
    
    items: List[ClientResponse]
    total: int
    page: int
    per_page: int
