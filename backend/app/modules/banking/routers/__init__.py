from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Query, Response

from app.modules.auth.dependencies import CurrentCustomer, Database
from app.modules.banking.repositories import BankingRepository
from app.modules.banking.schemas import (
    AccountResponse,
    BalanceResponse,
    CustomerResponse,
    LedgerResponse,
)
from app.modules.banking.services import BankingService

router = APIRouter(tags=["banking"])


@router.get("/customers", response_model=list[CustomerResponse])
def customers(session: Database):
    """Public list of fictitious profiles for the demo sign-in screen; no passwords or balances."""
    return BankingRepository(session).customers()


@router.get("/accounts", response_model=list[AccountResponse])
def accounts(session: Database, customer: CurrentCustomer):
    return BankingRepository(session).accounts(customer.id)


@router.get("/accounts/{account_id}", response_model=AccountResponse)
def account(account_id: UUID, session: Database, customer: CurrentCustomer):
    return BankingService(BankingRepository(session)).owned_account(account_id, customer.id)


@router.get("/accounts/{account_id}/balance", response_model=BalanceResponse)
def balance(account_id: UUID, session: Database, customer: CurrentCustomer, response: Response):
    response.headers["Cache-Control"] = "no-store"
    return BankingService(BankingRepository(session)).balance(account_id, customer.id)


@router.get("/accounts/{account_id}/ledger", response_model=list[LedgerResponse])
def ledger(
    account_id: UUID,
    session: Database,
    customer: CurrentCustomer,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    repository = BankingRepository(session)
    BankingService(repository).owned_account(account_id, customer.id)
    return repository.ledger(account_id, limit, offset)
