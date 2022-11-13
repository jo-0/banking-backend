from django.db import models, transaction
from django.contrib.auth import get_user_model


class Account(models.Model):
    user = models.ForeignKey(get_user_model(), on_delete=models.PROTECT, null=True, blank=False)
    created_at = models.DateTimeField(auto_now_add=True)
    balance = models.IntegerField()
    bank_name = models.CharField(max_length=24)
    branch = models.CharField(max_length=12)

    class Meta:
        verbose_name_plural = "accounts"

    def __str__(self) -> str:
        return f"{self.user}"


class Transaction(models.Model):
    class TransactionType(models.TextChoices):
        DEBIT = "Debit", "Withdraw"
        CREDIT = "Credit", "Deposit"

    class TransactionStatus(models.TextChoices):
        SUCCESS = "Success", "Success"
        FAILED = "Failed", "Failed"
        PENDING = "Pending", "Pending"

    created_at = models.DateTimeField(auto_now_add=True, verbose_name="date")
    from_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="from_account")
    to_account = models.ForeignKey(Account, on_delete=models.PROTECT, related_name="to_account")
    amount = models.PositiveIntegerField()
    note = models.CharField(max_length=48, null=True)
    status = models.CharField(max_length=8, choices=TransactionStatus.choices, default=TransactionStatus.PENDING)
    transaction_type = models.CharField(max_length=12, choices=TransactionType.choices)

    class Meta:
        verbose_name_plural = "transactions"

    def save(self, *args, **kwargs) -> None:
        if not self.pk:
            from_account = Account.objects.filter(id=self.from_account.id).first()
            to_account = Account.objects.filter(id=self.to_account.id).first()

            if from_account is not None and to_account is not None:
                # check if sending account has enough balance.
                if from_account.balance < self.amount:
                    return

                # doing transactions on the same account
                if from_account == to_account:
                    with transaction.atomic():
                        # if user withdraws
                        if self.transaction_type == self.TransactionType.DEBIT:
                            from_account.balance -= self.amount
                            from_account.save()
                        # if user deposits
                        elif self.transaction_type == self.TransactionType.CREDIT:
                            from_account.balance += self.amount
                            from_account.save()
                    self.status = self.TransactionStatus.SUCCESS
                    return super().save(*args, **kwargs)

                with transaction.atomic():
                    # Deduct amount from sending account
                    from_account.balance -= self.amount
                    from_account.save()

                    # Add new balance to account
                    to_account.balance += self.amount
                    to_account.save()

                    self.status = self.TransactionStatus.SUCCESS

        return super().save(*args, **kwargs)
