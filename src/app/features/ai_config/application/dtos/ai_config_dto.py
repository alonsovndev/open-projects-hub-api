"""Data transfer objects for AI credits and API key management."""

from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field
from pydantic.alias_generators import to_camel

from src.app.features.ai_config.domain.validators.api_key_validators import MAX_KEY_LENGTH
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider


class CreditBalanceResponse(BaseModel):
    """Current AI credit balance for the authenticated user."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    credits: int
    total_granted: int


class ApiKeyResponse(BaseModel):
    """
    A configured provider key, as the API is willing to describe it.

    `masked_key` is the only representation of the secret that exists above the database;
    there is deliberately no field carrying the key itself (FR-010-07).
    """

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    provider: AIProvider
    masked_key: str
    configured_at: datetime
    last_validated_at: datetime | None = None


class ListApiKeysResponse(BaseModel):
    """Every provider key the authenticated user has configured."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    keys: list[ApiKeyResponse]


class SaveApiKeyRequest(BaseModel):
    """Request to add or replace the key for one provider."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    provider: AIProvider
    # Length is bounded here so an oversized body is rejected before it reaches a log or a
    # provider call. Format is checked in the domain validator, which knows each provider's
    # prefix; repeating that rule in the DTO would let the two drift apart.
    api_key: str = Field(min_length=1, max_length=MAX_KEY_LENGTH)


class ValidateApiKeyResponse(BaseModel):
    """Result of testing a stored key against its provider."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)

    provider: AIProvider
    valid: bool
    # True when the provider reports quota at or above 80% consumed (FR-010-12). Providers
    # that expose no usage headers always report False.
    quota_warning: bool = False
