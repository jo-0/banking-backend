from django.contrib import admin, messages
from savings_bank.models import Account, Transaction


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "bank_name", "branch"]


@admin.register(Transaction)
class TransactionAdmin(admin.ModelAdmin):
    list_display = ["created_at", "from_account", "to_account", "amount", "status", "transaction_type"]
    exclude = ("status",)

    def save_model(self, request, obj, form, change) -> None:
        from_account = Account.objects.filter(id=obj.from_account.id).first()
        if from_account.balance < obj.amount:
            messages.error(request=request, message="Not enough balance")
        return super().save_model(request, obj, form, change)
