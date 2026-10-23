from concurrent.futures import ThreadPoolExecutor
from datetime import date
from decimal import Decimal
from uuid import UUID, uuid4

import pytest
from sqlalchemy import func, select
from sqlalchemy.orm import Session
from test_banking_integration import login

from app.core.errors import AppError
from app.modules.banking.models import Account, Customer, LedgerEntry
from app.modules.banking.repositories import BankingRepository
from app.modules.banking.transactions import TransactionInput, post_transaction
from app.modules.simulation.generator import ASOF, PROFILES, financial_rows, generate

pytestmark = pytest.mark.integration


def auth_context(client, email="gisele@demo.local"):
    auth = login(client, email)
    return auth["accounts"][0]["id"], {"Authorization": f"Bearer {auth['access_token']}"}


def payload(amount="10.00", **overrides):
    return {
        "amount": amount,
        "description": "Operação fictícia",
        "idempotency_key": str(uuid4()),
        **overrides,
    }


def test_credit_debit_pix_idempotency_validation_and_categories(pg_client):
    client, session = pg_client
    account, headers = auth_context(client)
    base = f"/api/v1/accounts/{account}"
    credit = payload("10.29")
    first = client.post(base + "/credits", json=credit, headers=headers)
    assert first.status_code == 200 and first.json()["balance"] == "2957.82"
    duplicate = client.post(base + "/credits", json=credit, headers=headers)
    assert duplicate.json() == first.json()
    assert (
        client.post(
            base + "/credits", json={**credit, "amount": "11.00"}, headers=headers
        ).status_code
        == 409
    )
    debit = payload("5.01", category_id="food")
    assert client.post(base + "/debits", json=debit, headers=headers).json()["balance"] == "2952.81"
    assert client.post(base + "/debits", json=debit, headers=headers).json()["balance"] == "2952.81"
    pix = payload("2.81", account_id=account, recipient="loja@demo.local")
    sent = client.post("/api/v1/pix/simulate", json=pix, headers=headers)
    assert sent.status_code == 200 and sent.json()["balance"] == "2950.00"
    assert client.post("/api/v1/pix/simulate", json=pix, headers=headers).json() == sent.json()
    before = session.scalar(select(func.count()).select_from(LedgerEntry))
    for invalid in ("0.00", "-1.00", "1.001", "NaN", 1.23, "10000000000000000.00"):
        assert (
            client.post(base + "/credits", json=payload(invalid), headers=headers).status_code
            == 422
        )
    assert (
        client.post(base + "/debits", json=payload("9999.00"), headers=headers).status_code == 409
    )
    assert (
        client.post(
            base + "/debits", json=payload(category_id="invalid"), headers=headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            "/api/v1/pix/simulate", json=payload(account_id=account), headers=headers
        ).status_code
        == 422
    )
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before
    tx = sent.json()["transaction"]["id"]
    changed = client.patch(
        base + f"/transactions/{tx}/category", json={"category_id": "transport"}, headers=headers
    )
    assert changed.status_code == 200 and changed.json()["category_id"] == "transport"
    assert client.get(base + "/balance", headers=headers).json()["balance"] == "2950.00"
    assert (
        client.patch(
            base + f"/transactions/{tx}/category", json={"category_id": "missing"}, headers=headers
        ).status_code
        == 422
    )
    foreign, other = auth_context(client, "rafael@demo.local")
    assert client.get(base + "/transactions", headers=other).status_code == 404
    assert client.post(base + "/credits", json=payload(), headers=other).status_code == 404
    assert (
        client.patch(
            f"/api/v1/accounts/{foreign}/transactions/{tx}/category",
            json={"category_id": "food"},
            headers=other,
        ).status_code
        == 404
    )
    categories = {row["id"] for row in client.get("/api/v1/categories").json()}
    assert all(row.category_id in categories for row in session.scalars(select(LedgerEntry)))


def test_cursor_order_filters_and_snapshot(pg_client):
    client, session = pg_client
    account, headers = auth_context(client)
    for i in range(7):
        session.add(
            LedgerEntry(
                account_id=UUID(account),
                occurred_on=date(2026, 10, 20 + i % 3),
                direction="credit",
                amount=Decimal("1.00"),
                description=f"Histórico {i}",
                reference=f"history-{i}",
                category_id="income",
            )
        )
    session.commit()
    path = f"/api/v1/accounts/{account}/transactions"
    response = client.get(path, params={"limit": 2}, headers=headers).json()
    rows = response["items"][:]
    # Insertion after the first page must not enter the in-progress snapshot.
    client.post(
        f"/api/v1/accounts/{account}/credits",
        json=payload(description="Posterior"),
        headers=headers,
    )
    while response["next_cursor"]:
        response = client.get(
            path, params={"limit": 2, "cursor": response["next_cursor"]}, headers=headers
        ).json()
        rows += response["items"]
    assert len(rows) == 8 and len({r["id"] for r in rows}) == 8
    assert [(r["occurred_on"], r["id"]) for r in rows] == sorted(
        [(r["occurred_on"], r["id"]) for r in rows], reverse=True
    )
    filtered = client.get(
        path,
        params={
            "search": "Histórico",
            "category_id": "income",
            "direction": "credit",
            "date_from": "2026-10-21",
            "date_to": "2026-10-22",
        },
        headers=headers,
    ).json()
    assert filtered["total"] == 4
    for params in (
        {"cursor": "bad!"},
        {"limit": 0},
        {"date_from": "2026-11-01", "date_to": "2026-10-01"},
    ):
        assert client.get(path, params=params, headers=headers).status_code == 422


def test_concurrent_retries_and_insufficient_funds(pg_client):
    client, session = pg_client
    account, _ = auth_context(client)
    customer_id = session.scalar(select(Account.customer_id).where(Account.id == UUID(account)))
    engine = session.get_bind()
    shared = TransactionInput(**payload("1.00"))

    def execute(body, kind):
        with Session(engine) as worker:
            try:
                return post_transaction(
                    worker, customer_id, UUID(account), body, kind
                ).transaction.id
            except AppError as exc:
                worker.rollback()
                return exc.code

    with ThreadPoolExecutor(max_workers=3) as pool:
        ids = list(pool.map(lambda _: execute(shared, "income"), range(3)))
    assert len(set(ids)) == 1
    with ThreadPoolExecutor(max_workers=2) as pool:
        results = list(
            pool.map(lambda _: execute(TransactionInput(**payload("2000.00")), "expense"), range(2))
        )
    assert results.count("INSUFFICIENT_FUNDS") == 1
    assert BankingRepository(session).balance(UUID(account)) == Decimal("948.53")


def test_clock_extra_events_salary_delay_and_no_future_leakage(pg_client):
    client, session = pg_client
    account, headers = auth_context(client)
    base = f"/api/v1/accounts/{account}"
    initial = client.get(base + "/scenario", headers=headers).json()
    salary = next(e for e in initial["pending_events"] if e["kind"] == "salary")
    delay = {
        "kind": "salary_delay",
        "scheduled_on": salary["date"],
        "delay_days": 5,
        "idempotency_key": str(uuid4()),
    }
    delayed = client.post(base + "/scenario/events", json=delay, headers=headers).json()
    assert client.post(base + "/scenario/events", json=delay, headers=headers).json() == delayed
    salary_after = next(e for e in delayed["pending_events"] if e["id"] == salary["id"])
    assert salary_after["date"] == "2026-11-10"
    for kind, amount in (("extra_income", "25.00"), ("extra_purchase", "10.00")):
        event = {
            "kind": kind,
            "amount": amount,
            "scheduled_on": "2026-10-24",
            "idempotency_key": str(uuid4()),
        }
        assert (
            client.post(base + "/scenario/events", json=event, headers=headers).status_code == 200
        )
        assert (
            client.post(base + "/scenario/events", json=event, headers=headers).status_code == 200
        )
    planned = client.get(base + "/scenario", headers=headers).json()
    assert Decimal(planned["scheduled_final_balance"]) == Decimal(
        initial["scheduled_final_balance"]
    ) + Decimal("15.00")
    assert client.get(base + "/balance", headers=headers).json()["balance"] == "2947.53"
    old_ids = {str(row.id) for row in session.scalars(select(LedgerEntry))}
    advanced = client.post(
        base + "/scenario/advance", json={"target_date": "2026-10-24"}, headers=headers
    ).json()
    assert advanced["balance"] == "2962.53" and advanced["processed_count"] == 2
    again = client.post(
        base + "/scenario/advance", json={"target_date": "2026-10-24"}, headers=headers
    ).json()
    assert again["processed_count"] == 0 and again["balance"] == advanced["balance"]
    assert old_ids <= {str(row.id) for row in session.scalars(select(LedgerEntry))}
    assert (
        client.post(
            base + "/scenario/advance", json={"target_date": "2026-10-23"}, headers=headers
        ).status_code
        == 422
    )
    assert (
        client.post(
            base + "/scenario/events", json={**delay, "delay_days": 6}, headers=headers
        ).status_code
        == 409
    )
    assert client.get(base + "/recurrences", headers=headers).json() == []


def test_1000_clients_12_months_100k_transactions_reconcile(pg_engine):
    engine, _ = pg_engine
    with Session(engine) as session:
        result = generate(session, seed=27, count=1000)
        assert result["created_customers"] == 1000 and result["created_transactions"] > 100000
        assert set(session.scalars(select(Customer.demo_profile).distinct())) == set(PROFILES)
        assert session.scalar(select(func.count()).select_from(Account)) == 1000
        # Reconcile every account independently against the deterministic source rows.
        from sqlalchemy import case

        totals = dict(
            session.execute(
                select(
                    LedgerEntry.account_id,
                    func.sum(
                        case(
                            (LedgerEntry.direction == "credit", LedgerEntry.amount),
                            else_=-LedgerEntry.amount,
                        )
                    ),
                ).group_by(LedgerEntry.account_id)
            ).all()
        )
        for i in range(1000):
            rows = financial_rows(27, i)
            expected = sum(
                (r["amount"] if r["direction"] == "credit" else -r["amount"] for r in rows),
                Decimal("0"),
            )
            assert totals[rows[0]["account_id"]] == expected
        assert session.scalar(select(func.max(LedgerEntry.occurred_on))) < ASOF
        assert generate(session, seed=27, count=1000)["created_transactions"] == 0
        assert all(
            email.endswith("@demo.local") for email in session.scalars(select(Customer.email))
        )
        print(f"DATASET: {result}")


def test_failed_commit_rolls_back_clock_and_all_debits(pg_client, monkeypatch):
    from app.modules.simulation.models import Scenario, ScheduledEvent
    from app.modules.simulation.services import advance, get_scenario

    client, session = pg_client
    account, _ = auth_context(client)
    scenario = get_scenario(session, UUID(account))
    session.add(
        ScheduledEvent(
            scenario_id=scenario.id,
            scheduled_on=date(2026, 10, 24),
            original_date=date(2026, 10, 24),
            direction="debit",
            amount=Decimal("15.00"),
            category_id="other",
            description="Evento de teste",
            kind="extra_purchase",
            processed=False,
        )
    )
    session.commit()
    customer_id = session.scalar(select(Account.customer_id).where(Account.id == UUID(account)))

    def fail_commit():
        raise RuntimeError("Injected failure after SQL flush")

    with pytest.raises(RuntimeError, match="Injected failure"):
        with Session(session.get_bind()) as worker:
            monkeypatch.setattr(worker, "commit", fail_commit)
            advance(worker, customer_id, UUID(account), date(2026, 10, 24))
    session.expire_all()
    assert BankingRepository(session).balance(UUID(account)) == Decimal("2947.53")
    assert session.get(Scenario, scenario.id).current_date == date(2026, 10, 23)
    assert (
        session.scalar(
            select(func.count())
            .select_from(ScheduledEvent)
            .where(ScheduledEvent.processed.is_(True))
        )
        == 0
    )


def test_generated_profiles_login_filters_and_recurrence_endpoint(pg_client):
    client, session = pg_client
    generate(session, seed=109, count=6, password="demo-test-only-2026")
    for profile in PROFILES:
        rows = client.get("/api/v1/customers", params={"profile": profile}).json()
        assert rows and all(row["demo_profile"] == profile for row in rows)
    account, headers = auth_context(client, "synthetic-109-0@demo.local")
    summary = client.get(f"/api/v1/accounts/{account}/data-summary", headers=headers).json()
    assert summary["transaction_count"] == 158 and summary["fictitious"] is True
    found = client.get(f"/api/v1/accounts/{account}/recurrences", headers=headers).json()
    assert {row["description"] for row in found} == {
        "salário fictício",
        "aluguel fictício",
        "assinatura fictícia",
    }
    assert all(row["next_date"] > "2026-10-23" for row in found)
