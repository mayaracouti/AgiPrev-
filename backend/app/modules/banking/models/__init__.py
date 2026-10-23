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
    demo_profile: Mapped[str] = mapped_column(String(24), index=True)
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
    category_id: Mapped[str] = mapped_column(
        String(24), ForeignKey("categories.id"), default="other", server_default="other"
    )
    kind: Mapped[str] = mapped_column(String(16), default="transfer", server_default="transfer")
    recipient: Mapped[str | None] = mapped_column(String(120))
    request_hash: Mapped[str | None] = mapped_column(String(64))
    available_on: Mapped[date | None] = mapped_column(Date)
    reversal_of: Mapped[str | None] = mapped_column(
        String(100), ForeignKey("ledger_entries.reference")
    )
    reference: Mapped[str] = mapped_column(String(100), unique=True)
    __table_args__ = (
        CheckConstraint("amount > 0", name="amount_positive"),
        CheckConstraint("direction IN ('credit', 'debit')", name="direction_valid"),
    )


class Category(Base):
    __tablename__ = "categories"
    id: Mapped[str] = mapped_column(String(24), primary_key=True)
    name: Mapped[str] = mapped_column(String(60))


# A transaction is a confirmed ledger entry, not a second source of monetary truth.
Transaction = LedgerEntry
