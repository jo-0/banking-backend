from django.contrib import admin, messages
from savings_bank.models import Account, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display: list[str] = ["user", "balance", "bank_name", "branch"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display: list[str] = [
        "created_at",
        "from_account",
        "to_account",
        "amount",
        "status",
        "transaction_type",
    ]
    exclude: tuple[str,] = ("status",)

    def save_model(self, request, obj, form, change) -> None:
        from_account: Account = Account.objects.get(id=obj.from_account.id)
        if from_account.balance < obj.amount:
            messages.error(request=request, message="Not enough balance")
        return super().save_model(request=request, obj=obj, form=form, change=change)
