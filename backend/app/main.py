from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.health import router as health_router
from app.api.router import router as api_router
from app.core.config import get_settings
from app.core.errors import install_error_handlers
from app.schemas.errors import ERROR_RESPONSES


def create_app() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title="AgiPrevê — API demonstrativa",
        version="0.1.0",
        description=(
            "Protótipo demonstrativo não oficial, com dados fictícios. "
            "Sem integração com o Agibank."
        ),
        debug=False,
        responses=ERROR_RESPONSES,
    )
    install_error_handlers(application)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
        allow_headers=["Content-Type", "Authorization", "Idempotency-Key"],
    )
    application.include_router(health_router)
    application.include_router(api_router)
    return application


app = create_app()
