"""Confirmed transactions: stable history and serialized, idempotent ledger writes."""

import base64
import hashlib
import json
from datetime import UTC, date, datetime
from decimal import Decimal
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer, field_validator
from sqlalchemy import func, select, tuple_
from sqlalchemy.orm import Session

from app.core.errors import AppError
from app.modules.banking.models import Account, Category, LedgerEntry
from app.modules.banking.repositories import BankingRepository

Amount = Annotated[str, Field(pattern=r"^(?:0|[1-9]\d{0,15})\.\d{2}$")]


class TransactionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)
    amount: Amount
    description: str = Field(min_length=1, max_length=120)
    category_id: str | None = Field(default=None, max_length=24)
    recipient: str | None = Field(default=None, min_length=1, max_length=120)
    idempotency_key: UUID

    @field_validator("amount")
    @classmethod
    def positive(cls, value):
        if Decimal(value) <= 0:
            raise ValueError("Amount must be positive")
        return value


class TransactionResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    occurred_on: date
    direction: Literal["credit", "debit"]
    amount: Decimal
    description: str
    category_id: str
    kind: str
    recipient: str | None

    @field_serializer("amount")
    def money(self, value):
        return format(value, ".2f")


class TransactionPage(BaseModel):
    items: list[TransactionResponse]
    next_cursor: str | None
    total: int


class Receipt(BaseModel):
    transaction: TransactionResponse
    balance: str
    simulated: Literal[True] = True
    forecast_id: UUID | None = None
    previous_forecast_id: UUID | None = None
    forecast_status: Literal["ready", "failed", "pending"] = "pending"
    correlation_id: str | None = None


class CategoryUpdate(BaseModel):
    category_id: str = Field(min_length=1, max_length=24)


def owned_locked(session: Session, account_id: UUID, customer_id: UUID) -> Account:
    account = session.scalar(
        select(Account)
        .where(Account.id == account_id, Account.customer_id == customer_id)
        .with_for_update()
    )
    if account is None:
        raise AppError(404, "ACCOUNT_NOT_FOUND", "Conta não encontrada.")
    return account


def category_exists(session, category_id):
    if session.get(Category, category_id) is None:
        raise AppError(422, "INVALID_CATEGORY", "Escolha uma categoria válida.")


def fingerprint(value: dict) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, default=str).encode()).hexdigest()


def post_transaction(session, customer_id, account_id, body: TransactionInput, kind: str):
    from app.modules.forecasting.recovery import queue_refresh, recover_refresh
    from app.modules.notifications.models import ForecastRefresh
    from app.modules.simulation.services import get_scenario

    owned_locked(session, account_id, customer_id)
    digest = fingerprint({**body.model_dump(exclude={"idempotency_key"}), "kind": kind})
    reference = f"{account_id}:{body.idempotency_key}"
    existing = session.scalar(select(LedgerEntry).where(LedgerEntry.reference == reference))
    if existing:
        if existing.request_hash != digest:
            raise AppError(409, "IDEMPOTENCY_CONFLICT", "Chave já usada para outra movimentação.")
        result = existing
        refresh = session.scalar(
            select(ForecastRefresh).where(ForecastRefresh.transaction_id == result.id)
        )
    else:
        direction = "credit" if kind == "income" else "debit"
        category = body.category_id or (
            "income" if kind == "income" else "pix" if kind == "pix" else "other"
        )
        category_exists(session, category)
        amount = Decimal(body.amount)
        if kind == "pix" and not body.recipient:
            raise AppError(422, "RECIPIENT_REQUIRED", "Informe um favorecido fictício.")
        balance = BankingRepository(session).balance(account_id)
        if direction == "debit" and amount > balance:
            raise AppError(
                409, "INSUFFICIENT_FUNDS", "Saldo insuficiente. Nenhum débito foi realizado."
            )
        if abs(balance + (amount if direction == "credit" else -amount)) > Decimal(
            "9999999999999999.99"
        ):
            raise AppError(422, "BALANCE_LIMIT", "Movimentação excede o limite do protótipo.")
        result = LedgerEntry(
            account_id=account_id,
            direction=direction,
            amount=amount,
            description=body.description,
            occurred_on=get_scenario(session, account_id).current_date,
            reference=reference,
            category_id=category,
            kind=kind,
            recipient=body.recipient,
            request_hash=digest,
        )
        session.add(result)
        session.flush()
        refresh = queue_refresh(session, result)
    receipt = Receipt(
        transaction=TransactionResponse.model_validate(result),
        balance=format(BankingRepository(session).balance(account_id), ".2f"),
    )
    refresh_id = refresh.id if refresh is not None else None
    session.commit()  # Monetary operation is durable even when the model fails.
    if refresh_id is not None:
        refresh = recover_refresh(session, refresh_id)
        receipt.forecast_id = refresh.forecast_id
        receipt.previous_forecast_id = refresh.previous_forecast_id
        receipt.forecast_status = refresh.status
        receipt.correlation_id = refresh.correlation_id
    return receipt


def history(
    session,
    account_id,
    limit=25,
    cursor=None,
    date_from=None,
    date_to=None,
    category_id=None,
    direction=None,
    search=None,
):
    if date_from and date_to and date_from > date_to:
        raise AppError(422, "INVALID_PERIOD", "Data inicial deve ser anterior à final.")
    conditions = [LedgerEntry.account_id == account_id]
    if date_from:
        conditions.append(LedgerEntry.occurred_on >= date_from)
    if date_to:
        conditions.append(LedgerEntry.occurred_on <= date_to)
    if category_id:
        category_exists(session, category_id)
        conditions.append(LedgerEntry.category_id == category_id)
    if direction:
        conditions.append(LedgerEntry.direction == direction)
    if search:
        conditions.append(LedgerEntry.description.icontains(search, autoescape=True))
    asof = datetime.now(UTC)
    after = None
    if cursor:
        try:
            decoded = json.loads(base64.urlsafe_b64decode(cursor.encode()))
            after = (date.fromisoformat(decoded["date"]), UUID(decoded["id"]))
            asof = datetime.fromisoformat(decoded["asof"])
            if asof.tzinfo is None or asof > datetime.now(UTC):
                raise ValueError("Invalid snapshot")
        except (ValueError, KeyError, TypeError, UnicodeError) as exc:
            raise AppError(422, "INVALID_CURSOR", "Página inválida. Atualize o extrato.") from exc
    conditions.append(LedgerEntry.created_at <= asof)
    total = session.scalar(select(func.count()).select_from(LedgerEntry).where(*conditions))
    query = select(LedgerEntry).where(*conditions)
    if after:
        query = query.where(tuple_(LedgerEntry.occurred_on, LedgerEntry.id) < after)
    rows = list(
        session.scalars(
            query.order_by(LedgerEntry.occurred_on.desc(), LedgerEntry.id.desc()).limit(limit + 1)
        )
    )
    more = len(rows) > limit
    rows = rows[:limit]
    next_cursor = None
    if more:
        last = rows[-1]
        next_cursor = base64.urlsafe_b64encode(
            json.dumps(
                {"date": str(last.occurred_on), "id": str(last.id), "asof": asof.isoformat()}
            ).encode()
        ).decode()
    return TransactionPage(
        items=[TransactionResponse.model_validate(row) for row in rows],
        next_cursor=next_cursor,
        total=total,
    )
