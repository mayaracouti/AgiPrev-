from fastapi import APIRouter

from app.api.health import HealthResponse, readiness
from app.modules.auth.dependencies import CurrentCustomer
from app.modules.auth.routers import router as auth_router
from app.modules.banking.routers import router as banking_router
from app.modules.banking.transaction_router import router as transaction_router
from app.modules.evaluation.router import router as evaluation_router
from app.modules.forecasting.router import router as forecast_router
from app.modules.notifications.router import router as notifications_router
from app.schemas.errors import ERROR_RESPONSES

router = APIRouter(prefix="/api/v1", responses=ERROR_RESPONSES)
router.include_router(auth_router)
router.include_router(banking_router)

router.include_router(transaction_router)
router.include_router(forecast_router)
router.include_router(evaluation_router)
router.include_router(notifications_router)

router.add_api_route(
    "/health", readiness, methods=["GET"], response_model=HealthResponse, tags=["health"]
)


@router.get("/observability")
def observability(customer: CurrentCustomer):
    from app.core.telemetry import counters

    return {"scope": "process_since_start", "counters": counters()}
