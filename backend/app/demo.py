"""Prepare a dedicated fictitious demo account without resetting existing ledgers."""

import argparse
import json
from decimal import Decimal
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.db.session import get_engine
from app.modules.banking.models import Account, LedgerEntry
from app.modules.banking.repositories import BankingRepository
from app.modules.banking.transactions import TransactionInput, post_transaction
from app.modules.forecasting.analytics import dashboard
from app.modules.simulation.generator import generate, identifier


def prepare_demo(session: Session, seed: int, password: str) -> dict:
    generate(session, seed=seed, count=6, password=password)
    account_id = identifier(seed, 2, "account")
    account = session.get(Account, account_id)
    key = uuid5(NAMESPACE_URL, f"agipreve-demo-budget-v1:{seed}")
    previous = session.scalar(
        select(LedgerEntry).where(LedgerEntry.reference == f"{account_id}:{key}")
    )
    balance = BankingRepository(session).balance(account_id)
    if previous is None:
        if balance <= Decimal("50.00"):
            raise ValueError("Use a fresh demo seed with sufficient fictitious balance")
        post_transaction(
            session,
            account.customer_id,
            account_id,
            TransactionInput(
                amount=format(balance - Decimal("50.00"), ".2f"),
                description="Preparação demonstrativa de orçamento fictício",
                idempotency_key=key,
            ),
            "expense",
        )
    summary = dashboard(session, account_id)
    session.commit()
    return {
        "seed": seed,
        "dataset": "synthetic-v1",
        "email": f"synthetic-{seed}-2@demo.local",
        "account_id": str(account_id),
        "reused": previous is not None,
        "dashboard": summary,
        "notice": "Não redefine saldo ou relógio; repetir seed preserva movimentos existentes.",
    }


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--seed", type=int, default=4241)
    args = parser.parse_args()
    settings = get_settings()
    if settings.app_env != "development" or settings.demo_password is None:
        raise SystemExit("Configure APP_ENV=development e DEMO_PASSWORD fictícia.")
    with Session(get_engine()) as session:
        print(
            json.dumps(prepare_demo(session, args.seed, settings.demo_password.get_secret_value()))
        )
