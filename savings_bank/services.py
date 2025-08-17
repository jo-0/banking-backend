"""
Business logic services for banking operations
"""

from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction as db_transaction

from .models import Account, Transaction


class TransactionService:
    """Service class for handling banking transactions"""

    @staticmethod
    def create_deposit(
        account: Account, amount: Decimal, note: str = ""
    ) -> Transaction:
        """Create a deposit transaction"""
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type=Transaction.TransactionType.DEPOSIT,
            note=note,
            status=Transaction.TransactionStatus.SUCCESS,
        )
        return transaction

    @staticmethod
    def create_withdrawal(
        account: Account, amount: Decimal, note: str = ""
    ) -> Transaction:
        """Create a withdrawal transaction"""
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        if account.balance < amount:
            raise ValidationError(
                f"Insufficient balance. Available: {account.balance}, Required: {amount}"
            )

        transaction = Transaction.objects.create(
            account=account,
            amount=amount,
            transaction_type=Transaction.TransactionType.WITHDRAWAL,
            note=note,
            status=Transaction.TransactionStatus.SUCCESS,
        )
        return transaction

    @staticmethod
    def create_transfer(
        from_account: Account, to_account: Account, amount: Decimal, note: str = ""
    ) -> tuple[Transaction, Transaction]:
        """Create a transfer between two accounts"""
        if amount <= 0:
            raise ValidationError("Amount must be positive")

        if from_account == to_account:
            raise ValidationError("Cannot transfer to the same account")

        if from_account.balance < amount:
            raise ValidationError(
                (
                    f"Insufficient balance. Available: {from_account.balance}, "
                    f"Required: {amount}"
                )
            )

        with db_transaction.atomic():
            # Create debit transaction for sender
            debit_transaction = Transaction.objects.create(
                account=from_account,
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                transaction_type=Transaction.TransactionType.TRANSFER,
                note=f"Transfer to {to_account.user.username}: {note}",
                status=Transaction.TransactionStatus.SUCCESS,
            )

            # Create credit transaction for receiver
            credit_transaction = Transaction.objects.create(
                account=to_account,
                from_account=from_account,
                to_account=to_account,
                amount=amount,
                transaction_type=Transaction.TransactionType.TRANSFER,
                note=f"Transfer from {from_account.user.username}: {note}",
                status=Transaction.TransactionStatus.SUCCESS,
            )

        return debit_transaction, credit_transaction


class AccountService:
    """Service class for account operations"""

    @staticmethod
    def get_transaction_history(account: Account, limit: int | None = None):
        """Get transaction history for an account"""
        transactions = account.transactions.all()
        if limit:
            transactions = transactions[:limit]
        return transactions

    @staticmethod
    def get_balance_at_date(account: Account, date):
        """Get account balance at a specific date"""
        return account.get_balance_at_date(date)
