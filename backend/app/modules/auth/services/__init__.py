import secrets
from datetime import UTC, datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.errors import AppError
from app.core.security import hash_password, token_hash, verify_password
from app.modules.auth.models import AuthSession
from app.modules.banking.models import Customer


def authenticate(session: Session, email: str, password: str | None = None) -> tuple[Customer, str, AuthSession]:
    customer = session.scalar(select(Customer).where(Customer.email == email.strip().lower()))
    # Passwordless profile selection is intentional in this fictitious prototype.
    # Keep password verification for older clients that still send a credential.
    encoded = customer.password_hash if customer else _DUMMY_HASH
    valid = password is None or verify_password(password, encoded)
    if not customer or not valid:
        raise AppError(401, "INVALID_CREDENTIALS", "Perfil ou senha demonstrativa inválidos.")
    token = secrets.token_urlsafe(32)
    auth_session = AuthSession(
        customer_id=customer.id,
        token_hash=token_hash(token),
        expires_at=datetime.now(UTC) + timedelta(minutes=get_settings().session_ttl_minutes),
    )
    session.add(auth_session)
    session.commit()
    return customer, token, auth_session


_DUMMY_HASH = hash_password("not-a-user-password")
