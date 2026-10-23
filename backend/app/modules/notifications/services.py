from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.modules.notifications.models import Alert, AlertRule


def recommendation(risk_date: date, deficit: Decimal, base_date: date) -> str:
    days = max(0, (risk_date - base_date).days)
    return (
        f"Até {risk_date.isoformat()} ({days} dias), revise despesas e datas de recebimento "
        f"para uma insuficiência estimada de R$ {deficit:.2f}. "
        "Considere adiar gastos não essenciais. É uma estimativa, sem garantia de resultado."
    )


def emit_alert(session: Session, account_id: UUID, run) -> Alert | None:
    risk = run.payload.get("risk")
    rules = session.get(AlertRule, account_id)
    if not risk or (rules and not rules.enabled):
        return None
    risk_date = date.fromisoformat(risk["date"])
    existing = session.scalar(
        select(Alert).where(Alert.account_id == account_id, Alert.risk_date == risk_date)
    )
    if existing:
        return existing
    deficit = abs(Decimal(risk["balance"]))
    critical_days = rules.critical_days if rules else 3
    severity = "critical" if (risk_date - run.base_date).days <= critical_days else "warning"
    alert = Alert(
        account_id=account_id,
        run_id=run.id,
        risk_date=risk_date,
        deficit=deficit,
        severity=severity,
        title="Possível saldo insuficiente",
        message=f"Saldo estimado negativo em {risk_date}: R$ {-deficit:.2f}. "
        f"Previsão {run.id}, base {run.base_date}, {run.horizon} dias. "
        "Gasto acima da média, isoladamente, não gera este alerta.",
        recommendation=recommendation(risk_date, deficit, run.base_date),
    )
    session.add(alert)
    session.flush()
    return alert
