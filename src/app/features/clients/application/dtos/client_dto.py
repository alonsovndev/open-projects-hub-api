"""Client Data Transfer Objects."""

from pydantic import BaseModel, ConfigDict, field_validator
from pydantic.alias_generators import to_camel

from src.app.features.clients.domain.validators.client_validators import ClientValidators


class CreateClientRequest(BaseModel):
    """Request DTO for creating a client."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    address: str | None = None
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str) -> str:
        """Validate client name using domain validators."""
        ClientValidators.validate_name(name)
        return name

    @field_validator("company")
    @classmethod
    def validate_company(cls, company: str | None) -> str | None:
        """Validate company name using domain validators."""
        if company:
            ClientValidators.validate_company(company)
        return company


class UpdateClientRequest(BaseModel):
    """Request DTO for updating a client."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    name: str | None = None
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    address: str | None = None
    notes: str | None = None

    @field_validator("name")
    @classmethod
    def validate_name(cls, name: str | None) -> str | None:
        """Validate client name using domain validators."""
        if name is not None:
            ClientValidators.validate_name(name)
        return name

    @field_validator("company")
    @classmethod
    def validate_company(cls, company: str | None) -> str | None:
        """Validate company name using domain validators."""
        if company is not None:
            ClientValidators.validate_company(company)
        return company


class ClientResponse(BaseModel):
    """Response DTO for client data."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
        from_attributes=True,
    )

    id: str
    name: str
    email: str | None = None
    phone: str | None = None
    company: str | None = None
    address: str | None = None
    notes: str | None = None
    created_at: str
    updated_at: str


class PaginatedClientsResponse(BaseModel):
    """Response DTO for paginated clients list."""

    model_config = ConfigDict(
        alias_generator=to_camel,
        populate_by_name=True,
    )

    items: list[ClientResponse]
    total: int
    page: int
    per_page: int
