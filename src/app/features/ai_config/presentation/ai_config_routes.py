"""AI credit and API key management routes."""

from fastapi import APIRouter, Depends, status

from src.app.composition import (
    get_credit_balance_use_case,
    get_delete_api_key_use_case,
    get_list_api_keys_use_case,
    get_save_api_key_use_case,
    get_validate_api_key_use_case,
)
from src.app.features.ai_config.application.dtos.ai_config_dto import (
    ApiKeyResponse,
    CreditBalanceResponse,
    ListApiKeysResponse,
    SaveApiKeyRequest,
    ValidateApiKeyResponse,
)
from src.app.features.ai_config.application.use_cases.delete_api_key import DeleteApiKeyUseCase
from src.app.features.ai_config.application.use_cases.get_credit_balance import GetCreditBalanceUseCase
from src.app.features.ai_config.application.use_cases.list_api_keys import ListApiKeysUseCase
from src.app.features.ai_config.application.use_cases.save_api_key import SaveApiKeyUseCase
from src.app.features.ai_config.application.use_cases.validate_api_key import ValidateApiKeyUseCase
from src.app.features.ai_config.domain.value_objects.ai_provider import AIProvider
from src.app.shared.application.request_context import RequestContext
from src.app.shared.presentation.auth_dependencies import require_editor


router = APIRouter()


@router.get("/me/credits", response_model=CreditBalanceResponse)
async def get_credit_balance(
    ctx: RequestContext = Depends(require_editor),
    use_case: GetCreditBalanceUseCase = Depends(get_credit_balance_use_case),
) -> CreditBalanceResponse:
    """
    Get the caller's AI credit balance.

    Requires ADMIN or MEMBER role.

    Args:
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected GetCreditBalanceUseCase

    Returns:
        CreditBalanceResponse with remaining and originally granted credits
    """
    return await use_case.execute(user_id=str(ctx.user_id))


@router.get("/me/api-keys", response_model=ListApiKeysResponse)
async def list_api_keys(
    ctx: RequestContext = Depends(require_editor),
    use_case: ListApiKeysUseCase = Depends(get_list_api_keys_use_case),
) -> ListApiKeysResponse:
    """
    List the caller's configured provider keys, masked.

    There is no endpoint that returns a key in plaintext (FR-010-07); this is the only
    read path, and it exposes the mask alone.

    Args:
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected ListApiKeysUseCase

    Returns:
        ListApiKeysResponse with one masked entry per configured provider
    """
    return await use_case.execute(user_id=str(ctx.user_id))


@router.post("/me/api-keys", response_model=ApiKeyResponse, status_code=status.HTTP_201_CREATED)
async def save_api_key(
    payload: SaveApiKeyRequest,
    ctx: RequestContext = Depends(require_editor),
    use_case: SaveApiKeyUseCase = Depends(get_save_api_key_use_case),
) -> ApiKeyResponse:
    """
    Add or replace the caller's key for one provider.

    Posting again for the same provider rotates the key: the stored secret is overwritten,
    so the previous key stops working immediately.

    Args:
        payload: SaveApiKeyRequest with provider and the raw key
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected SaveApiKeyUseCase

    Returns:
        ApiKeyResponse describing the stored key in masked form

    Raises:
        400: Key does not match the provider's documented format
        422: Provider refused the key
        429: Validation budget for this user is spent
    """
    return await use_case.execute(request=payload, user_id=str(ctx.user_id))


@router.delete("/me/api-keys/{provider}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_api_key(
    provider: AIProvider,
    ctx: RequestContext = Depends(require_editor),
    use_case: DeleteApiKeyUseCase = Depends(get_delete_api_key_use_case),
) -> None:
    """
    Delete the caller's key for one provider.

    The key material is hard-deleted, not flagged (NFR-010-04).

    Args:
        provider: Provider whose key should be removed
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected DeleteApiKeyUseCase

    Raises:
        404: No key is configured for that provider
    """
    await use_case.execute(provider=provider, user_id=str(ctx.user_id))


@router.post("/me/api-keys/{provider}/validate", response_model=ValidateApiKeyResponse)
async def validate_api_key(
    provider: AIProvider,
    ctx: RequestContext = Depends(require_editor),
    use_case: ValidateApiKeyUseCase = Depends(get_validate_api_key_use_case),
) -> ValidateApiKeyResponse:
    """
    Re-test the caller's stored key against its provider.

    Args:
        provider: Provider whose key should be tested
        ctx: Caller identity and workspace (from JWT)
        use_case: Injected ValidateApiKeyUseCase

    Returns:
        ValidateApiKeyResponse reporting acceptance and any low-quota warning

    Raises:
        404: No key is configured for that provider
        422: Provider refused the key
        429: Validation budget for this user is spent
    """
    return await use_case.execute(provider=provider, user_id=str(ctx.user_id))
