from decimal import Decimal

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_transactions_simulation import auth_context, payload

pytestmark = pytest.mark.integration


def test_forecast_api_versions_auth_validation_money_and_immutability(pg_client):
    client, session = pg_client
    account, headers = auth_context(client)
    base = f"/api/v1/accounts/{account}"
    assert client.post(base + "/forecasts", json={}).status_code == 401
    assert client.post(base + "/forecasts", json={"horizon": 8}, headers=headers).status_code == 422
    series = client.get(base + "/daily-series", headers=headers)
    assert series.status_code == 200 and series.json()["series"][0]["income"] == "2947.53"
    snapshots = []
    for horizon in (7, 15, 30):
        response = client.post(base + "/forecasts", json={"horizon": horizon}, headers=headers)
        assert response.status_code == 200, response.text
        run = response.json()
        assert len(run["points"]) == horizon and run["base_date"] == "2026-10-23"
        assert run["model_version"] and run["dataset_version"]
        assert run["points"][0]["balance"] == "2947.53"
        snapshots.append(run)
    credit = client.post(base + "/credits", json=payload("1.01"), headers=headers)
    credit.raise_for_status()
    assert credit.json()["forecast_status"] == "ready"
    automatic_id = credit.json()["forecast_id"]
    new = client.post(base + "/forecasts", json={}, headers=headers).json()
    assert new["points"][0]["balance"] == "2948.54"
    old = client.get(base + "/forecasts/" + snapshots[0]["id"], headers=headers)
    assert old.json() == snapshots[0]
    versions = client.get(base + "/forecasts", headers=headers).json()
    assert len(versions) == 5  # Three originals, one automatic after credit, one manual.
    assert automatic_id in {run["id"] for run in versions}
    assert automatic_id != new["id"]
    other, other_headers = auth_context(client, "rafael@demo.local")
    assert client.get(base + "/forecasts", headers=other_headers).status_code == 404
    assert (
        client.get(
            f"/api/v1/accounts/{other}/forecasts/{new['id']}", headers=other_headers
        ).status_code
        == 404
    )
    assert session.scalar(text("SELECT balance FROM forecast_points LIMIT 1")) == Decimal("2947.53")
    session.rollback()
    for table in ("forecast_runs", "forecast_points"):
        for action in ("UPDATE", "DELETE"):
            with pytest.raises(DBAPIError), session.begin():
                statement = (
                    f"UPDATE {table} SET seed=1"
                    if table == "forecast_runs"
                    else f"UPDATE {table} SET balance=0"
                )
                session.execute(text(statement if action == "UPDATE" else f"DELETE FROM {table}"))


def test_persisted_series_late_availability_reversals_and_trained_forecast(pg_client):
    from datetime import date
    from uuid import UUID

    from app.modules.banking.models import LedgerEntry
    from app.modules.simulation.generator import financial_rows

    client, session = pg_client
    account, headers = auth_context(client)
    for entry in financial_rows(42, 0):
        session.add(LedgerEntry(**{**entry, "account_id": UUID(account)}))
    session.add(
        LedgerEntry(
            account_id=UUID(account),
            reference="late-import",
            occurred_on=date(2026, 10, 20),
            available_on=date(2026, 11, 1),
            direction="credit",
            amount=Decimal("999999"),
            description="Late",
        )
    )
    session.add(
        LedgerEntry(
            account_id=UUID(account),
            reference="reverse-opening",
            occurred_on=date(2026, 10, 23),
            reversal_of="opening-regular",
            direction="debit",
            amount=Decimal("2947.53"),
            description="Estorno",
        )
    )
    session.commit()
    base = f"/api/v1/accounts/{account}"
    response = client.get(base + "/daily-series", headers=headers)
    assert response.status_code == 200, response.text
    assert not any("late-import" in p["references"] for p in response.json()["series"])
    assert response.json()["series"][-1]["income"] == "0.00"
    forecast = client.post(base + "/forecasts", json={"horizon": 30}, headers=headers)
    assert forecast.status_code == 200, forecast.text
    assert forecast.json()["model_version"].startswith("boosted-stumps-v2:")
    assert all(Decimal(p["variable_expense"]) >= 0 for p in forecast.json()["points"])


def test_inconsistent_reversal_returns_controlled_error(pg_client):
    from datetime import date
    from uuid import UUID

    from app.modules.banking.models import LedgerEntry

    client, session = pg_client
    account, headers = auth_context(client)
    session.add(
        LedgerEntry(
            account_id=UUID(account),
            reference="invalid-reversal",
            occurred_on=date(2026, 10, 23),
            reversal_of="opening-regular",
            direction="debit",
            amount=Decimal("1.00"),
            description="Invalid",
        )
    )
    session.commit()
    base = f"/api/v1/accounts/{account}"
    assert client.post(base + "/forecasts", json={}, headers=headers).status_code == 422
    assert client.get(base + "/daily-series", headers=headers).status_code == 422
