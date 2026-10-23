from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Literal
from uuid import UUID

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select

from app.core.errors import AppError
from app.modules.auth.dependencies import CurrentCustomer, Database
from app.modules.banking.transactions import owned_locked
from app.modules.notifications.models import Alert, AlertRule

router = APIRouter(prefix="/accounts/{account_id}", tags=["alerts"])


class AlertView(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    account_id: UUID
    run_id: UUID
    severity: str
    title: str
    message: str
    risk_date: date
    deficit: Decimal
    recommendation: str
    read_at: datetime | None
    created_at: datetime


class RuleInput(BaseModel):
    enabled: bool = True
    critical_days: int = Field(default=3, ge=0, le=30)


class ReadInput(BaseModel):
    read: Literal[True]


@router.get("/alert-rules", response_model=RuleInput)
def rules(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    rule = session.get(AlertRule, account_id)
    return (
        RuleInput(enabled=rule.enabled, critical_days=rule.critical_days) if rule else RuleInput()
    )


@router.put("/alert-rules", response_model=RuleInput)
def set_rules(account_id: UUID, body: RuleInput, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    rule = session.get(AlertRule, account_id)
    if rule is None:
        rule = AlertRule(account_id=account_id, **body.model_dump())
        session.add(rule)
    else:
        rule.enabled, rule.critical_days = body.enabled, body.critical_days
    session.commit()
    return body


@router.get("/alerts", response_model=list[AlertView])
def alerts(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    return list(
        session.scalars(
            select(Alert)
            .where(Alert.account_id == account_id)
            .order_by(Alert.created_at.desc())
            .limit(100)
        )
    )


def find_alert(session, account_id, alert_id):
    alert = session.scalar(
        select(Alert).where(Alert.id == alert_id, Alert.account_id == account_id)
    )
    if alert is None:
        raise AppError(404, "ALERT_NOT_FOUND", "Alerta não encontrado.")
    return alert


@router.get("/alerts/{alert_id}", response_model=AlertView)
def detail(account_id: UUID, alert_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    return find_alert(session, account_id, alert_id)


@router.patch("/alerts/{alert_id}", response_model=AlertView)
def read(
    account_id: UUID, alert_id: UUID, body: ReadInput, session: Database, customer: CurrentCustomer
):
    owned_locked(session, account_id, customer.id)
    alert = find_alert(session, account_id, alert_id)
    alert.read_at = alert.read_at or datetime.now(UTC)
    result = AlertView.model_validate(alert)
    session.commit()
    return result
