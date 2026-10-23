from datetime import date, timedelta
from decimal import Decimal
from typing import Literal
from uuid import NAMESPACE_URL, UUID, uuid5

from pydantic import BaseModel, Field
from sqlalchemy import select

from app.core.errors import AppError
from app.modules.banking.models import LedgerEntry
from app.modules.banking.repositories import BankingRepository
from app.modules.banking.transactions import Amount, category_exists, fingerprint, owned_locked
from app.modules.simulation.models import Scenario, ScenarioAction, ScheduledEvent


class AdvanceInput(BaseModel):
    target_date: date


class EventInput(BaseModel):
    kind: Literal["salary_delay", "extra_purchase", "extra_income"]
    scheduled_on: date
    amount: Amount = "100.00"
    delay_days: int = Field(default=5, ge=1, le=60)
    idempotency_key: UUID


def get_scenario(session, account_id):
    scenario = session.scalar(select(Scenario).where(Scenario.account_id == account_id))
    if scenario is None:
        scenario = Scenario(account_id=account_id, current_date=date(2026, 10, 23), seed=42)
        session.add(scenario)
        session.flush()
        from app.modules.simulation.generator import future_rows

        session.add_all([ScheduledEvent(**row) for row in future_rows(42, 0, scenario.id)])
        session.flush()
    return scenario


def scenario_view(session, scenario):
    events = session.scalars(
        select(ScheduledEvent)
        .where(ScheduledEvent.scenario_id == scenario.id, ScheduledEvent.processed.is_(False))
        .order_by(ScheduledEvent.scheduled_on, ScheduledEvent.id)
    )
    balance = BankingRepository(session).balance(scenario.account_id)
    running = balance
    pending = []
    for event in events:
        running += event.amount if event.direction == "credit" else -event.amount
        pending.append(
            {
                "id": str(event.id),
                "date": str(event.scheduled_on),
                "kind": event.kind,
                "amount": format(event.amount, ".2f"),
                "direction": event.direction,
                "description": event.description,
                "scheduled_balance": format(running, ".2f"),
            }
        )
    return {
        "id": str(scenario.id),
        "current_date": str(scenario.current_date),
        "seed": scenario.seed,
        "version": scenario.version,
        "balance": format(balance, ".2f"),
        "scheduled_final_balance": format(running, ".2f"),
        "pending_events": pending,
    }


def advance(session, customer_id, account_id, target):
    owned_locked(session, account_id, customer_id)
    scenario = get_scenario(session, account_id)
    if target < scenario.current_date or target > scenario.current_date + timedelta(days=366):
        raise AppError(422, "INVALID_DATE", "Avance de 0 a 366 dias, sem voltar no tempo.")
    events = list(
        session.scalars(
            select(ScheduledEvent)
            .where(
                ScheduledEvent.scenario_id == scenario.id,
                ScheduledEvent.processed.is_(False),
                ScheduledEvent.scheduled_on <= target,
            )
            .order_by(ScheduledEvent.scheduled_on, ScheduledEvent.id)
            .with_for_update()
        )
    )
    for event in events:
        session.add(
            LedgerEntry(
                id=uuid5(NAMESPACE_URL, f"event:{event.id}"),
                account_id=account_id,
                occurred_on=event.scheduled_on,
                direction=event.direction,
                amount=event.amount,
                category_id=event.category_id,
                description=event.description,
                kind="event",
                reference=f"event:{event.id}",
            )
        )
        event.processed = True
    scenario.current_date = target
    session.flush()
    result = scenario_view(session, scenario)
    session.commit()
    return {**result, "processed_count": len(events)}


def schedule_event(session, customer_id, account_id, body):
    owned_locked(session, account_id, customer_id)
    scenario = get_scenario(session, account_id)
    digest = fingerprint(body.model_dump(exclude={"idempotency_key"}))
    previous = session.scalar(
        select(ScenarioAction).where(
            ScenarioAction.scenario_id == scenario.id,
            ScenarioAction.key == str(body.idempotency_key),
        )
    )
    if previous:
        if previous.request_hash != digest:
            raise AppError(409, "IDEMPOTENCY_CONFLICT", "Chave já utilizada com outros dados.")
    else:
        if (
            not scenario.current_date
            < body.scheduled_on
            <= scenario.current_date + timedelta(days=366)
        ):
            raise AppError(422, "INVALID_DATE", "Escolha uma data futura dentro de 366 dias.")
        if body.kind == "salary_delay":
            event = session.scalar(
                select(ScheduledEvent)
                .where(
                    ScheduledEvent.scenario_id == scenario.id,
                    ScheduledEvent.kind == "salary",
                    ScheduledEvent.processed.is_(False),
                    ScheduledEvent.scheduled_on == body.scheduled_on,
                )
                .with_for_update()
            )
            if event is None:
                raise AppError(409, "NO_PENDING_SALARY", "Nenhum salário pendente nessa data.")
            event.scheduled_on += timedelta(days=body.delay_days)
        else:
            if Decimal(body.amount) <= 0:
                raise AppError(422, "INVALID_AMOUNT", "Informe um valor positivo.")
            category = "income" if body.kind == "extra_income" else "other"
            category_exists(session, category)
            event = ScheduledEvent(
                id=uuid5(NAMESPACE_URL, f"{scenario.id}:{body.idempotency_key}"),
                scenario_id=scenario.id,
                scheduled_on=body.scheduled_on,
                original_date=body.scheduled_on,
                direction="credit" if body.kind == "extra_income" else "debit",
                amount=Decimal(body.amount),
                category_id=category,
                kind=body.kind,
                description="Receita eventual fictícia"
                if body.kind == "extra_income"
                else "Compra extraordinária fictícia",
                processed=False,
            )
            session.add(event)
        session.flush()
        session.add(
            ScenarioAction(
                scenario_id=scenario.id,
                key=str(body.idempotency_key),
                request_hash=digest,
                event_id=event.id,
            )
        )
    result = scenario_view(session, scenario)
    session.commit()
    return result
