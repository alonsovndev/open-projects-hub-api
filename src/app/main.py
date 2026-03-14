from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.app.presentation.api.routes.auth import router as auth_router

LOCAL_FRONTEND_ORIGIN = "http://localhost:5173"


def create_app() -> FastAPI:
    app = FastAPI(title="Open Projects Hub API")

    app.add_middleware(
        CORSMiddleware,
        allow_origins=[LOCAL_FRONTEND_ORIGIN],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health")
    def healthcheck() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(auth_router)
    return app


app = create_app()
