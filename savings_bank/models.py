from django.db import models
from django.contrib.auth import get_user_model


class Account(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null=True, blank=False)
    balance = models.IntegerField()
    bank_name = models.CharField(max_length=24)
    branch = models.CharField(max_length=12)

    class Meta:
        verbose_name_plural = "accounts"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEBIT = "Debit", "Withdraw"
        CREDIT = "Credit", "Deposit"

    class TransactionStatus(models.TextChoices):
        SUCCESS = "Success", "Success"
        FAILED = "Failed", "Failed"
        PENDING = "Pending", "Pending"

    date = models.DateTimeField(auto_now_add=True)
    from_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="from_account")
    to_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="to_account")
    amount = models.PositiveIntegerField()
    note = models.CharField(max_length=48)
    status = models.CharField(max_length=8, choices=TransactionStatus.choices, null=True)
    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)

    class Meta:
        verbose_name_plural = "transactions"
