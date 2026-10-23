from decimal import Decimal
from uuid import UUID

from sqlalchemy import case, func, select
from sqlalchemy.orm import Session

from app.modules.banking.models import Account, Customer, LedgerEntry


class BankingRepository:
    def __init__(self, session: Session) -> None:
        self.session = session

    def customers(self) -> list[Customer]:
        return list(self.session.scalars(select(Customer).order_by(Customer.name)))

    def accounts(self, customer_id: UUID) -> list[Account]:
        return list(self.session.scalars(select(Account).where(Account.customer_id == customer_id)))

    def account(self, account_id: UUID, customer_id: UUID) -> Account | None:
        return self.session.scalar(
            select(Account).where(Account.id == account_id, Account.customer_id == customer_id)
        )

    def balance(self, account_id: UUID) -> Decimal:
        signed = case(
            (LedgerEntry.direction == "credit", LedgerEntry.amount), else_=-LedgerEntry.amount
        )
        value = self.session.scalar(
            select(func.coalesce(func.sum(signed), 0)).where(LedgerEntry.account_id == account_id)
        )
        return Decimal(value).quantize(Decimal("0.01"))

    def ledger(self, account_id: UUID, limit: int, offset: int) -> list[LedgerEntry]:
        return list(
            self.session.scalars(
                select(LedgerEntry)
                .where(LedgerEntry.account_id == account_id)
                .order_by(LedgerEntry.occurred_on.desc(), LedgerEntry.id)
                .limit(limit)
                .offset(offset)
            )
        )
