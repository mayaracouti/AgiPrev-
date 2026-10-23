from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import Date, ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IdentityMixin
from app.db.types import MONEY


class Scenario(IdentityMixin, Base):
    __tablename__ = "scenarios"
    account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="CASCADE"), unique=True
    )
    current_date: Mapped[date] = mapped_column(Date, default=date(2026, 10, 23))
    seed: Mapped[int] = mapped_column(default=42)
    version: Mapped[str] = mapped_column(String(24), default="synthetic-v1")


class ScheduledEvent(IdentityMixin, Base):
    __tablename__ = "scheduled_events"
    scenario_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("scenarios.id", ondelete="CASCADE"), index=True
    )
    scheduled_on: Mapped[date] = mapped_column(Date)
    original_date: Mapped[date] = mapped_column(Date)
    direction: Mapped[str] = mapped_column(String(6))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    category_id: Mapped[str] = mapped_column(String(24), ForeignKey("categories.id"))
    description: Mapped[str] = mapped_column(String(120))
    kind: Mapped[str] = mapped_column(String(24))
    processed: Mapped[bool] = mapped_column(default=False)


class ScenarioAction(IdentityMixin, Base):
    __tablename__ = "scenario_actions"
    scenario_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("scenarios.id", ondelete="CASCADE"))
    key: Mapped[str] = mapped_column(String(80))
    request_hash: Mapped[str] = mapped_column(String(64))
    event_id: Mapped[UUID] = mapped_column(Uuid, ForeignKey("scheduled_events.id"))
    __table_args__ = (UniqueConstraint("scenario_id", "key"),)
