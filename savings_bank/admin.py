from django.contrib import admin
from savings_bank.models import Account, Transaction


admin.site.register(Transaction)


@admin.register(Account)
class AccountAdmin(admin.ModelAdmin):
    list_display = ["user", "balance", "bank_name"]
