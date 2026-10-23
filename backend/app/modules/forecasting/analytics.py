"""Observed values are bounded by the persisted scenario clock, never forecast dates."""

import hashlib
from datetime import date
from decimal import Decimal
from uuid import uuid4

from sqlalchemy import select

from app.core.errors import AppError
from app.modules.banking.repositories import BankingRepository
from app.modules.forecasting.engine import project
from app.modules.forecasting.models import ForecastRun
from app.modules.forecasting.pipeline import aggregate, eligible
from app.modules.forecasting.recovery import latest_run
from app.modules.simulation.services import get_scenario


def dashboard(session, account_id, horizon=None):
    from app.modules.forecasting.router import Run, observations

    cutoff = get_scenario(session, account_id).current_date
    run = latest_run(session, account_id, horizon)
    rows = eligible(observations(session, account_id, cutoff), cutoff)
    digest = hashlib.sha256(repr(rows).encode()).hexdigest()
    stale = run is None or run.base_date != cutoff or run.dataset_version != digest
    payload = Run.model_validate(run.payload).model_dump(mode="json") if run else None
    return {
        "forecast": payload,
        "current_balance": format(BankingRepository(session).balance(account_id), ".2f"),
        "current_date": str(cutoff),
        "stale": stale,
        "future_balance": payload["points"][-1]["balance"] if payload else None,
        "income": format(sum((Decimal(p["income"]) for p in payload["points"]), Decimal(0)), ".2f")
        if payload
        else None,
        "risk": payload["risk"] if payload else None,
    }


def comparison(session, account_id, run_id):
    from app.modules.forecasting.router import observations

    run = session.scalar(
        select(ForecastRun).where(ForecastRun.id == run_id, ForecastRun.account_id == account_id)
    )
    if run is None:
        raise AppError(404, "FORECAST_NOT_FOUND", "Previsão não encontrada.")
    cutoff = get_scenario(session, account_id).current_date
    known = eligible(observations(session, account_id, cutoff), cutoff)
    start = min((r.occurred_on for r in known), default=cutoff)
    daily = aggregate(known, start, cutoff)
    balances, expenses = {}, {}
    running = Decimal("0.00")
    for day in daily:
        running += day.income - day.expense
        balances[day.day], expenses[day.day] = running, day.expense
    points = []
    actual = predicted = Decimal("0.00")
    for point in run.payload["points"]:
        day = date.fromisoformat(point["date"])
        observed = day <= cutoff
        expense = expenses.get(day, Decimal("0.00")) if observed else None
        if observed:
            actual += expense
            predicted += Decimal(point["expense"])
        points.append(
            {
                "date": str(day),
                "predicted_balance": point["balance"],
                "observed_balance": format(balances.get(day, Decimal(0)), ".2f")
                if observed
                else None,
                "predicted_expense": point["expense"],
                "observed_expense": format(expense, ".2f") if expense is not None else None,
            }
        )
    difference = actual - predicted
    current = dashboard(session, account_id)
    return {
        "base_date": str(run.base_date),
        "current_date": str(cutoff),
        "points": points,
        "deviation": {
            "actual_expense": format(actual, ".2f"),
            "predicted_expense": format(predicted, ".2f"),
            "amount": format(difference, ".2f"),
            "percent": format(difference / predicted * 100, ".2f") if predicted else None,
            "alert_eligible": bool(current["risk"]) and not current["stale"],
            "risk_date": current["risk"]["date"] if current["risk"] else None,
        },
    }


def simulate_expense(session, account_id, amount, horizon):
    from app.modules.forecasting.router import Run, observations

    debit = Decimal(amount)
    if debit <= 0:
        raise AppError(422, "INVALID_AMOUNT", "Informe um gasto hipotético positivo.")
    cutoff = get_scenario(session, account_id).current_date
    before = Run(id=uuid4(), **project(observations(session, account_id, cutoff), cutoff, horizon))
    after = before.model_copy(deep=True)
    after.id = uuid4()
    for point in after.points:
        point.balance -= debit
    after.points[0].expense += debit
    after.points[0].variable_expense += debit
    from app.modules.forecasting.router import Risk

    after.risk = next(
        (Risk(date=p.date, balance=p.balance) for p in after.points if p.balance < 0), None
    )
    return {
        "before": before.model_dump(mode="json"),
        "after": after.model_dump(mode="json"),
        "amount": amount,
        "hypothetical": True,
        "persisted": False,
    }
