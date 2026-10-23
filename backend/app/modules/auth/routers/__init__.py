from datetime import UTC, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Response

from app.modules.auth.dependencies import CurrentCustomer, Database, get_auth_session
from app.modules.auth.models import AuthSession
from app.modules.auth.schemas import LoginRequest, LoginResponse
from app.modules.auth.services import authenticate
from app.modules.banking.repositories import BankingRepository
from app.modules.banking.schemas import CustomerResponse

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=LoginResponse)
def login(body: LoginRequest, session: Database, response: Response):
    customer, token, auth = authenticate(session, body.email, body.password.get_secret_value())
    response.headers["Cache-Control"] = "no-store"
    return LoginResponse(
        access_token=token,
        expires_at=auth.expires_at,
        customer=CustomerResponse.model_validate(customer),
        accounts=BankingRepository(session).accounts(customer.id),
    )


@router.get("/me", response_model=CustomerResponse)
def me(customer: CurrentCustomer):
    return customer


@router.post("/logout", status_code=204)
def logout(session: Database, auth: Annotated[AuthSession, Depends(get_auth_session)]):
    auth.revoked_at = datetime.now(UTC)
    session.commit()
    return Response(status_code=204)
