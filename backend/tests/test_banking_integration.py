from datetime import UTC, date, datetime, timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from sqlalchemy import select

from app.core.security import token_hash
from app.modules.auth.models import AuthSession
from app.modules.banking.models import Account, Customer, LedgerEntry
from app.modules.banking.repositories import BankingRepository
from app.seed import seed

pytestmark = pytest.mark.integration


def login(client, email="gisele@demo.local"):
    response = client.post(
        "/api/v1/auth/login", json={"email": email, "password": "demo-test-only-2026"}
    )
    assert response.status_code == 200
    return response.json()


def test_seed_is_idempotent_and_each_customer_has_an_account(pg_client):
    client, session = pg_client
    seed(session, "different-do-not-overwrite")
    customers = client.get("/api/v1/customers").json()
    assert len(customers) == 3
    assert "password_hash" not in customers[0]
    assert len(list(session.scalars(select(Account)))) == 3
    assert len(list(session.scalars(select(LedgerEntry)))) == 3
    assert login(client)["customer"]["email"] == "gisele@demo.local"


def test_balance_matches_credits_and_debits_and_uses_decimal_strings(pg_client):
    client, session = pg_client
    auth = login(client)
    account_id = auth["accounts"][0]["id"]
    account = session.scalar(
        select(Account).join(Customer).where(Customer.email == "gisele@demo.local")
    )
    session.add(
        LedgerEntry(
            account_id=account.id,
            amount=Decimal("0.29"),
            direction="debit",
            description="Débito de teste",
            occurred_on=date(2026, 10, 23),
            reference="integration-debit",
        )
    )
    session.commit()
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    response = client.get(f"/api/v1/accounts/{account_id}/balance", headers=headers)
    assert response.status_code == 200
    assert response.json()["balance"] == "2947.24"
    assert response.headers["cache-control"] == "no-store"
    entries = client.get(f"/api/v1/accounts/{account_id}/ledger", headers=headers).json()
    assert all(isinstance(item["amount"], str) for item in entries)


def test_empty_ledger_has_exact_zero_balance(pg_client):
    _, session = pg_client
    customer = Customer(
        name="Empty", email="empty@demo.local", demo_profile="empty", password_hash="unused"
    )
    session.add(customer)
    session.flush()
    account = Account(customer_id=customer.id)
    session.add(account)
    session.flush()
    assert BankingRepository(session).balance(account.id) == Decimal("0.00")


def test_session_cannot_access_another_customers_accounts(pg_client):
    client, _ = pg_client
    first, second = login(client), login(client, "ana@demo.local")
    headers = {"Authorization": f"Bearer {first['access_token']}"}
    other_id = second["accounts"][0]["id"]
    for suffix in ("", "/balance", "/ledger"):
        response = client.get(f"/api/v1/accounts/{other_id}{suffix}", headers=headers)
        assert response.status_code == 404
    accounts = client.get("/api/v1/accounts", headers=headers).json()
    assert len(accounts) == 1
    assert accounts[0]["customer_id"] == first["customer"]["id"]


def test_invalid_login_missing_token_expired_token_and_logout(pg_client):
    client, session = pg_client
    bad = client.post(
        "/api/v1/auth/login", json={"email": "gisele@demo.local", "password": "wrong"}
    )
    assert bad.status_code == 401
    assert client.get("/api/v1/accounts").status_code == 401
    auth = login(client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    assert client.post("/api/v1/auth/logout", headers=headers).status_code == 204
    assert client.get("/api/v1/auth/me", headers=headers).status_code == 401
    auth = login(client)
    record = session.scalar(
        select(AuthSession).where(AuthSession.token_hash == token_hash(auth["access_token"]))
    )
    record.expires_at = datetime.now(UTC) - timedelta(seconds=1)
    session.commit()
    assert (
        client.get(
            "/api/v1/auth/me", headers={"Authorization": f"Bearer {auth['access_token']}"}
        ).status_code
        == 401
    )


def test_invalid_identifier_negative_pagination_and_foreign_unknown_accounts(pg_client):
    client, _ = pg_client
    auth = login(client)
    headers = {"Authorization": f"Bearer {auth['access_token']}"}
    account_id = auth["accounts"][0]["id"]
    assert client.get("/api/v1/accounts/not-a-uuid/balance", headers=headers).status_code == 422
    assert client.get(f"/api/v1/accounts/{uuid4()}/balance", headers=headers).status_code == 404
    assert (
        client.get(f"/api/v1/accounts/{account_id}/ledger?limit=0", headers=headers).status_code
        == 422
    )
    assert (
        client.get(f"/api/v1/accounts/{account_id}/ledger?offset=-1", headers=headers).status_code
        == 422
    )


def test_database_rejects_negative_amounts_and_duplicate_references(pg_client):
    from sqlalchemy.exc import IntegrityError

    _, session = pg_client
    account = session.scalar(select(Account).limit(1))
    for amount, reference in (
        (Decimal("-0.01"), "negative"),
        (Decimal("0.00"), "zero"),
        (Decimal("1.00"), "opening-regular"),
    ):
        with pytest.raises(IntegrityError), session.begin_nested():
            session.add(
                LedgerEntry(
                    account_id=account.id,
                    amount=amount,
                    direction="credit",
                    description="Invalid test entry",
                    occurred_on=date(2026, 10, 23),
                    reference=reference,
                )
            )
            session.flush()
