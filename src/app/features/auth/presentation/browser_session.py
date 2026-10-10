import re
from datetime import UTC, datetime

from fastapi import HTTPException, Request, Response

from src.app.config.app_config import AppConfig
from src.app.features.auth.application.dtos.auth_dto import RefreshTokenRequest
from src.app.shared.infrastructure.security.jwt_handler import JWTHandler
from src.app.shared.presentation.middleware import get_allowed_cors_origins


REFRESH_COOKIE = "oph_refresh_token"
COOKIE_PATH = "/v1/auth"
BROWSER_SESSION_OPENAPI = {
    "parameters": [
        {
            "name": "X-Session-Mode",
            "in": "header",
            "schema": {"type": "string", "enum": ["cookie"]},
            "description": "Opt into an HttpOnly refresh-cookie session; requires a trusted Origin.",
        },
        {
            "name": "Origin",
            "in": "header",
            "schema": {"type": "string"},
            "description": "Required and checked against configured trusted origins in cookie mode.",
        },
    ],
}


def is_browser_session(request: Request) -> bool:
    mode = request.headers.get("X-Session-Mode")
    if mode not in (None, "cookie"):
        raise HTTPException(status_code=400, detail="Invalid session mode")
    if mode != "cookie":
        return False
    config = AppConfig.instance()
    origins = get_allowed_cors_origins()
    frontend_origin = config.get_config("app.frontend_base_url", "").rstrip("/")
    if frontend_origin:
        origins.append(frontend_origin)
    origin = request.headers.get("Origin")
    local_origin = config.env == "local" and origin and re.fullmatch(r"http://(localhost|127\.0\.0\.1):\d+", origin)
    if not origin or origin == "null" or (origin not in origins and not local_origin):
        raise HTTPException(status_code=403, detail="Untrusted session origin")
    return True


def refresh_request(request: Request, payload: RefreshTokenRequest | None) -> RefreshTokenRequest:
    if is_browser_session(request):
        if payload is not None:
            raise HTTPException(status_code=422, detail="Cookie sessions do not accept body credentials")
        token = request.cookies.get(REFRESH_COOKIE)
        if not token:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return RefreshTokenRequest(refresh_token=token)
    if payload is None:
        raise HTTPException(status_code=422, detail="Refresh token is required")
    return payload


def set_refresh_cookie(response: Response, token: str, jwt_handler: JWTHandler) -> None:
    claims = jwt_handler.decode_refresh_token(token)
    remaining = max(0, int(claims["exp"] - datetime.now(UTC).timestamp()))
    response.set_cookie(
        REFRESH_COOKIE,
        token,
        httponly=True,
        secure=AppConfig.instance().env not in ("local", "test"),
        samesite="lax",
        path=COOKIE_PATH,
        max_age=remaining if claims.get("remember_me", False) else None,
    )
    response.headers["Cache-Control"] = "no-store"


def clear_refresh_cookie(response: Response) -> None:
    response.delete_cookie(
        REFRESH_COOKIE,
        path=COOKIE_PATH,
        httponly=True,
        secure=AppConfig.instance().env not in ("local", "test"),
        samesite="lax",
    )
    response.headers["Cache-Control"] = "no-store"
