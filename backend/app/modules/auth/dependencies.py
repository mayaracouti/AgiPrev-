from datetime import UTC, datetime
from typing import Annotated

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.core.security import token_hash
from app.db.session import get_session
from app.modules.auth.models import AuthSession
from app.modules.banking.models import Customer

bearer = HTTPBearer(auto_error=False)
Database = Annotated[Session, Depends(get_session)]


def get_auth_session(
    session: Database,
    credentials: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> AuthSession:
    if credentials is None or len(credentials.credentials) > 512:
        raise AppError(401, "UNAUTHENTICATED", "Entre no protótipo para continuar.")
    auth_session = session.scalar(
        select(AuthSession).where(
            AuthSession.token_hash == token_hash(credentials.credentials),
            AuthSession.revoked_at.is_(None),
            AuthSession.expires_at > datetime.now(UTC),
        )
    )
    if auth_session is None:
        raise AppError(401, "SESSION_EXPIRED", "Sessão inválida ou expirada. Entre novamente.")
    return auth_session


def get_customer(
    session: Database, auth: Annotated[AuthSession, Depends(get_auth_session)]
) -> Customer:
    customer = session.get(Customer, auth.customer_id)
    if customer is None:
        raise AppError(401, "UNAUTHENTICATED", "Sessão inválida.")
    return customer


CurrentCustomer = Annotated[Customer, Depends(get_customer)]
