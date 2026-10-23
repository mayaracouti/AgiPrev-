from datetime import date
from decimal import Decimal
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_serializer


class CustomerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    name: str
    email: str
    demo_profile: str


class AccountResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    customer_id: UUID
    currency: Literal["BRL"]


class BalanceResponse(BaseModel):
    account_id: UUID
    currency: Literal["BRL"] = "BRL"
    balance: Decimal = Field(max_digits=18, decimal_places=2)

    @field_serializer("balance")
    def serialize_balance(self, value: Decimal) -> str:
        return format(value, ".2f")


class LedgerResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: UUID
    occurred_on: date
    direction: Literal["credit", "debit"]
    amount: Decimal
    description: str

    @field_serializer("amount")
    def serialize_amount(self, value: Decimal) -> str:
        return format(value, ".2f")
