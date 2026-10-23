from uuid import UUID

from app.core.errors import AppError
from app.modules.banking.models import Account
from app.modules.banking.repositories import BankingRepository
from app.modules.banking.schemas import BalanceResponse


class BankingService:
    def __init__(self, repository: BankingRepository) -> None:
        self.repository = repository

    def owned_account(self, account_id: UUID, customer_id: UUID) -> Account:
        account = self.repository.account(account_id, customer_id)
        if account is None:
            # Avoid disclosing whether another customer's account exists.
            raise AppError(404, "ACCOUNT_NOT_FOUND", "Conta não encontrada.")
        return account

    def balance(self, account_id: UUID, customer_id: UUID) -> BalanceResponse:
        account = self.owned_account(account_id, customer_id)
        return BalanceResponse(account_id=account.id, balance=self.repository.balance(account.id))
