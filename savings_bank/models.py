import secrets
from decimal import Decimal

from django.contrib.auth import get_user_model
from django.db import models


class Account(models.Model):
    user = models.OneToOneField(
        get_user_model(), on_delete=models.PROTECT, related_name="account"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    bank_name = models.CharField(max_length=100)
    branch = models.CharField(max_length=50)

    class Meta:
        verbose_name_plural = "accounts"

    def __str__(self) -> str:
        return f"{self.user.username}'s Account - {self.bank_name}"

    @property
    def balance(self) -> Decimal:
        """Calculate balance from all transactions"""
        from django.db.models import Q, Sum

        # Sum all credits (deposits and incoming transfers)
        credits = self.transactions.filter(
            Q(transaction_type="DEPOSIT")
            | Q(transaction_type="TRANSFER", to_account=self)
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # Sum all debits (withdrawals and outgoing transfers)
        debits = self.transactions.filter(
            Q(transaction_type="WITHDRAWAL")
            | Q(transaction_type="TRANSFER", from_account=self)
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        return credits - debits

    def has_sufficient_balance(self, amount: Decimal) -> bool:
        """Check if account has sufficient balance for a transaction"""
        return self.balance >= amount

    def get_balance_at_date(self, date):
        """Get balance at a specific date (bonus feature from README)"""
        from django.db.models import Q, Sum

        # Sum all credits up to the specified date
        credits = self.transactions.filter(
            Q(transaction_type="DEPOSIT")
            | Q(transaction_type="TRANSFER", to_account=self),
            created_at__lte=date,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        # Sum all debits up to the specified date
        debits = self.transactions.filter(
            Q(transaction_type="WITHDRAWAL")
            | Q(transaction_type="TRANSFER", from_account=self),
            created_at__lte=date,
        ).aggregate(total=Sum("amount"))["total"] or Decimal("0")

        return credits - debits


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEPOSIT = "DEPOSIT", "Deposit"
        WITHDRAWAL = "WITHDRAWAL", "Withdrawal"
        TRANSFER = "TRANSFER", "Transfer"

    class TransactionStatus(models.TextChoices):
        SUCCESS = "SUCCESS", "Success"
        FAILED = "FAILED", "Failed"
        PENDING = "PENDING", "Pending"

    # Main account involved in the transaction
    account = models.ForeignKey(
        Account, on_delete=models.PROTECT, related_name="transactions"
    )

    # For transfers only - the other account involved
    from_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="outgoing_transfers",
        null=True,
        blank=True,
    )
    to_account = models.ForeignKey(
        Account,
        on_delete=models.PROTECT,
        related_name="incoming_transfers",
        null=True,
        blank=True,
    )

    amount = models.DecimalField(max_digits=12, decimal_places=2)
    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)
    status = models.CharField(
        max_length=8,
        choices=TransactionStatus.choices,
        default=TransactionStatus.PENDING,
    )
    note = models.CharField(max_length=200, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "transactions"
        ordering = ["-created_at"]

    def __str__(self) -> str:
        return f"{self.transaction_type} - {self.amount} - {self.account.user.username}"

    def _validate_sufficient_balance(self, account, transaction_type):
        """Helper method to validate sufficient balance"""
        from django.core.exceptions import ValidationError

        if account.balance < self.amount:
            raise ValidationError(
                f"Insufficient balance for {transaction_type.lower()}. "
                f"Available: {account.balance}, Required: {self.amount}"
            )

    def clean(self):
        """Validate transaction data"""
        from django.core.exceptions import ValidationError

        if self.transaction_type == self.TransactionType.TRANSFER:
            if not self.from_account or not self.to_account:
                raise ValidationError(
                    "Transfer requires both from_account and to_account"
                )
            if self.from_account == self.to_account:
                raise ValidationError("Cannot transfer to the same account")

            # Check if from_account has sufficient balance
            self._validate_sufficient_balance(self.from_account, "transfer")

        elif self.transaction_type == self.TransactionType.WITHDRAWAL:
            if self.from_account or self.to_account:
                raise ValidationError(
                    "Withdrawals should not have from_account or to_account"
                )
            # Check if account has sufficient balance for withdrawal
            self._validate_sufficient_balance(self.account, "withdrawal")

        elif self.transaction_type == self.TransactionType.DEPOSIT:
            if self.from_account or self.to_account:
                raise ValidationError(
                    "Deposits should not have from_account or to_account"
                )

    def save(self, *args, **kwargs):
        """Save transaction - business logic moved to service layer"""
        self.clean()
        super().save(*args, **kwargs)


class AuthToken(models.Model):
    """Custom authentication token model"""

    user = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="auth_tokens"
    )
    key = models.CharField(max_length=40, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_used = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "Authentication Token"
        verbose_name_plural = "Authentication Tokens"

    def save(self, *args, **kwargs):
        if not self.key:
            self.key = self.generate_key()
        return super().save(*args, **kwargs)

    @classmethod
    def generate_key(cls):
        return secrets.token_urlsafe(30)

    def __str__(self):
        return f"Token for {self.user.username}"
