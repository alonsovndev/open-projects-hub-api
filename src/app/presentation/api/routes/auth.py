from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from src.app.application.auth.dto import LoginCommand
from src.app.application.auth.use_cases import LoginUseCase
from src.app.domain.auth.errors import InvalidCredentialsError
from src.app.presentation.api.dependencies import get_login_use_case
from src.app.presentation.api.schemas import LoginRequest, LoginResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse, status_code=status.HTTP_200_OK)
def login(
    payload: LoginRequest,
    use_case: Annotated[LoginUseCase, Depends(get_login_use_case)],
) -> LoginResponse:
    try:
        result = use_case.execute(
            LoginCommand(email=payload.email, password=payload.password)
        )
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc

    return LoginResponse(
        token=result.token,
        email=result.email,
        displayName=result.display_name,
        loggedInAt=result.logged_in_at,
    )
