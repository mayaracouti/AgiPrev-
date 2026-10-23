from datetime import date
from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import func, select
from test_transactions_simulation import auth_context, payload

from app.modules.banking.models import LedgerEntry
from app.modules.forecasting.models import ForecastRun
from app.modules.notifications.models import Alert, ForecastRefresh

pytestmark = pytest.mark.integration


def seed_fixed(session, account):
    for month in (7, 8, 9):
        session.add(
            LedgerEntry(
                account_id=UUID(account),
                direction="debit",
                amount=Decimal("300"),
                occurred_on=date(2026, month, 8),
                category_id="housing",
                description="Aluguel fictício",
                reference=f"{account}:rent:{month}",
            )
        )
    session.commit()


def test_pix_forecast_alert_dedup_authorization_and_read(pg_client):
    client, session = pg_client
    account, headers = auth_context(client)
    seed_fixed(session, account)
    base = f"/api/v1/accounts/{account}"
    original = client.post(base + "/forecasts", json={"horizon": 30}, headers=headers)
    assert original.status_code == 200, original.text
    before = original.json()
    assert before["risk"] is None
    pix = payload("2000.00", account_id=account, recipient="loja@demo.local")
    first = client.post("/api/v1/pix/simulate", json=pix, headers=headers)
    assert first.status_code == 200, first.text
    receipt = first.json()
    assert receipt["forecast_status"] == "ready"
    assert receipt["previous_forecast_id"] == before["id"]
    assert receipt["forecast_id"] != before["id"]
    assert receipt["balance"] == "47.53" and receipt["correlation_id"]
    duplicate = client.post("/api/v1/pix/simulate", json=pix, headers=headers)
    assert duplicate.json() == receipt
    assert client.get(base + "/forecasts/" + before["id"], headers=headers).json() == before
    latest = client.get(base + "/forecasts/latest", headers=headers).json()
    assert latest["forecast"]["id"] == receipt["forecast_id"]
    assert latest["current_balance"] == "47.53" and latest["risk"] is not None
    assert latest["stale"] is False
    alerts = client.get(base + "/alerts", headers=headers).json()
    assert len(alerts) == 1
    assert "estimativa" in alerts[0]["recommendation"]
    assert "crédito" not in alerts[0]["recommendation"]
    client.post(base + "/forecasts", json={"horizon": 30}, headers=headers).raise_for_status()
    assert len(client.get(base + "/alerts", headers=headers).json()) == 1
    alert_id = alerts[0]["id"]
    assert client.get(base + "/alerts/" + alert_id, headers=headers).json()["read_at"] is None
    read = client.patch(base + "/alerts/" + alert_id, json={"read": True}, headers=headers)
    assert read.status_code == 200 and read.json()["read_at"] is not None
    assert (
        client.patch(base + "/alerts/" + alert_id, json={"read": True}, headers=headers).json()
        == read.json()
    )
    other, other_headers = auth_context(client, "rafael@demo.local")
    assert client.get(base + "/alerts", headers=other_headers).status_code == 404
    assert (
        client.get(f"/api/v1/accounts/{other}/alerts/{alert_id}", headers=other_headers).status_code
        == 404
    )
    assert (
        client.patch(
            base + "/alerts/" + alert_id, json={"read": True}, headers=other_headers
        ).status_code
        == 404
    )
    assert session.scalar(select(func.count()).select_from(ForecastRefresh)) == 1


def test_series_deviation_and_hypothesis_never_change_money(pg_client):
    client, session = pg_client
    account, headers = auth_context(client)
    base = f"/api/v1/accounts/{account}"
    run = client.post(base + "/forecasts", json={"horizon": 7}, headers=headers).json()
    future = client.get(base + "/forecasts/" + run["id"] + "/series", headers=headers).json()
    assert all(
        p["observed_balance"] is None and p["observed_expense"] is None for p in future["points"]
    )
    assert future["deviation"]["percent"] is None
    before_balance = client.get(base + "/balance", headers=headers).json()
    before_ledger = session.scalar(select(func.count()).select_from(LedgerEntry))
    before_runs = session.scalar(select(func.count()).select_from(ForecastRun))
    simulation = client.post(
        base + "/forecasts/simulate", json={"amount": "3000.01", "horizon": 7}, headers=headers
    )
    assert simulation.status_code == 200, simulation.text
    body = simulation.json()
    for original, altered in zip(body["before"]["points"], body["after"]["points"], strict=True):
        assert Decimal(original["balance"]) - Decimal(altered["balance"]) == Decimal("3000.01")
    assert body["after"]["risk"] is not None
    assert client.get(base + "/balance", headers=headers).json() == before_balance
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == before_ledger
    assert session.scalar(select(func.count()).select_from(ForecastRun)) == before_runs
    for value in ("0.00", "-1.00", "NaN", "1.001"):
        assert (
            client.post(
                base + "/forecasts/simulate", json={"amount": value}, headers=headers
            ).status_code
            == 422
        )
    advance = client.post(
        base + "/scenario/advance", json={"target_date": "2026-10-25"}, headers=headers
    )
    assert advance.status_code == 200
    # Expenditure above a zero baseline but no future deficit must not create an alert.
    session.add(
        LedgerEntry(
            account_id=UUID(account),
            direction="debit",
            amount=Decimal("1.00"),
            occurred_on=date(2026, 10, 24),
            description="Despesa extra",
            reference="deviation-extra",
            category_id="other",
        )
    )
    session.commit()
    client.post(base + "/forecasts", json={"horizon": 7}, headers=headers).raise_for_status()
    result = client.get(base + "/forecasts/" + run["id"] + "/series", headers=headers).json()
    assert result["deviation"]["amount"] == "1.00"
    assert result["deviation"]["percent"] is None and result["deviation"]["alert_eligible"] is False
    assert all(p["observed_balance"] is None for p in result["points"] if p["date"] > "2026-10-25")
    assert client.get(base + "/alerts", headers=headers).json() == []


def test_model_failure_preserves_bank_commit_and_can_recover(pg_client, monkeypatch):
    import app.modules.forecasting.router as forecasting

    client, session = pg_client
    account, headers = auth_context(client)
    base = f"/api/v1/accounts/{account}"
    client.post(base + "/forecasts", json={}, headers=headers).raise_for_status()
    original = forecasting.project

    def fail(*args, **kwargs):
        raise RuntimeError("injected ML failure")

    monkeypatch.setattr(forecasting, "project", fail)
    response = client.post(base + "/credits", json=payload("10.00"), headers=headers)
    assert response.status_code == 200, response.text
    assert response.json()["balance"] == "2957.53"
    assert response.json()["forecast_status"] == "failed"
    assert response.headers["X-Correlation-ID"] == response.headers["X-Request-ID"]
    refresh = session.scalar(select(ForecastRefresh))
    assert refresh.status == "failed" and refresh.error_code == "FORECAST_FAILED"
    assert client.get(base + "/forecasts/latest", headers=headers).json()["stale"] is True
    monkeypatch.setattr(forecasting, "project", original)
    retry = client.post(base + "/forecast-refreshes/retry", headers=headers)
    assert retry.status_code == 200 and retry.json()[0]["status"] == "ready"
    assert client.get(base + "/forecasts/latest", headers=headers).json()["stale"] is False
    assert client.get(base + "/balance", headers=headers).json()["balance"] == "2957.53"
    assert (
        client.get("/api/v1/observability", headers=headers).json()["counters"][
            "forecast_refresh_failed"
        ]
        >= 1
    )


def test_configurable_alert_rules(pg_client):
    client, session = pg_client
    account, headers = auth_context(client)
    base = f"/api/v1/accounts/{account}"
    seed_fixed(session, account)
    assert (
        client.put(
            base + "/alert-rules", json={"enabled": False, "critical_days": 1}, headers=headers
        ).status_code
        == 200
    )
    client.post(
        "/api/v1/pix/simulate",
        json=payload("2000.00", account_id=account, recipient="demo"),
        headers=headers,
    ).raise_for_status()
    assert session.scalar(select(func.count()).select_from(Alert)) == 0
    assert client.get(base + "/alert-rules", headers=headers).json()["enabled"] is False
    assert (
        client.put(
            base + "/alert-rules", json={"enabled": True, "critical_days": 31}, headers=headers
        ).status_code
        == 422
    )
    client.put(
        base + "/alert-rules", json={"enabled": True, "critical_days": 30}, headers=headers
    ).raise_for_status()
    client.post(base + "/forecasts", json={"horizon": 30}, headers=headers).raise_for_status()
    assert client.get(base + "/alerts", headers=headers).json()[0]["severity"] == "critical"


def test_demo_preparation_is_repeatable_and_has_calculated_risk(pg_client):
    from app.demo import prepare_demo

    _, session = pg_client
    first = prepare_demo(session, 4241, "demo-test-only-2026")
    assert first["dashboard"]["current_balance"] == "50.00"
    assert first["dashboard"]["risk"] is not None
    count = session.scalar(select(func.count()).select_from(LedgerEntry))
    repeated = prepare_demo(session, 4241, "demo-test-only-2026")
    assert repeated["reused"] is True
    assert repeated["dashboard"]["forecast"]["id"] == first["dashboard"]["forecast"]["id"]
    assert session.scalar(select(func.count()).select_from(LedgerEntry)) == count
