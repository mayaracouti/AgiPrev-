from datetime import date
from decimal import Decimal
from uuid import UUID

from sqlalchemy import CheckConstraint, Date, ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.db.mixins import IdentityMixin
from app.db.types import MONEY


class Customer(IdentityMixin, Base):
    __tablename__ = "customers"
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(160), unique=True)
    demo_profile: Mapped[str] = mapped_column(String(24), unique=True)
    password_hash: Mapped[str] = mapped_column(String(256))


class Account(IdentityMixin, Base):
    __tablename__ = "accounts"
    customer_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("customers.id", ondelete="CASCADE"), unique=True
    )
    currency: Mapped[str] = mapped_column(String(3), default="BRL", server_default="BRL")
    __table_args__ = (CheckConstraint("currency = 'BRL'", name="currency_brl"),)


class LedgerEntry(IdentityMixin, Base):
    __tablename__ = "ledger_entries"
    account_id: Mapped[UUID] = mapped_column(
        Uuid, ForeignKey("accounts.id", ondelete="CASCADE"), index=True
    )
    direction: Mapped[str] = mapped_column(String(6))
    amount: Mapped[Decimal] = mapped_column(MONEY)
    description: Mapped[str] = mapped_column(String(120))
    occurred_on: Mapped[date] = mapped_column(Date)
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("direction IN ('credit', 'debit')", name="direction_valid"),
    )
