"""Bank commits first; durable refresh events survive forecasting failures."""

from uuid import uuid4

from sqlalchemy import select

from app.core.telemetry import correlation, event
from app.modules.banking.models import Account
from app.modules.forecasting.models import ForecastRun
from app.modules.notifications.models import ForecastRefresh


def latest_run(session, account_id, horizon=None):
    query = select(ForecastRun).where(ForecastRun.account_id == account_id)
    if horizon is not None:
        query = query.where(ForecastRun.horizon == horizon)
    return session.scalar(
        query.order_by(ForecastRun.created_at.desc(), ForecastRun.id.desc()).limit(1)
    )


def queue_refresh(session, transaction):
    old = latest_run(session, transaction.account_id)
    record = ForecastRefresh(
        account_id=transaction.account_id,
        transaction_id=transaction.id,
        status="pending",
        attempts=0,
        previous_forecast_id=old.id if old else None,
        correlation_id=correlation.get() or str(uuid4()),
    )
    session.add(record)
    session.flush()
    return record


def recover_refresh(session, refresh_id):
    from app.modules.forecasting.router import persist_forecast
    from app.modules.simulation.services import get_scenario

    record = session.get(ForecastRefresh, refresh_id)
    account_id, trace = record.account_id, record.correlation_id
    session.scalar(select(Account).where(Account.id == account_id).with_for_update())
    session.refresh(record)
    if record.status == "ready":
        return record
    record.attempts += 1
    try:
        cutoff = get_scenario(session, account_id).current_date
        response = persist_forecast(session, account_id, cutoff, 30, "hybrid")
        record.forecast_id, record.status, record.error_code = response.id, "ready", None
        session.commit()
        event("forecast_refresh_ready", refresh_id=str(refresh_id), trace=trace)
    except Exception as exc:
        session.rollback()
        record = session.get(ForecastRefresh, refresh_id)
        record.attempts += 1
        record.status, record.error_code = "failed", "FORECAST_FAILED"
        session.commit()
        event(
            "forecast_refresh_failed",
            refresh_id=str(refresh_id),
            trace=trace,
            error_type=type(exc).__name__,
        )
    return record
