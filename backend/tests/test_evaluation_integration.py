from decimal import Decimal
from uuid import UUID

import pytest
from sqlalchemy import text
from sqlalchemy.exc import DBAPIError
from test_transactions_simulation import auth_context

pytestmark = pytest.mark.integration


def test_experiment_persistence_idempotency_exports_and_isolation(pg_client):
    from app.modules.banking.models import LedgerEntry
    from app.modules.simulation.generator import financial_rows

    client, session = pg_client
    account, headers = auth_context(client)
    for row in financial_rows(42, 0):
        session.add(LedgerEntry(**{**row, "account_id": UUID(account)}))
    session.commit()
    base = f"/api/v1/accounts/{account}"
    body = {"train_end": "2026-07-01", "validation_end": "2026-08-01", "final_end": "2026-09-01"}
    response = client.post(base + "/experiments", json=body, headers=headers)
    assert response.status_code == 200, response.text
    result = response.json()
    assert result["seed"] == 42 and result["model_artifact"]["trees"]
    assert client.post(base + "/experiments", json=body, headers=headers).json() == result
    assert session.scalar(text("SELECT count(*) FROM experiments")) == 1
    locked = client.post(
        base + "/experiments", json={**body, "train_end": "2026-06-30"}, headers=headers
    )
    assert locked.status_code == 409
    assert locked.json()["error"]["code"] == "FINAL_HOLDOUT_LOCKED"

    report = client.get(base + "/evaluation/reports?model=constant&horizon=7", headers=headers)
    assert len(report.json()["records"]) == 2
    assert all(Decimal(r["metrics"]["mae"]) >= 0 for r in report.json()["records"])
    assert "mae" in client.get(base + "/evaluation/reports?format=csv", headers=headers).text
    html_report = client.get(base + "/evaluation/reports?format=html", headers=headers).text
    assert "<svg" in html_report
    assert result["id"] in html_report and "evaluation-v1" in html_report
    for key in ("model", "horizon", "profile", "partition"):
        assert 'data-filter="' + key + '"' in html_report
    assert "row.hidden = filters.some" in html_report
    _, other_headers = auth_context(client, "rafael@demo.local")
    assert client.get(base + "/experiments", headers=other_headers).status_code == 404
    assert client.get(base + "/experiments").status_code == 401
    assert (
        client.post(
            base + "/experiments", json={**body, "final_end": "2030-01-01"}, headers=headers
        ).status_code
        == 422
    )
    session.rollback()
    with pytest.raises(DBAPIError), session.begin():
        session.execute(text("DELETE FROM experiments"))
