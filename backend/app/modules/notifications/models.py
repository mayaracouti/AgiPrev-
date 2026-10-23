from datetime import date, datetime
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, DateTime, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IdentityMixin
from app.db.types import MONEY


class AlertRule(Base):
    __tablename__ = "alert_rules"
    account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("accounts.id"), primary_key=True)
    enabled: Mapped[bool] = mapped_column(default=True)
    critical_days: Mapped[int] = mapped_column(default=3)


class Alert(IdentityMixin, Base):
    __tablename__ = "alerts"
    account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("accounts.id"), index=True)
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("forecast_runs.id"))
    risk_date: Mapped[date] = mapped_column(Date)
    deficit: Mapped[Decimal] = mapped_column(MONEY)
    severity: Mapped[str] = mapped_column(String(16))
    title: Mapped[str] = mapped_column(String(120))
    message: Mapped[str] = mapped_column(String(600))
    recommendation: Mapped[str] = mapped_column(String(600))
    read_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    __table_args__ = (UniqueConstraint("account_id", "risk_date"),)


class ForecastRefresh(IdentityMixin, Base):
    __tablename__ = "forecast_refreshes"
    account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("accounts.id"), index=True)
    transaction_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("ledger_entries.id"), unique=True)
    status: Mapped[str] = mapped_column(String(16), default="pending")
    attempts: Mapped[int] = mapped_column(default=0)
    correlation_id: Mapped[str] = mapped_column(String(64))
    previous_forecast_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("forecast_runs.id"))
    forecast_id: Mapped[UUID | None] = mapped_column(Uuid, ForeignKey("forecast_runs.id"))
    error_code: Mapped[str | None] = mapped_column(String(40))
