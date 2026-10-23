"""Idempotent development seed. Never overwrites existing credentials or ledger entries."""

from datetime import date
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.security import hash_password
from app.db.session import get_engine
from app.modules.banking.models import Account, Customer, LedgerEntry

PROFILES = (
    ("regular", "Gisele Santos", "gisele@demo.local", "2947.53"),
    ("variable", "Rafael Lima", "rafael@demo.local", "1875.00"),
    ("tight", "Ana Costa", "ana@demo.local", "420.00"),
)


def seed(session: Session, password: str) -> None:
    for profile, name, email, opening in PROFILES:
        customer = session.scalar(select(Customer).where(Customer.demo_profile == profile))
        if customer is None:
            customer = Customer(
                name=name, email=email, demo_profile=profile, password_hash=hash_password(password)
            )
            session.add(customer)
            session.flush()
        account = session.scalar(select(Account).where(Account.customer_id == customer.id))
        if account is None:
            account = Account(customer_id=customer.id, currency="BRL")
            session.add(account)
            session.flush()
        reference = f"opening-{profile}"
        existing = session.scalar(select(LedgerEntry).where(LedgerEntry.reference == reference))
        if existing is None:
            session.add(
                LedgerEntry(
                    account_id=account.id,
                    amount=Decimal(opening),
                    direction="credit",
                    description="Crédito inicial fictício",
                    occurred_on=date(2026, 10, 23),
                    reference=reference,
                )
            )
    session.commit()


if __name__ == "__main__":
    settings = get_settings()
    if settings.app_env != "development" or settings.demo_password is None:
        raise SystemExit("Configure APP_ENV=development and DEMO_PASSWORD before seeding.")
    with Session(get_engine()) as session:
        seed(session, settings.demo_password.get_secret_value())
    print("Perfis, contas e créditos iniciais fictícios disponíveis; seed idempotente concluído.")
