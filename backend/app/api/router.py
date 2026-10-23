from fastapi import APIRouter

from app.modules.auth.routers import router as auth_router
from app.modules.banking.routers import router as banking_router
from app.schemas.errors import ERROR_RESPONSES
from app.api.health import readiness, HealthResponse

router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)
router.include_router(auth_router)
router.include_router(banking_router)

router.add_api_route("/health", readiness, methods=["GET"], response_model=HealthResponse, tags=["health"])
