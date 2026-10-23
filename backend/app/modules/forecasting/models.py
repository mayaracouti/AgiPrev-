from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import JSON, Date, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IdentityMixin
from app.db.types import MONEY


class ForecastRun(IdentityMixin, Base):
    __tablename__ = "forecast_runs"
    account_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("accounts.id"), index=True)
    base_date: Mapped[date] = mapped_column(Date)
    horizon: Mapped[int]
    method: Mapped[str] = mapped_column(String(24))
    model_version: Mapped[str] = mapped_column(String(80))
    dataset_version: Mapped[str] = mapped_column(String(64))
    seed: Mapped[int]
    payload: Mapped[dict] = mapped_column(JSON)


class ForecastPoint(IdentityMixin, Base):
    __tablename__ = "forecast_points"
    run_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("forecast_runs.id"), index=True)
    day: Mapped[date] = mapped_column(Date)
    income: Mapped[Decimal] = mapped_column(MONEY)
    expense: Mapped[Decimal] = mapped_column(MONEY)
    balance: Mapped[Decimal] = mapped_column(MONEY)
    __table_args__ = (UniqueConstraint("run_id", "day"),)
