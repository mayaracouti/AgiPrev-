from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Query
from sqlalchemy import func, select

from app.modules.auth.dependencies import CurrentCustomer, Database
from app.modules.banking.models import Category, LedgerEntry
from app.modules.banking.repositories import BankingRepository
from app.modules.banking.services import BankingService
from app.modules.banking.transactions import (
    CategoryUpdate,
    Receipt,
    TransactionInput,
    TransactionPage,
    TransactionResponse,
    category_exists,
    history,
    owned_locked,
    post_transaction,
)
from app.modules.forecasting.recurrences import detect_recurrences
from app.modules.simulation.services import (
    AdvanceInput,
    EventInput,
    advance,
    get_scenario,
    scenario_view,
    schedule_event,
)

router = APIRouter(tags=["transactions and simulation"])


def owned(session, account_id, customer_id):
    return BankingService(BankingRepository(session)).owned_account(account_id, customer_id)


@router.get("/categories")
def categories(session: Database):
    return [
        {"id": c.id, "name": c.name}
        for c in session.scalars(select(Category).order_by(Category.name))
    ]


@router.get("/accounts/{account_id}/transactions", response_model=TransactionPage)
def transactions(
    account_id: UUID,
    session: Database,
    customer: CurrentCustomer,
    limit: Annotated[int, Query(ge=1, le=100)] = 25,
    cursor: Annotated[str | None, Query(max_length=512)] = None,
    date_from: date | None = None,
    date_to: date | None = None,
    category_id: Annotated[str | None, Query(max_length=24)] = None,
    direction: Literal["credit", "debit"] | None = None,
    search: Annotated[str | None, Query(max_length=120)] = None,
):
    owned(session, account_id, customer.id)
    return history(
        session, account_id, limit, cursor, date_from, date_to, category_id, direction, search
    )


@router.post("/accounts/{account_id}/credits", response_model=Receipt)
def credit(account_id: UUID, body: TransactionInput, session: Database, customer: CurrentCustomer):
    return post_transaction(session, customer.id, account_id, body, "income")


@router.post("/accounts/{account_id}/debits", response_model=Receipt)
def debit(account_id: UUID, body: TransactionInput, session: Database, customer: CurrentCustomer):
    return post_transaction(session, customer.id, account_id, body, "expense")


class PixInput(TransactionInput):
    account_id: UUID


@router.post("/pix/simulate", response_model=Receipt)
def pix(body: PixInput, session: Database, customer: CurrentCustomer):
    data = TransactionInput.model_validate(body.model_dump(exclude={"account_id"}))
    return post_transaction(session, customer.id, body.account_id, data, "pix")


@router.patch(
    "/accounts/{account_id}/transactions/{transaction_id}/category",
    response_model=TransactionResponse,
)
def update_category(
    account_id: UUID,
    transaction_id: UUID,
    body: CategoryUpdate,
    session: Database,
    customer: CurrentCustomer,
):
    owned_locked(session, account_id, customer.id)
    category_exists(session, body.category_id)
    row = session.scalar(
        select(LedgerEntry).where(
            LedgerEntry.id == transaction_id, LedgerEntry.account_id == account_id
        )
    )
    if row is None:
        from app.core.errors import AppError

        raise AppError(404, "TRANSACTION_NOT_FOUND", "Transação não encontrada.")
    row.category_id = body.category_id
    session.flush()
    result = TransactionResponse.model_validate(row)
    session.commit()
    return result


@router.get("/accounts/{account_id}/scenario")
def scenario(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    value = scenario_view(session, get_scenario(session, account_id))
    session.commit()
    return value


@router.post("/accounts/{account_id}/scenario/advance")
def advance_scenario(
    account_id: UUID, body: AdvanceInput, session: Database, customer: CurrentCustomer
):
    return advance(session, customer.id, account_id, body.target_date)


@router.post("/accounts/{account_id}/scenario/events")
def add_event(account_id: UUID, body: EventInput, session: Database, customer: CurrentCustomer):
    return schedule_event(session, customer.id, account_id, body)


@router.get("/accounts/{account_id}/data-summary")
def summary(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned(session, account_id, customer.id)
    count, first, last = session.execute(
        select(
            func.count(), func.min(LedgerEntry.occurred_on), func.max(LedgerEntry.occurred_on)
        ).where(LedgerEntry.account_id == account_id)
    ).one()
    return {
        "transaction_count": count,
        "first_date": first,
        "last_date": last,
        "balance": format(BankingRepository(session).balance(account_id), ".2f"),
        "fictitious": True,
    }


@router.get("/accounts/{account_id}/recurrences")
def recurrences(account_id: UUID, session: Database, customer: CurrentCustomer):
    owned_locked(session, account_id, customer.id)
    scenario = get_scenario(session, account_id)
    rows = session.scalars(
        select(LedgerEntry).where(
            LedgerEntry.account_id == account_id, LedgerEntry.occurred_on <= scenario.current_date
        )
    )
    result = detect_recurrences(
        [
            {
                "description": row.description,
                "direction": row.direction,
                "occurred_on": row.occurred_on,
                "amount": row.amount,
            }
            for row in rows
        ],
        scenario.current_date,
    )
    session.commit()
    return result
