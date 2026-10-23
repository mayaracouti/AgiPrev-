from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID, uuid4

from fastapi import APIRouter
from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.errors import AppError
from app.modules.auth.dependencies import CurrentCustomer, Database
from app.modules.banking.models import LedgerEntry
from app.modules.banking.transaction_router import owned_locked
from app.modules.forecasting.engine import project
from app.modules.forecasting.models import ForecastPoint, ForecastRun
from app.modules.forecasting.pipeline import Observation, aggregate
from app.modules.simulation.services import get_scenario

router = APIRouter(prefix="/accounts/{account_id}", tags=["forecasting"])


class ForecastInput(BaseModel):
    horizon: Literal[7, 15, 30] = 7
    method: Literal["hybrid", "constant", "moving_average", "seasonal"] = "hybrid"


class Point(BaseModel):
    date: date
    income: Decimal
    fixed_expense: Decimal
    variable_expense: Decimal
    expense: Decimal
    balance: Decimal
    events: list[dict]


class Risk(BaseModel):
    date: date
    balance: Decimal


class Run(BaseModel):
    created_at: datetime = Field(default_factory=lambda: datetime.now(UTC))
    id: UUID
    base_date: date
    horizon: Literal[7, 15, 30]
    method: str
    model_version: str
    dataset_version: str
    seed: int
    points: list[Point]
    risk: Risk | None
    estimate_notice: str


def observations(session, account_id, cutoff):
    # The simulator posts only realized entries. Creation time is not economic availability:
    # historical synthetic imports are explicitly available on their economic date.
    return [
        Observation(
            r.reference,
            r.occurred_on,
            r.available_on or r.occurred_on,
            r.direction,
            r.amount,
            r.description,
            r.reversal_of,
        )
        for r in session.scalars(
            select(LedgerEntry)
            .where(LedgerEntry.account_id == account_id, LedgerEntry.occurred_on <= cutoff)
            .order_by(LedgerEntry.occurred_on, LedgerEntry.reference)
        )
    ]


@router.get("/daily-series")
def daily_series(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    cutoff = get_scenario(session, account_id).current_date
    rows = observations(session, account_id, cutoff)
    start = min((r.occurred_on for r in rows), default=cutoff)
    try:
        result = [
            {
                "date": r.day,
                "income": format(r.income, ".2f"),
                "expense": format(r.expense, ".2f"),
                "references": r.references,
            }
            for r in aggregate(rows, start, cutoff)
        ]
    except ValueError as exc:
        raise AppError(
            422, "INVALID_FORECAST_HISTORY", "Histórico inconsistente para agregação."
        ) from exc
    session.commit()
    return {"base_date": cutoff, "series": result}


@router.post("/forecasts", response_model=Run)
def create_forecast(
    account_id: UUID, body: ForecastInput, session: Database, customer: CurrentCustomer
):
    owned_locked(session, account_id, customer.id)
    cutoff = get_scenario(session, account_id).current_date
    try:
        result = project(
            observations(session, account_id, cutoff), cutoff, body.horizon, body.method
        )
    except ValueError as exc:
        raise AppError(
            422, "INVALID_FORECAST_HISTORY", "Histórico inconsistente para previsão."
        ) from exc
    run_id = uuid4()
    response = Run(id=run_id, **result)
    run = ForecastRun(
        id=run_id,
        created_at=response.created_at,
        account_id=account_id,
        base_date=cutoff,
        horizon=body.horizon,
        method=body.method,
        model_version=result["model_version"],
        dataset_version=result["dataset_version"],
        seed=42,
        payload=response.model_dump(mode="json"),
    )
    session.add(run)
    session.flush()
    session.add_all(
        [
            ForecastPoint(
                run_id=run.id, day=p.date, income=p.income, expense=p.expense, balance=p.balance
            )
            for p in response.points
        ]
    )
    session.commit()
    return response


@router.get("/forecasts", response_model=list[Run])
def list_forecasts(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    return [
        Run.model_validate(r.payload)
        for r in session.scalars(
            select(ForecastRun)
            .where(ForecastRun.account_id == account_id)
            .order_by(ForecastRun.created_at.desc())
            .limit(100)
        )
    ]


@router.get("/forecasts/{run_id}", response_model=Run)
def get_forecast(account_id: UUID, run_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    row = session.scalar(
        select(ForecastRun).where(ForecastRun.id == run_id, ForecastRun.account_id == account_id)
    )
    if row is None:
        raise AppError(404, "FORECAST_NOT_FOUND", "Previsão não encontrada.")
    return Run.model_validate(row.payload)
